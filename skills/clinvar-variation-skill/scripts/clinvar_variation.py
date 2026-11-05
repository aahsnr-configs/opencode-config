#!/usr/bin/env python3
"""Compact ClinVar + NCBI Variation helper for ChatGPT-imported skills."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:  # pragma: no cover
    requests = None
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

CLINICAL_TABLES_URL = "https://clinicaltables.nlm.nih.gov/api/variants/v4/search"
VARIATION_BASE = "https://api.ncbi.nlm.nih.gov/variation/v0/beta"


MAX_RESPONSE_BYTES = 5 * 1024 * 1024


def _decode_json(raw):
    """Reject excessive response nesting before recursive summary processing."""
    try:
        result = json.loads(raw)
    except RecursionError as exc:
        raise ValueError("JSON response nesting exceeds the supported depth.") from exc
    pending = [(iter((result,)), 0)]
    while pending:
        values, depth = pending[-1]
        try:
            value = next(values)
        except StopIteration:
            pending.pop()
            continue
        if depth > 64:
            raise ValueError("JSON response nesting exceeds the supported depth of 64.")
        if isinstance(value, dict):
            pending.append((iter(value.values()), depth + 1))
        elif isinstance(value, list):
            pending.append((iter(value), depth + 1))
    return result


def _bounded_request(request, *args, **kwargs):
    """Read one bounded response; never forward a request across redirects."""
    from types import SimpleNamespace
    kwargs.update(stream=True, allow_redirects=False)
    response = request(*args, **kwargs)
    try:
        if 300 <= response.status_code < 400:
            raise ValueError("HTTP redirect refused; use the verified final endpoint explicitly.")
        body = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                raise ValueError("Response exceeds the 5 MiB download limit; narrow the query.")
            body.extend(chunk)
        raw = bytes(body)
        try:
            text = raw.decode(response.encoding or "utf-8", errors="replace")
        except LookupError:
            text = raw.decode("utf-8", errors="replace")
        return SimpleNamespace(content=raw, text=text, headers=response.headers,
            status_code=response.status_code, json=lambda: _decode_json(raw),
            raise_for_status=response.raise_for_status)
    finally:
        response.close()


def _check_output_parent(path):
    """Reject linked ancestors; use canonical paths for intentional directory links.

    This preflight does not protect against concurrent filesystem replacement.
    """
    for parent in Path(path).absolute().parents:
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise OSError("Raw output parent must be a real directory, not a symlink.")


def error(code: str, message: str, warnings: list[str] | None = None) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}, "warnings": warnings or []}


def _compact(value: Any, max_items: int, max_depth: int) -> Any:
    if isinstance(value, str):
        return value if len(value) <= 240 else value[:240] + "..."
    if max_depth <= 0:
        if isinstance(value, (dict, list)):
            return "..."
        return value
    if isinstance(value, list):
        out = [_compact(item, max_items, max_depth - 1) for item in value[:max_items]]
        if len(value) > max_items:
            out.append(f"... (+{len(value) - max_items} more)")
        return out
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        items = list(value.items())
        for key, item in items[:max_items]:
            out[str(key)] = _compact(item, max_items, max_depth - 1)
        if len(items) > max_items:
            out["_truncated_keys"] = len(items) - max_items
        return out
    return value


def parse_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be one JSON object.")
    action = payload.get("action")
    if not isinstance(action, str) or action not in {"search", "vcv", "rcv", "scv", "refsnp"}:
        raise ValueError("`action` must be one of: search, vcv, rcv, scv, refsnp.")
    max_items = payload.get("max_items", 5)
    max_depth = payload.get("max_depth", 3)
    timeout_sec = payload.get("timeout_sec", 30)
    save_raw = payload.get("save_raw", False)
    for name, value in {
        "max_items": max_items,
        "max_depth": max_depth,
        "timeout_sec": timeout_sec,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"`{name}` must be a positive integer.")
    if not isinstance(save_raw, bool):
        raise ValueError("`save_raw` must be a boolean.")
    raw_output_path = payload.get("raw_output_path")
    if raw_output_path is not None and (
        not isinstance(raw_output_path, str) or not raw_output_path.strip()
    ):
        raise ValueError("`raw_output_path` must be a non-empty string.")
    return {
        "action": action,
        "terms": payload.get("terms"),
        "vcv": payload.get("vcv"),
        "rcv": payload.get("rcv"),
        "scv": payload.get("scv"),
        "refsnp": payload.get("refsnp"),
        "params": payload.get("params") or {},
        "max_items": max_items,
        "max_depth": max_depth,
        "timeout_sec": timeout_sec,
        "save_raw": save_raw,
        "raw_output_path": raw_output_path.strip() if isinstance(raw_output_path, str) else None,
    }


def _save(raw_output: str, raw_output_path: str | None) -> str:
    path = (Path(raw_output_path) if raw_output_path else
            Path(tempfile.mkdtemp(prefix="opencode-life-science-")) / "clinvar-variation-raw.json")
    _check_output_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(raw_output)
    return str(path)


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    config = parse_input(payload)
    try:
        if config["action"] == "search":
            if not isinstance(config["terms"], str) or not config["terms"].strip():
                raise ValueError("`terms` is required for `search`.")
            params = {"terms": config["terms"].strip(), "maxList": config["max_items"]}
            if not isinstance(config["params"], dict):
                raise ValueError("`params` must be an object.")
            params.update(config["params"])
            response = _bounded_request(requests.get,
                CLINICAL_TABLES_URL, params=params, timeout=config["timeout_sec"]
            )
            response.raise_for_status()
            data = response.json()
            raw_output = json.dumps(data, indent=2)
            raw_output_path = (
                _save(raw_output, config["raw_output_path"]) if config["save_raw"] else None
            )
            if not isinstance(data, list) or len(data) < 4:
                return error(
                    "invalid_response",
                    "Clinical Tables response did not match the expected list shape.",
                )
            total = data[0]
            identifiers = data[1] if isinstance(data[1], list) else []
            extra_fields = data[2]
            display_rows = data[3] if isinstance(data[3], list) else []
            return {
                "ok": True,
                "source": "clinvar-clinicaltables",
                "action": "search",
                "total": total,
                "record_count_returned": len(display_rows[: config["max_items"]]),
                "record_count_available": len(display_rows),
                "truncated": len(display_rows) > config["max_items"] or (len(display_rows[: config["max_items"]]) < total if type(total) is int else False),
                "identifiers": identifiers[: config["max_items"]],
                "display_rows": _compact(
                    display_rows[: config["max_items"]], config["max_items"], config["max_depth"]
                ),
                "extra_fields": _compact(extra_fields, config["max_items"], config["max_depth"]),
                "raw_output_path": raw_output_path,
                "warnings": [],
            }

        id_key = config["action"]
        identifier = config[id_key]
        if type(identifier) not in (str, int) or not str(identifier).strip():
            raise ValueError(f"`{id_key}` is required for `{config['action']}`.")
        if config["action"] == "vcv":
            digits = str(identifier).strip().lstrip("VCV")
            path = f"{VARIATION_BASE}/clinvar/variation/{digits}"
        elif config["action"] == "rcv":
            path = f"{VARIATION_BASE}/clinvar/rcv/{str(identifier).strip()}"
        elif config["action"] == "scv":
            path = f"{VARIATION_BASE}/clinvar/scv/{str(identifier).strip()}"
        else:
            digits = str(identifier).strip().lstrip("rs").lstrip("RS")
            path = f"{VARIATION_BASE}/refsnp/{digits}"

        response = _bounded_request(requests.get, path, timeout=config["timeout_sec"])
        response.raise_for_status()
        data = response.json()
        raw_output = json.dumps(data, indent=2)
        raw_output_path = (
            _save(raw_output, config["raw_output_path"]) if config["save_raw"] else None
        )
        return {
            "ok": True,
            "source": "clinvar-variation",
            "action": config["action"],
            "summary": _compact(data, config["max_items"], config["max_depth"]),
            "top_keys": list(data)[: config["max_items"]] if isinstance(data, dict) else None,
            "raw_output_path": raw_output_path,
            "warnings": [],
        }
    except requests.RequestException as exc:
        return error("network_error", f"Request failed ({type(exc).__name__}).")
    except ValueError as exc:
        return error("invalid_input", str(exc))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(json.dumps(error("invalid_json", f"Could not parse JSON input: {exc}")))
        return 2
    try:
        output = execute(payload)
    except OSError as exc:
        output = error("file_error", f"File operation failed: {exc}")
    except ValueError as exc:
        output = error("invalid_input", str(exc))
    sys.stdout.write(json.dumps(output))
    return 0 if output.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
