from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import requests

ENSEMBL_GRCH38 = "https://rest.ensembl.org"
ENSEMBL_GRCH37 = "https://grch37.rest.ensembl.org"

DEFAULT_TIMEOUT_S = 15
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
USER_AGENT = "variant-coordinate-finder/1.0 (+requests)"

SEP_RE = re.compile(r"[-:_/\s]+")
CHR_RE = re.compile(r"^(?:chr)?([0-9]{1,2}|X|Y|M|MT)$", re.IGNORECASE)
ALLELE_RE = re.compile(r"^(?:[ACGTN]+|\*)$")


class VariantResolutionError(Exception):
    def __init__(self, code: str, message: str, warnings: list[str] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.warnings = warnings or []


@dataclass
class Coord:
    chr: str
    pos: int
    ref: str | None
    alts: list[str]


def build_key_for(build: str) -> str:
    return "grch37" if build in {"GRCh37", "hg19"} else "grch38"


def build_variant_record(
    chrom: str,
    pos: int,
    ref: str | None,
    alt: str | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "chr": chrom,
        "pos": pos,
        "ref": ref,
        "alt": alt,
    }
    if ref is not None and alt is not None:
        record["canonical"] = f"{chrom}:{pos}-{ref}-{alt}"
    return record


def parse_variant_string(value: str) -> tuple[str, int, str, str]:
    raw = value.strip()
    if not raw:
        raise ValueError("Variant string is empty.")

    parts = [part for part in SEP_RE.split(raw) if part]
    if len(parts) != 4:
        raise ValueError(
            "Invalid variant format. Expected chrom-pos-ref-alt with flexible separators."
        )

    chrom_raw, pos_raw, ref_raw, alt_raw = parts
    match = CHR_RE.match(chrom_raw)
    if not match:
        raise ValueError(f"Invalid chromosome: {chrom_raw!r}")

    chrom = match.group(1).upper()
    if chrom == "M":
        chrom = "MT"
    if chrom.isdigit() and not 1 <= int(chrom) <= 22:
        raise ValueError("Chromosome must be 1-22, X, Y or MT.")

    try:
        pos = int(pos_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid position: {pos_raw!r}") from exc
    if pos <= 0:
        raise ValueError("Position must be > 0.")

    ref = ref_raw.upper()
    alt = alt_raw.upper()
    if not ALLELE_RE.match(ref):
        raise ValueError(f"Invalid REF allele: {ref_raw!r}")
    if not ALLELE_RE.match(alt):
        raise ValueError(f"Invalid ALT allele: {alt_raw!r}")

    if ref == alt:
        raise ValueError("REF and ALT must differ.")
    return chrom, pos, ref, alt


def extract_variant_input(payload: Any, *, default_build_key: str) -> tuple[str, str]:
    if isinstance(payload, str):
        return default_build_key, payload.strip()

    if not isinstance(payload, dict):
        raise ValueError("Input must be a JSON string or object.")

    provided: list[tuple[str, str]] = []
    for key in ("rsid", "grch37", "grch38", "variant"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            provided.append((key, value.strip()))

    if not provided:
        raise ValueError(
            f"Provide exactly one of `rsid`, `grch37`, `grch38`, or `{default_build_key}`."
        )
    if len(provided) != 1:
        raise ValueError(
            "Provide exactly one variant input: `rsid`, `grch37`, `grch38`, or `variant`."
        )

    input_type, input_value = provided[0]
    if input_type == "variant":
        input_type = default_build_key
    return input_type, input_value


def _server_for(build: str) -> str:
    return ENSEMBL_GRCH37 if build in {"GRCh37", "hg19"} else ENSEMBL_GRCH38


def _assembly_cmp(build: str) -> str:
    return "GRCh37" if build in {"GRCh37", "hg19"} else "GRCh38"


def _get_json(url: str, *, timeout: int = DEFAULT_TIMEOUT_S) -> Any:
    if type(timeout) is not int or timeout <= 0:
        raise VariantResolutionError("invalid_input", "Timeout must be a positive integer.")
    try:
        parsed = urlsplit(url)
        origin = (parsed.scheme, parsed.hostname, parsed.port if parsed.port is not None else 443)
        allowed = {("https", "rest.ensembl.org", 443), ("https", "grch37.rest.ensembl.org", 443)}
        if (origin not in allowed or parsed.username is not None or parsed.password is not None
                or parsed.fragment or "\\" in url or any(character.isspace() for character in url)):
            raise ValueError("Unsupported Ensembl URL")
    except (TypeError, ValueError) as exc:
        raise VariantResolutionError("invalid_input", "Use an Ensembl HTTPS URL without embedded credentials.") from exc
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=False, stream=True)
    try:
        if 300 <= response.status_code < 400:
            raise VariantResolutionError("redirect_refused", "Ensembl redirected the request; refusing another endpoint.")
        response.raise_for_status()
        body = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                raise VariantResolutionError("response_too_large", "Ensembl response exceeds the 5 MiB limit.")
            body.extend(chunk)
        try:
            return json.loads(body)
        except (ValueError, RecursionError) as exc:
            raise VariantResolutionError("invalid_response", "Ensembl returned invalid or excessively nested JSON.") from exc
    finally:
        response.close()


def lookup_rsid(rsid: str, build: str = "GRCh38") -> Coord | None:
    server = _server_for(build)
    asm = _assembly_cmp(build)
    url = (
        f"{server}/variation/human/{requests.utils.quote(rsid, safe='')}"
        "?content-type=application/json"
    )

    data = _get_json(url, timeout=DEFAULT_TIMEOUT_S)
    mappings = data.get("mappings") if isinstance(data, dict) else None
    if not mappings:
        return None

    matches: dict[tuple[Any, ...], Coord] = {}
    for mapping in mappings:
        if not isinstance(mapping, dict) or mapping.get("assembly_name") != asm:
            continue
        chrom = str(mapping.get("seq_region_name", ""))
        if not CHR_RE.fullmatch(chrom) or (chrom.isdigit() and not 1 <= int(chrom) <= 22):
            continue
        if mapping.get("strand", 1) != 1:
            raise VariantResolutionError("uncertain_allele_mapping", "Reverse-strand mappings require explicit target-build coordinates.")
        pos = mapping.get("start")
        allele_string = mapping.get("allele_string")
        if type(pos) is not int or pos <= 0 or not isinstance(allele_string, str):
            raise VariantResolutionError("invalid_response", "Ensembl mapping has incomplete coordinates or alleles.")
        alleles = allele_string.split("/")
        if len(alleles) < 2 or not all(ALLELE_RE.fullmatch(a) for a in alleles):
            raise VariantResolutionError("uncertain_allele_mapping", "Unanchored or incomplete alleles require explicit target-build coordinates.")
        matches[(chrom, pos, allele_string)] = Coord(chrom, pos, alleles[0], alleles[1:])
    if len(matches) > 1:
        raise VariantResolutionError("ambiguous_variant", "Multiple assembly mappings found; provide explicit target-build coordinates.")
    return next(iter(matches.values()), None)


def lookup_position(
    chrom: str,
    pos: int,
    build: str = "GRCh38",
    ref: str | None = None,
    alt: str | None = None,
) -> tuple[str, str | None, list[str]] | None:
    server = _server_for(build)
    url = (
        f"{server}/overlap/region/human/{chrom}:{pos}-{pos}"
        "?feature=variation;content-type=application/json"
    )
    data = _get_json(url, timeout=DEFAULT_TIMEOUT_S)
    if not isinstance(data, list):
        raise VariantResolutionError("invalid_response", "Ensembl overlap response must be a list.")

    matches = {}
    for variant in data:
        if not isinstance(variant, dict):
            continue
        rsid = variant.get("id")
        alleles = variant.get("alleles")
        if (
            isinstance(rsid, str) and re.fullmatch(r"rs[0-9]+", rsid)
            and str(variant.get("seq_region_name")) == chrom
            and variant.get("start") == pos
            and variant.get("strand", 1) == 1
            and isinstance(alleles, list) and len(alleles) >= 2
            and ref == alleles[0] and alt in alleles[1:]
        ):
            matches[rsid] = (rsid, alleles[0], alleles[1:])
    if len(matches) > 1:
        raise VariantResolutionError("ambiguous_variant", "Multiple rsIDs match these coordinates and alleles; provide an explicit target-build variant.")
    return next(iter(matches.values()), None)


def _coord_details(coord: Coord | None) -> dict[str, Any] | None:
    if coord is None:
        return None
    return {"chr": coord.chr, "pos": coord.pos, "ref": coord.ref, "alts": coord.alts}


def resolve_rsid_both_builds(rsid: str) -> dict[str, Any]:
    result: dict[str, Any] = {"rsid": rsid, "warnings": []}
    for build, key in (("GRCh38", "grch38"), ("GRCh37", "grch37")):
        try:
            result[key] = _coord_details(lookup_rsid(rsid, build))
        except requests.RequestException as exc:
            result[key] = None
            result["warnings"].append(f"{build} lookup failed: {type(exc).__name__}")
    return result


def resolve_position_both_builds(
    chrom: str, pos: int, build: str, ref: str, alt: str,
) -> dict[str, Any] | None:
    native_key = build_key_for(build)
    other_build = "GRCh38" if native_key == "grch37" else "GRCh37"
    match = lookup_position(chrom, pos, build, ref, alt)
    if match is None:
        return None
    rsid, matched_ref, alts = match
    result = {"rsid": rsid, "warnings": [], native_key: {
        "chr": chrom, "pos": pos, "ref": matched_ref, "alts": alts,
    }}
    try:
        result[build_key_for(other_build)] = _coord_details(lookup_rsid(rsid, other_build))
    except requests.RequestException as exc:
        result[build_key_for(other_build)] = None
        result["warnings"].append(f"Other-build lookup failed: {type(exc).__name__}")
    return result


def resolve_variant(input_type: str, input_value: str) -> dict[str, Any]:
    requested_ref = None
    requested_alt = None
    if input_type == "rsid":
        rsid = input_value.strip()
        if not re.fullmatch(r"rs[0-9]+", rsid):
            raise ValueError("rsid must be 'rs' followed by digits.")
        resolved = resolve_rsid_both_builds(rsid)
    elif input_type in {"grch37", "grch38"}:
        build = "GRCh37" if input_type == "grch37" else "GRCh38"
        chrom, pos, requested_ref, requested_alt = parse_variant_string(input_value)
        resolved = resolve_position_both_builds(chrom, pos, build, requested_ref, requested_alt)
        if resolved is None:
            raise VariantResolutionError(
                "not_found", f"No exact rsID match for {chrom}:{pos}-{requested_ref}-{requested_alt} on {build}.",
            )
    else:
        raise ValueError(f"Unsupported input type: {input_type!r}")

    output = {"input": {"type": input_type, "value": input_value},
              "rsid": resolved["rsid"], "warnings": resolved["warnings"]}
    for key in ("grch37", "grch38"):
        coord = resolved.get(key)
        if coord is None:
            output[key] = None
            continue
        ref, alts = coord["ref"], coord["alts"]
        if not ref or not alts:
            raise VariantResolutionError("resolution_failed", "Resolved variant has no complete allele information.")
        if requested_alt is None:
            if len(alts) != 1:
                raise VariantResolutionError("ambiguous_variant", "Multiallelic rsID requires an explicit target-build REF/ALT variant.")
            alt = alts[0]
        else:
            if ref != requested_ref or requested_alt not in alts:
                raise VariantResolutionError("uncertain_allele_mapping", "Alleles differ between assemblies; provide an explicit target-build variant. Automatic allele substitution is refused.")
            alt = requested_alt
        output[key] = build_variant_record(coord["chr"], coord["pos"], ref, alt)
    return output


def resolve_query_variant(
    *,
    input_type: str,
    input_value: str,
    target_build: str,
) -> dict[str, Any]:
    target_key = build_key_for(target_build)
    if input_type == target_key:
        chrom, pos, ref, alt = parse_variant_string(input_value)
        target_variant = build_variant_record(chrom, pos, ref, alt)
        return {
            "input": {"type": input_type, "value": input_value},
            "query_variant": target_variant,
            "rsid": None,
            "grch37": target_variant if target_key == "grch37" else None,
            "grch38": target_variant if target_key == "grch38" else None,
            "warnings": [],
        }

    resolved = resolve_variant(input_type, input_value)
    target_variant = resolved.get(target_key)
    if not isinstance(target_variant, dict) or not target_variant.get("canonical"):
        raise VariantResolutionError(
            "resolution_failed",
            f"Could not resolve input variant to {target_build}.",
            warnings=list(resolved.get("warnings") or []),
        )

    return {
        "input": resolved["input"],
        "query_variant": target_variant,
        "rsid": resolved.get("rsid"),
        "grch37": resolved.get("grch37"),
        "grch38": resolved.get("grch38"),
        "warnings": list(resolved.get("warnings") or []),
    }
