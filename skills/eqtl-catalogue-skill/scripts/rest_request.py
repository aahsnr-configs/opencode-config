#!/usr/bin/env python3
"""Generic compact REST client for ChatGPT-imported skills."""

from __future__ import annotations

import json
import sys
import tempfile
from urllib.parse import urljoin, urlsplit
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError as exc:  # pragma: no cover
    requests = None
    REQUESTS_IMPORT_ERROR = exc
else:
    REQUESTS_IMPORT_ERROR = None

EQTLCAT_BASE_URL = "https://www.ebi.ac.uk/eqtl/api"
EQTLCAT_ASSOCIATION_FLOAT_DEFAULTS = {
    "p_lower": 0,
    "p_upper": 1,
}
EQTLCAT_ASSOCIATION_STR_DEFAULTS = {
    "quant_method": "ge",
    "snp": "",
    "study": "",
    "tissue": "",
    "gene_id": "",
    "molecular_trait_id": "",
    "qtl_group": "",
}


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


def _require_object(name: str, value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"`{name}` must be an object.")
    return value


def _require_bool(name: str, value: Any, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ValueError(f"`{name}` must be a boolean.")
    return value


def _require_int(name: str, value: Any, default: int) -> int:
    if value is None:
        return default
    if type(value) is not int or value <= 0:
        raise ValueError(f"`{name}` must be a positive integer.")
    return value


def _require_str(name: str, value: Any, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"`{name}` is required.")
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{name}` must be a non-empty string.")
    return value.strip()


def _service_name(base_url: str) -> str:
    host = base_url.split("://", 1)[-1].split("/", 1)[0]
    return host.replace(".", "-")


def _drop_none_values(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _url_origin(url: str) -> tuple[str, str, int]:
    parsed = urlsplit(url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment or "\\" in url or any(c.isspace() for c in url)):
        raise ValueError("URLs must use HTTP(S) without embedded credentials, fragments, or whitespace.")
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
    return parsed.scheme, parsed.hostname.lower(), port


def _build_url(base_url: str, path: str) -> str:
    """Keep relative paths and absolute same-origin URLs within the approved base."""
    origin = _url_origin(base_url)
    if urlsplit(base_url).query:
        raise ValueError("`base_url` must not include a query; use `params` instead.")
    parsed_path = urlsplit(path)
    if parsed_path.scheme or parsed_path.netloc:
        url = urljoin(base_url.rstrip("/") + "/", path)
    else:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if _url_origin(url) != origin:
        raise ValueError("`path` must use the same origin as `base_url`; cross-origin headers are refused.")
    return url


def _get_by_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, list):
            if not part.isdigit():
                raise ValueError(f"`record_path` segment {part!r} must be a list index.")
            index = int(part)
            if index >= len(current):
                raise ValueError(f"`record_path` index {index} is out of range.")
            current = current[index]
        elif isinstance(current, dict):
            if part not in current:
                raise ValueError(f"`record_path` key {part!r} was not present in the response.")
            current = current[part]
        else:
            raise ValueError(f"`record_path` segment {part!r} could not be applied.")
    return current


def _infer_target(data: Any) -> tuple[str | None, Any]:
    if isinstance(data, list):
        return "$", data
    if isinstance(data, dict):
        embedded = data.get("_embedded")
        if isinstance(embedded, dict):
            for key, value in embedded.items():
                if isinstance(value, list):
                    return f"_embedded.{key}", value
        for key in (
            "collection",
            "results",
            "structures",
            "activities",
            "molecules",
            "mechanisms",
            "records",
            "items",
        ):
            value = data.get(key)
            if isinstance(value, list):
                return key, value
    return None, data


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


def _save_raw_output(
    raw_output: str, raw_output_path: str | None, base_url: str, suffix: str
) -> str:
    path = (Path(raw_output_path) if raw_output_path else
            Path(tempfile.mkdtemp(prefix="opencode-life-science-")) / f"{_service_name(base_url)}-raw.{suffix}")
    _check_output_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(raw_output)
    return str(path)


def _is_eqtl_catalogue_association_request(base_url: str, path: str) -> bool:
    return base_url.rstrip("/") == EQTLCAT_BASE_URL and "associations" in path


def _normalize_eqtl_catalogue_params(
    base_url: str, path: str, params: dict[str, Any]
) -> dict[str, Any]:
    normalized = _drop_none_values(params)
    if not _is_eqtl_catalogue_association_request(base_url, path):
        return normalized

    # The live eQTL Catalogue API currently validates these query keys as
    # non-null even when the docs say they are optional. Backfill safe defaults
    # so omitted filters do not trigger upstream Pydantic errors.
    variant_id = normalized.get("variant_id")
    snp = normalized.get("snp")
    if variant_id and not snp:
        normalized["snp"] = variant_id
    elif snp and not variant_id:
        normalized["variant_id"] = snp

    for key, value in EQTLCAT_ASSOCIATION_FLOAT_DEFAULTS.items():
        if key not in normalized:
            normalized[key] = value
    for key, value in EQTLCAT_ASSOCIATION_STR_DEFAULTS.items():
        if key not in normalized:
            normalized[key] = value
    return normalized


def _extract_error_message(response: Any) -> str:
    body = (getattr(response, "text", "") or "").strip()
    content_type = str((getattr(response, "headers", {}) or {}).get("content-type") or "").lower()

    if "json" in content_type and hasattr(response, "json"):
        try:
            data = response.json()
        except ValueError:
            data = None
        if isinstance(data, dict):
            for key in ("message", "detail", "error"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    if body:
        return body[:800]
    return f"HTTP {getattr(response, 'status_code', 'unknown')}"


def parse_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Input must be one JSON object.")
    base_url = _require_str("base_url", payload.get("base_url"), required=True)
    path = _require_str("path", payload.get("path"), required=True)
    method = (_require_str("method", payload.get("method")) or "GET").upper()
    if method not in {"GET", "POST"}:
        raise ValueError("`method` must be GET or POST.")
    json_body = payload.get("json_body")
    form_body = payload.get("form_body")
    if json_body is not None and form_body is not None:
        raise ValueError("Provide only one of `json_body` or `form_body`.")
    response_format = (
        _require_str("response_format", payload.get("response_format")) or "auto"
    ).lower()
    if response_format not in {"auto", "json", "text"}:
        raise ValueError("`response_format` must be auto, json, or text.")
    params = _require_object("params", payload.get("params"))
    headers = _drop_none_values(_require_object("headers", payload.get("headers")))
    return {
        "base_url": base_url,
        "path": path,
        "method": method,
        "params": _normalize_eqtl_catalogue_params(base_url, path, params),
        "headers": headers,
        "json_body": json_body,
        "form_body": _drop_none_values(_require_object("form_body", form_body))
        if form_body is not None
        else None,
        "record_path": _require_str("record_path", payload.get("record_path")),
        "response_format": response_format,
        "max_items": _require_int("max_items", payload.get("max_items"), 5),
        "max_depth": _require_int("max_depth", payload.get("max_depth"), 3),
        "timeout_sec": _require_int("timeout_sec", payload.get("timeout_sec"), 30),
        "save_raw": _require_bool("save_raw", payload.get("save_raw"), False),
        "raw_output_path": _require_str("raw_output_path", payload.get("raw_output_path")),
    }


def execute(payload: Any) -> dict[str, Any]:
    if requests is None:
        return error("missing_dependency", f"`requests` is required: {REQUESTS_IMPORT_ERROR}")
    config = parse_input(payload)
    url = _build_url(config["base_url"], config["path"])
    session = requests.Session()
    session.headers.update(config["headers"])

    request_kwargs: dict[str, Any] = {"params": config["params"], "timeout": config["timeout_sec"]}
    if config["json_body"] is not None:
        request_kwargs["json"] = config["json_body"]
    if config["form_body"] is not None:
        request_kwargs["data"] = config["form_body"]

    try:
        response = _bounded_request(session.request, config["method"], url, **request_kwargs)
        response.raise_for_status()
        content_type = (response.headers.get("content-type") or "").lower()
        wants_json = config["response_format"] == "json"
        wants_text = config["response_format"] == "text"
        auto_json = not wants_text and (
            "json" in content_type or response.text.lstrip().startswith(("{", "["))
        )

        if wants_json or auto_json:
            data = response.json()
            raw_output = json.dumps(data, indent=2)
            raw_output_path = None
            if config["save_raw"]:
                raw_output_path = _save_raw_output(
                    raw_output, config["raw_output_path"], config["base_url"], "json"
                )

            record_path = config["record_path"]
            path_used, target = (
                _infer_target(data)
                if record_path is None
                else (record_path, _get_by_path(data, record_path))
            )
            out = {
                "ok": True,
                "source": _service_name(config["base_url"]),
                "path": config["path"],
                "method": config["method"],
                "status_code": response.status_code,
                "record_path": path_used,
                "raw_output_path": raw_output_path,
                "warnings": [],
            }
            if isinstance(target, list):
                records = target[: config["max_items"]]
                out.update(
                    {
                        "record_count_returned": len(records),
                        "record_count_available": len(target),
                        "truncated": len(records) < len(target),
                        "records": _compact(records, config["max_items"], config["max_depth"]),
                    }
                )
            else:
                out["summary"] = _compact(target, config["max_items"], config["max_depth"])
                if isinstance(target, dict):
                    out["top_keys"] = list(target)[: config["max_items"]]
            return out

        raw_output_path = None
        if config["save_raw"]:
            raw_output_path = _save_raw_output(
                response.text, config["raw_output_path"], config["base_url"], "txt"
            )
        text_head = response.text[:800]
        return {
            "ok": True,
            "source": _service_name(config["base_url"]),
            "path": config["path"],
            "method": config["method"],
            "status_code": response.status_code,
            "content_type": content_type,
            "text_head": None if raw_output_path else text_head,
            "text_head_truncated": False
            if raw_output_path
            else len(text_head) < len(response.text),
            "raw_output_path": raw_output_path,
            "warnings": [],
        }
    except requests.HTTPError as exc:
        if exc.response is None:
            return error("http_error", f"Request failed ({type(exc).__name__}).")
        message = _extract_error_message(response)
        # Upstream diagnostics can reflect caller-supplied credentials.
        sensitive_values = list(config["headers"].values())
        sensitive_values.extend(value for key, value in config["params"].items()
                                if any(word in key.lower() for word in ("key", "token", "auth", "password")))
        for value in sensitive_values:
            if isinstance(value, str) and value:
                message = message.replace(value, "[redacted]")
        return error(
            "http_error",
            f"HTTP {response.status_code}: {message}",
        )
    except requests.RequestException as exc:
        return error("network_error", f"Request failed ({type(exc).__name__}).")
    except ValueError as exc:
        return error("invalid_response", str(exc))
    finally:
        session.close()


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
