#!/usr/bin/env python3
"""genebass-gene-burden

Fetch Genebass gene burden PheWAS associations for one Ensembl gene input.
Input JSON on stdin:
  - {"ensembl_gene_id":"ENSG00000173531"}
  - {"ensembl_gene_id":"ENSG00000173531","burden_set":"pLoF","max_results":100}
  - "ENSG00000173531"
Output JSON on stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote, unquote

import requests

GENEBASS_API_BASE = "https://main.genebass.org/api"
USER_AGENT = "genebass-gene-burden-skill/1.0 (+requests)"
DEFAULT_TIMEOUT_S = 30
CANONICAL_BURDEN_SETS = ("pLoF", "missense|LC", "synonymous")
ENSG_RE = re.compile(r"^ENSG[0-9]+(?:\.[0-9]+)?$", re.IGNORECASE)


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


def normalize_gene_id(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Ensembl gene ID is empty.")
    if not ENSG_RE.match(value):
        raise ValueError(
            "Invalid Ensembl gene ID. Expected format like ENSG00000173531 (optional .version)."
        )
    value = value.upper()
    if "." in value:
        value = value.split(".", 1)[0]
    return value


def normalize_burden_set(raw: str) -> str:
    value = unquote(raw.strip())
    key = re.sub(r"[^a-z0-9]", "", value.lower())

    if key in {"plof", "lof"}:
        return "pLoF"
    if key in {"missense", "missenselc"}:
        return "missense|LC"
    if key == "synonymous":
        return "synonymous"

    canonical = ", ".join(CANONICAL_BURDEN_SETS)
    raise ValueError(
        f"Invalid `burden_set`. Allowed canonical values: {canonical}. "
        "Accepted aliases: LoF/LOF/lof/plof -> pLoF; missense -> missense|LC."
    )


def parse_input(payload: Any) -> tuple[str, str, int | None]:
    if isinstance(payload, str):
        return normalize_gene_id(payload), "pLoF", None

    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON string or object.")

    gene = payload.get("ensembl_gene_id") or payload.get("gene_id") or payload.get("gene")
    if not gene or not isinstance(gene, str):
        raise ValueError("Provide `ensembl_gene_id` as a non-empty string.")
    gene_id = normalize_gene_id(gene)

    burden_raw = payload.get("burden_set", "pLoF")
    if not isinstance(burden_raw, str) or not burden_raw.strip():
        raise ValueError("`burden_set` must be a non-empty string when provided.")
    burden_set = normalize_burden_set(burden_raw)

    max_results = payload.get("max_results")
    if max_results is None:
        return gene_id, burden_set, None

    if type(max_results) is not int or max_results <= 0:
        raise ValueError("`max_results` must be a positive integer when provided.")
    return gene_id, burden_set, max_results


def fetch_gene_phewas(gene_id: str, burden_set: str) -> tuple[str, Any, int]:
    encoded_gene = quote(gene_id, safe="")
    encoded_burden = quote(burden_set, safe="|")
    url = f"{GENEBASS_API_BASE}/phewas/{encoded_gene}?burdenSet={encoded_burden}"
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    resp = _bounded_request(requests.get, url, headers=headers, timeout=DEFAULT_TIMEOUT_S)
    status_code = resp.status_code
    if status_code == 404:
        return url, None, status_code
    if status_code >= 400:
        snippet = " ".join(resp.text.split())[:180]
        raise RuntimeError(f"Genebass API returned HTTP {status_code}: {snippet}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Genebass API returned non-JSON for URL {url}") from exc
    return url, data, status_code


def fetch_phenotypes_metadata() -> list[dict[str, Any]]:
    url = f"{GENEBASS_API_BASE}/phenotypes"
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    resp = _bounded_request(requests.get, url, headers=headers, timeout=DEFAULT_TIMEOUT_S)
    if resp.status_code >= 400:
        snippet = " ".join(resp.text.split())[:180]
        raise RuntimeError(f"Genebass phenotypes API returned HTTP {resp.status_code}: {snippet}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError("Genebass phenotypes API returned non-JSON.") from exc

    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


def build_description_map(phenotypes: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in phenotypes:
        analysis_id = row.get("analysis_id")
        description = row.get("description")
        if isinstance(analysis_id, str) and analysis_id and isinstance(description, str):
            mapping[analysis_id] = description
    return mapping


def unpack_phewas_payload(data: Any) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if data is None:
        return None, []

    if isinstance(data, dict):
        gene = data.get("gene") if isinstance(data.get("gene"), dict) else None
        rows = data.get("phewas") if isinstance(data.get("phewas"), list) else []
        return gene, [row for row in rows if isinstance(row, dict)]

    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and isinstance(first.get("phewas"), list):
            gene = first.get("gene") if isinstance(first.get("gene"), dict) else None
            rows = first.get("phewas") or []
            return gene, [row for row in rows if isinstance(row, dict)]
        return None, [row for row in data if isinstance(row, dict)]

    return None, []


def build_phenotype_id(row: dict[str, Any]) -> str:
    trait_type = row.get("trait_type", "")
    phenocode = row.get("phenocode", "")
    pheno_sex = row.get("pheno_sex", "")
    coding = row.get("coding", "")
    modifier = row.get("modifier", "")
    return f"{trait_type}-{phenocode}-{pheno_sex}-{coding}-{modifier}"


def transform_rows(
    rows: list[dict[str, Any]], description_map: dict[str, str]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        phenotype_id = build_phenotype_id(row)
        out.append(
            {
                "phenotype_id": phenotype_id,
                "phenotype_description": description_map.get(phenotype_id),
                "skat_o_pvalue": row.get("Pvalue"),
            }
        )
    return out


def main() -> int:
    warnings: list[str] = []

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001
        sys.stdout.write(json.dumps(error("invalid_json", f"Could not parse JSON input: {exc}")))
        return 2

    try:
        gene_id, burden_set, max_results = parse_input(payload)
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_input", str(exc))))
        return 2

    try:
        query_url, data, status_code = fetch_gene_phewas(gene_id, burden_set)
    except requests.RequestException as exc:
        sys.stdout.write(json.dumps(error("network_error", f"Request failed ({type(exc).__name__}).")))
        return 1
    except ValueError as exc:
        sys.stdout.write(json.dumps(error("invalid_response", str(exc))))
        return 1
    except RuntimeError as exc:
        message = str(exc)
        code = "upstream_error"
        if "HTTP 500" in message:
            code = "not_found_or_invalid_upstream_request"
            message = (
                "Genebass returned HTTP 500. This often means an unknown gene ID or invalid "
                "burden_set. Use Ensembl IDs and burden_set in "
                "{pLoF, missense|LC, synonymous} (aliases are accepted)."
            )
        sys.stdout.write(json.dumps(error(code, message)))
        return 1

    if status_code == 404:
        warnings.append("Gene not found in Genebass PheWAS API (HTTP 404).")
        output = {
            "ok": True,
            "source": "genebass",
            "input": {"type": "ensembl_gene_id", "value": gene_id},
            "burden_set": burden_set,
            "query_url": query_url,
            "gene": None,
            "association_count": 0,
            "association_count_total": 0,
            "truncated": False,
            "associations": [],
            "warnings": warnings,
        }
        sys.stdout.write(json.dumps(output))
        return 0

    description_map: dict[str, str] = {}
    try:
        phenotypes = fetch_phenotypes_metadata()
        description_map = build_description_map(phenotypes)
    except requests.RequestException as exc:
        warnings.append(f"Could not fetch phenotype descriptions ({type(exc).__name__}).")
    except (RuntimeError, ValueError) as exc:
        warnings.append(str(exc))

    gene, rows = unpack_phewas_payload(data)
    associations = transform_rows(rows, description_map)
    total = len(associations)
    if max_results is not None and total > max_results:
        associations = associations[:max_results]
    truncated = len(associations) < total

    gene_out = None
    if isinstance(gene, dict):
        gene_out = {
            "gene_id": gene.get("gene_id"),
            "symbol": gene.get("symbol"),
            "name": gene.get("name"),
        }

    output = {
        "ok": True,
        "source": "genebass",
        "input": {"type": "ensembl_gene_id", "value": gene_id},
        "burden_set": burden_set,
        "query_url": query_url,
        "gene": gene_out,
        "association_count": len(associations),
        "association_count_total": total,
        "truncated": truncated,
        "associations": associations,
        "warnings": warnings,
    }
    sys.stdout.write(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
