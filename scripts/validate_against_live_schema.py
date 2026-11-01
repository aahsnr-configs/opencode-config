#!/usr/bin/env python3
"""Validate an OpenCode V2 config against its published schema when available.

Unlike the previous version, HTTP 403 and other download failures do not imply a
config error. Use a saved official schema (or cached copy), or run the local CLI
as a *partial fallback*; never describe that fallback as a full schema check.

This script makes no model calls, changes no connected accounts, and never
writes to an OpenCode config or authorization file. It stores only a public
schema cache (not configuration contents or credentials).
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

SCHEMA_URL = "https://opencode.ai/config.json"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "opencode.jsonc"
DEFAULT_CACHE = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))).expanduser() / "opencode-v2" / "config-schema.json"


def parse_json_or_jsonc(path):
    raw = Path(path).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        try:
            import json5  # Optional for commented/trailing-comma JSONC files.
        except ImportError:
            raise ValueError(f"{path}: JSON parsing failed: {exc}. If you use JSONC comments/trailing commas, install 'json5' (python3 -m pip install json5).") from exc
        return json5.loads(raw)


def is_v2_schema(schema):
    """Reject wrong-format HTML or legacy-only schemas as a source of truth."""
    if not isinstance(schema, dict):
        return False
    props = schema.get("properties", {})
    mcp = props.get("mcp", {})
    return (
        isinstance(props.get("permissions"), dict)
        and isinstance(props.get("agents"), dict)
        and isinstance(mcp.get("properties"), dict)
        and "servers" in mcp["properties"]
        and isinstance(props.get("compaction"), dict)
        and "keep" in props["compaction"].get("properties", {})
    )


def fetch_schema(url=SCHEMA_URL, timeout=15):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/128.0",
            "Accept": "application/schema+json, application/json;q=0.9, */*;q=0.1",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def load_cache(cache_path):
    if not cache_path.is_file():
        raise FileNotFoundError(str(cache_path))
    value = parse_json_or_jsonc(cache_path)
    if not is_v2_schema(value):
        raise ValueError("Cached schema does not contain required OpenCode V2 fields")
    return value


def atomic_store(path, schema):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        fd, name = tempfile.mkstemp(prefix=".config-schema-", suffix=".json", dir=str(path.parent))
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(schema, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if name is not None and os.path.exists(name):
            os.unlink(name)


def validate_schema(schema, config):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        raise RuntimeError("Full schema validation requires jsonschema: python3 -m pip install jsonschema")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(config), key=lambda err: (list(map(str, err.absolute_path)), err.message))
    if errors:
        for error in errors[:10]:
            location = "$" + "".join(f"[{json.dumps(x)}]" for x in error.absolute_path)
            print(f"FAIL: {location}: {error.message}", file=sys.stderr)
        if len(errors) > 10:
            print(f"... plus {len(errors) - 10} additional errors", file=sys.stderr)
        return False
    return True


def cli_fallback(config_path):
    binary = shutil.which("opencode")
    if not binary:
        print("NOTICE: 'opencode' is unavailable; cannot perform runtime fallback.")
        return False
    # This check verifies that the installed CLI can load its active configuration.
    # It is NOT equivalent to JSON Schema validation of an arbitrary --config file.
    try:
        result = subprocess.run(
            [binary, "debug", "config"],
            cwd=str(config_path.parent),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"FAIL: OpenCode CLI diagnostic could not run: {exc}", file=sys.stderr)
        return False
    if result.returncode:
        print(f"FAIL: 'opencode debug config' exited {result.returncode}.", file=sys.stderr)
        if result.stderr:
            print(result.stderr[:1500], file=sys.stderr)
        return False
    print("PASS: OpenCode runtime configuration-source diagnostic exited successfully.")
    print("NOTICE: This confirms only runtime diagnostic success, NOT full schema validation of the supplied file.")
    if config_path.resolve() != (ROOT / "opencode.jsonc").resolve():
        print("NOTICE: Check 'opencode debug config' separately to confirm it loaded your --config path.")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Config to validate (default: bundled opencode.jsonc)")
    parser.add_argument("--schema-file", type=Path, help="Use an official schema JSON downloaded in your browser (no network request)")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="Local public-schema cache")
    parser.add_argument("--offline", action="store_true", help="Do not fetch the schema; use --schema-file or cached schema")
    parser.add_argument("--require-schema", action="store_true", help="Exit nonzero if full schema validation cannot be performed")
    args = parser.parse_args(argv)
    try:
        config = parse_json_or_jsonc(args.config)
        if not isinstance(config, dict):
            raise ValueError("Configuration root must be a JSON object")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: Could not parse configuration: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: Parsed configuration: {args.config}")

    schema = None
    source = None
    fetch_error = None
    if args.schema_file:
        try:
            schema = parse_json_or_jsonc(args.schema_file)
            source = f"explicit file: {args.schema_file}"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"FAIL: Could not read --schema-file: {exc}", file=sys.stderr)
            return 1
    elif not args.offline:
        try:
            schema = fetch_schema()
            if not is_v2_schema(schema):
                raise ValueError("downloaded schema does not contain the OpenCode V2 fields (possible stale response)")
            atomic_store(args.cache, schema)
            source = SCHEMA_URL
        except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
            fetch_error = str(exc)
            print(f"NOTICE: Official schema download unavailable: {fetch_error}")
    if schema is None:
        try:
            schema = load_cache(args.cache)
            source = f"previously downloaded V2 schema cache: {args.cache}"
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    if schema is not None:
        if not is_v2_schema(schema):
            print("FAIL: Schema appears stale or incompatible with OpenCode V2; refusing misleading validation.", file=sys.stderr)
            return 1
        try:
            if not validate_schema(schema, config):
                return 1
        except Exception as exc:
            print(f"FAIL: Schema validation could not run: {exc}", file=sys.stderr)
            return 1
        print(f"PASS: FULL OpenCode V2 JSON Schema validation using {source}")
        return 0

    print("SKIP: Full JSON Schema validation (official schema not available locally).")
    print("For full validation, download https://opencode.ai/config.json in a browser and run:")
    print("  python3 scripts/validate_against_live_schema.py --schema-file ~/Downloads/config.json")
    if args.require_schema:
        print("FAIL: --require-schema was specified; schema is unavailable.", file=sys.stderr)
        return 2
    if cli_fallback(args.config):
        print("PARTIAL: JSON parsing and runtime diagnostic passed; full schema check SKIPPED.")
        return 0
    print("UNVERIFIED: JSON parsed, but no schema or successful OpenCode runtime check is available.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
