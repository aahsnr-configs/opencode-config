#!/usr/bin/env python3
"""Compact gnomAD GraphQL client for ChatGPT-imported skills."""

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

ENDPOINT = "https://gnomad.broadinstitute.org/api"


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
    query = payload.get("query")
    query_path = payload.get("query_path")
    if query is None and query_path is None:
        raise ValueError("Provide `query` or `query_path`.")
    if query is not None and (not isinstance(query, str) or not query.strip()):
        raise ValueError("`query` must be a non-empty string.")
    if query_path is not None and (not isinstance(query_path, str) or not query_path.strip()):
        raise ValueError("`query_path` must be a non-empty string.")
    variables = payload.get("variables") or {}
    if not isinstance(variables, dict):
        raise ValueError("`variables` must be an object.")
    save_raw = payload.get("save_raw", False)
    if not isinstance(save_raw, bool):
        raise ValueError("`save_raw` must be a boolean.")
    raw_output_path = payload.get("raw_output_path")
    if raw_output_path is not None and (
        not isinstance(raw_output_path, str) or not raw_output_path.strip()
    ):
        raise ValueError("`raw_output_path` must be a non-empty string.")
    for key in ("max_items", "max_depth", "timeout_sec"):
        value = payload.get(key, 5 if key == "max_items" else 3 if key == "max_depth" else 60)
        if type(value) is not int or value <= 0:
            raise ValueError(f"`{key}` must be a positive integer.")
        payload[key] = value
    query_text = (
        query.strip() if isinstance(query, str) else Path(query_path).read_text(encoding="utf-8")
    )
    return {
        "query": query_text,
        "variables": variables,
        "max_items": payload["max_items"],
        "max_depth": payload["max_depth"],
        "timeout_sec": payload["timeout_sec"],
        "save_raw": save_raw,
        "raw_output_path": raw_output_path.strip() if isinstance(raw_output_path, str) else None,
    }


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    config = parse_input(payload)
    try:
        response = _bounded_request(requests.post,
            ENDPOINT,
            json={"query": config["query"], "variables": config["variables"]},
            timeout=config["timeout_sec"],
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return error("invalid_response", "GraphQL response must be an object.")
    except requests.RequestException as exc:
        return error("network_error", f"GraphQL request failed ({type(exc).__name__}).")
    except ValueError as exc:
        return error("invalid_response", str(exc))

    raw_output_path = None
    if config["save_raw"]:
        raw_text = json.dumps(data, indent=2)
        path = (Path(config["raw_output_path"]) if config["raw_output_path"] else
                Path(tempfile.mkdtemp(prefix="opencode-life-science-")) / "gnomad-graphql.json")
        _check_output_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(raw_text)
        raw_output_path = str(path)

    if "errors" in data:
        return error(
            "graphql_error",
            json.dumps(data["errors"])[:500],
            warnings=[f"raw_output_path={raw_output_path}"] if raw_output_path else [],
        )

    payload_data = data.get("data")
    if not isinstance(payload_data, dict):
        return error("invalid_response", "GraphQL response did not include a `data` object.")

    return {
        "ok": True,
        "source": "gnomad-graphql",
        "top_keys": list(payload_data)[: config["max_items"]],
        "summary": _compact(payload_data, config["max_items"], config["max_depth"]),
        "raw_output_path": raw_output_path,
        "warnings": [],
    }


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
        code = 1
    except ValueError as exc:
        output = error("invalid_input", str(exc))
        code = 2
    else:
        code = 0 if output.get("ok") else 1
    sys.stdout.write(json.dumps(output))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
