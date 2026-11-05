#!/usr/bin/env python3
"""ukb-topmed-phewas

Fetch UKB-TOPMed PheWAS associations for one variant input.
Input JSON on stdin:
  - {"grch38":"10-112998590-C-T"}
  - {"grch37":"10:114758349:C:T","max_results":25}
  - {"rsid":"rs7903146","max_results":25,"save_raw":true}
  - "10-112998590-C-T"
Output JSON on stdout.
"""

from __future__ import annotations

import json
import math
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import requests
from variant_resolution import (
    VariantResolutionError,
    extract_variant_input,
    resolve_query_variant,
)

UKB_TOPMED_BASE = "https://pheweb.org/UKB-TOPMed"
USER_AGENT = "ukb-topmed-phewas-skill/1.0 (+requests)"
DEFAULT_TIMEOUT_S = 20
DEFAULT_MAX_RESULTS = 10
SAFE_PATH_RE = re.compile(r"[^A-Za-z0-9._-]+")


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
    return {
        "ok": False,
        "error": {"code": code, "message": message},
        "warnings": warnings or [],
    }


def parse_input(payload: Any) -> tuple[str, str, int, bool, str | None, float]:
    if isinstance(payload, str):
        return "grch38", payload.strip(), DEFAULT_MAX_RESULTS, False, None, DEFAULT_TIMEOUT_S

    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON string or object.")

    input_type, variant = extract_variant_input(payload, default_build_key="grch38")

    max_results = payload.get("max_results", DEFAULT_MAX_RESULTS)
    if type(max_results) is not int or max_results <= 0:
        raise ValueError("`max_results` must be a positive integer when provided.")

    save_raw = payload.get("save_raw", False)
    if not isinstance(save_raw, bool):
        raise ValueError("`save_raw` must be a boolean when provided.")

    raw_output_path = payload.get("raw_output_path")
    if raw_output_path is not None:
        if not isinstance(raw_output_path, str) or not raw_output_path.strip():
            raise ValueError("`raw_output_path` must be a non-empty string when provided.")
        raw_output_path = raw_output_path.strip()

    timeout_sec = payload.get("timeout_sec", DEFAULT_TIMEOUT_S)
    if (type(timeout_sec) not in (int, float) or not math.isfinite(timeout_sec) or timeout_sec <= 0):
        raise ValueError("`timeout_sec` must be a positive number when provided.")

    return input_type, variant, max_results, save_raw, raw_output_path, float(timeout_sec)


def fetch_variant(
    session: requests.Session,
    variant_str: str,
    timeout_sec: float,
) -> tuple[Any | None, int | None]:
    encoded = requests.utils.quote(variant_str, safe=":-")
    url = f"{UKB_TOPMED_BASE}/api/variant/{encoded}"
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    resp = _bounded_request(session.get, url, headers=headers, timeout=timeout_sec)
    if resp.status_code == 404:
        return None, 404
    resp.raise_for_status()
    return resp.json(), resp.status_code


def extract_associations(data: Any) -> list[Any]:
    if data is None:
        return []
    if isinstance(data, dict) and isinstance(data.get("phenos"), list):
        return data["phenos"]
    if isinstance(data, list):
        return data
    return []


def resolve_raw_output_path(canonical_variant: str, raw_output_path: str | None) -> Path:
    if raw_output_path:
        return Path(raw_output_path).expanduser()

    safe_variant = SAFE_PATH_RE.sub("_", canonical_variant).strip("._") or "variant"
    return Path(tempfile.mkdtemp(prefix="opencode-life-sciences-")) / f"ukb-topmed-phewas-{safe_variant}.json"


def write_raw_json(path: Path, data: Any) -> None:
    _check_output_parent(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream)


def main() -> int:
    warnings: list[str] = []

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(json.dumps(error("invalid_json", f"Could not parse JSON input: {exc}")))
        return 2

    try:
        input_type, input_variant, max_results, save_raw, raw_output_path, timeout_sec = (
            parse_input(payload)
        )
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_input", str(exc))))
        return 2

    try:
        resolution = resolve_query_variant(
            input_type=input_type,
            input_value=input_variant,
            target_build="GRCh38",
        )
        parsed = dict(resolution["query_variant"])
        warnings.extend(resolution["warnings"])
    except requests.RequestException as exc:
        sys.stdout.write(json.dumps(error("network_error", f"Request failed ({type(exc).__name__}).")))
        return 1
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_input", str(exc))))
        return 2
    except VariantResolutionError as exc:
        sys.stdout.write(json.dumps(error(exc.code, exc.message, exc.warnings)))
        return 1

    session = requests.Session()
    try:
        data, status_code = fetch_variant(session, parsed["canonical"], timeout_sec)
    except requests.RequestException as exc:
        sys.stdout.write(json.dumps(error("network_error", f"Request failed ({type(exc).__name__}).")))
        return 1
    except ValueError as exc:
        sys.stdout.write(
            json.dumps(error("invalid_response", f"UKB-TOPMed returned non-JSON: {exc}"))
        )
        return 1

    variant_url = f"{UKB_TOPMED_BASE}/variant/{parsed['canonical']}"
    saved_raw_output_path: str | None = None
    if save_raw and data is not None:
        try:
            raw_path = resolve_raw_output_path(parsed["canonical"], raw_output_path)
            write_raw_json(raw_path, data)
        except OSError as exc:
            sys.stdout.write(json.dumps(error("write_error", f"Could not write raw output: {exc}")))
            return 1
        saved_raw_output_path = str(raw_path)

    if status_code == 404:
        warnings.append("Variant not found in UKB-TOPMed PheWAS API (HTTP 404).")
        output = {
            "ok": True,
            "source": "ukb-topmed",
            "input": resolution["input"],
            "query_variant": parsed,
            "max_results_applied": max_results,
            "association_count": 0,
            "association_count_total": 0,
            "truncated": False,
            "associations": [],
            "variant": None,
            "variant_url": variant_url,
            "raw_output_path": None,
            "warnings": warnings,
        }
        sys.stdout.write(json.dumps(output))
        return 0

    associations = extract_associations(data)
    total = len(associations)
    if total > max_results:
        associations = associations[:max_results]
    truncated = len(associations) < total

    variant_info = None
    if isinstance(data, dict):
        variant_info = {
            "chrom": data.get("chrom"),
            "pos": data.get("pos"),
            "ref": data.get("ref"),
            "alt": data.get("alt"),
            "rsids": data.get("rsids"),
            "variant_name": data.get("variant_name"),
            "nearest_genes": data.get("nearest_genes"),
        }

    output = {
        "ok": True,
        "source": "ukb-topmed",
        "input": resolution["input"],
        "query_variant": parsed,
        "max_results_applied": max_results,
        "association_count": len(associations),
        "association_count_total": total,
        "truncated": truncated,
        "associations": associations,
        "variant": variant_info,
        "variant_url": variant_url,
        "raw_output_path": saved_raw_output_path,
        "warnings": warnings,
    }
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
