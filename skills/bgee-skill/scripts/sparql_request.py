#!/usr/bin/env python3
"""Compact Bgee SPARQL client for ChatGPT-imported skills."""

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

ENDPOINT = "https://www.bgee.org/sparql/"


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
    method = str(payload.get("method", "GET")).upper()
    if method not in {"GET", "POST"}:
        raise ValueError("`method` must be GET or POST.")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise ValueError("`params` must be an object.")
    response_format = str(payload.get("response_format", "auto")).lower()
    if response_format not in {"auto", "json", "text"}:
        raise ValueError("`response_format` must be auto, json, or text.")
    save_raw = payload.get("save_raw", False)
    if not isinstance(save_raw, bool):
        raise ValueError("`save_raw` must be a boolean.")
    raw_output_path = payload.get("raw_output_path")
    if raw_output_path is not None and (
        not isinstance(raw_output_path, str) or not raw_output_path.strip()
    ):
        raise ValueError("`raw_output_path` must be a non-empty string.")
    for key in ("max_items", "max_depth", "timeout_sec"):
        default = 5 if key == "max_items" else 3 if key == "max_depth" else 60
        value = payload.get(key, default)
        if type(value) is not int or value <= 0:
            raise ValueError(f"`{key}` must be a positive integer.")
        payload[key] = value
    query_text = (
        query.strip() if isinstance(query, str) else Path(query_path).read_text(encoding="utf-8")
    )
    return {
        "query": query_text,
        "method": method,
        "params": params,
        "response_format": response_format,
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
    headers = {
        "Accept": "application/sparql-results+json, application/json;q=0.9, text/tab-separated-values;q=0.8, text/plain;q=0.5"
    }
    try:
        if config["method"] == "GET":
            params = dict(config["params"])
            params.setdefault("query", config["query"])
            params.setdefault("format", "json")
            response = _bounded_request(requests.get,
                ENDPOINT, params=params, headers=headers, timeout=config["timeout_sec"]
            )
        else:
            response = _bounded_request(requests.post,
                ENDPOINT,
                data={"query": config["query"], **config["params"]},
                headers=headers,
                timeout=config["timeout_sec"],
            )
        response.raise_for_status()
    except requests.RequestException as exc:
        return error("network_error", f"Request failed ({type(exc).__name__}).")
    except ValueError as exc:
        return error("invalid_response", str(exc))

    raw_output_path = None
    if config["save_raw"]:
        suffix = "json" if "json" in (response.headers.get("content-type") or "").lower() else "txt"
        path = (Path(config["raw_output_path"]) if config["raw_output_path"] else
                Path(tempfile.mkdtemp(prefix="opencode-life-science-")) / f"bgee-sparql.{suffix}")
        _check_output_parent(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(response.text)
        raw_output_path = str(path)

    content_type = (response.headers.get("content-type") or "").lower()
    wants_text = config["response_format"] == "text"
    auto_json = not wants_text and (
        "json" in content_type or response.text.lstrip().startswith("{")
    )
    if not auto_json and config["response_format"] != "json":
        text_head = None if raw_output_path else response.text[:800]
        return {
            "ok": True,
            "source": "bgee-sparql",
            "content_type": content_type,
            "text_head": text_head,
            "text_head_truncated": False if raw_output_path else len(response.text) > 800,
            "raw_output_path": raw_output_path,
            "warnings": [],
        }

    try:
        data = response.json()
    except ValueError as exc:
        return error("invalid_response", str(exc))

    if not isinstance(data, dict):
        return error("invalid_response", "SPARQL JSON response must be an object.")
    if "boolean" in data:
        summary: Any = {"boolean": data["boolean"]}
        top_keys = ["boolean"]
    else:
        results = data.get("results", {})
        bindings = results.get("bindings", []) if isinstance(results, dict) else []
        if not isinstance(bindings, list):
            return error("invalid_response", "SPARQL bindings must be an array.")
        summary = {
            "head": data.get("head", {}),
            "record_count_returned": min(len(bindings), config["max_items"]),
            "record_count_available": len(bindings),
            "truncated": len(bindings) > config["max_items"],
            "records": _compact(
                bindings[: config["max_items"]], config["max_items"], config["max_depth"]
            ),
        }
        top_keys = list(summary)[: config["max_items"]]

    return {
        "ok": True,
        "source": "bgee-sparql",
        "top_keys": top_keys,
        "summary": _compact(summary, config["max_items"], config["max_depth"]),
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
