# Fix: HTTP 403 while validating OpenCode V2 configuration

## What happened

The previous `scripts/validate_against_live_schema.py` used Python's default `urllib.request.urlopen("https://opencode.ai/config.json")` request. Some website/CDN security filters deny that request with `HTTP Error 403: Forbidden`. A 403 is a **schema-download failure**, not a failure of `opencode.jsonc` validation.

The schema is still documented at <https://opencode.ai/config.json>. OpenCode merged PR #55524 on October 14, 2026, to publish a unified schema accepting V1 and V2 field forms. The current schema contains the OpenCode V2 `permissions`, `mcp.servers`, `agents`, and `compaction.keep.tokens` properties.

## Replacement script

Run from the extracted package directory:

```bash
python3 -m pip install jsonschema
python3 scripts/validate_against_live_schema.py
```

The script now makes a browser-style request, caches a successfully retrieved **public schema** at `${XDG_CACHE_HOME:-~/.cache}/opencode-v2/config-schema.json`, and reuses this cache on connection errors. It rejects the old V1-only schema if returned by a proxy.

### If the website still returns 403

Open <https://opencode.ai/config.json> in your normal web browser, save the raw JSON as `~/Downloads/config.json`, and run:

```bash
python3 scripts/validate_against_live_schema.py --schema-file "$HOME/Downloads/config.json"
```

This performs full Draft 2020-12 schema validation **without using Python's network connection**. The `--schema-file` must contain the actual full schema, not an HTML error page.

Use a custom config path if you edited the installed file:

```bash
python3 scripts/validate_against_live_schema.py \
  --config "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/opencode.jsonc" \
  --schema-file "$HOME/Downloads/config.json"
```

### Work offline / use a previous download

```bash
python3 scripts/validate_against_live_schema.py --offline
```

If the cache is absent, it performs a CLI fallback (where possible) and clearly labels the result **PARTIAL**. The fallback is *not* equivalent to full schema validation. With `--require-schema`, missing schema always returns a nonzero exit status:

```bash
python3 scripts/validate_against_live_schema.py --require-schema
```

For JSONC comments/trailing commas rather than plain JSON, additionally install `json5`:

```bash
python3 -m pip install json5
```

## Interpretation of status messages

- `PASS: FULL ...`: `jsonschema` accepted the selected config against the retrieved, cached, or manually supplied V2 JSON Schema.
- `PARTIAL ...`: config parsed, and the local OpenCode configuration diagnostic succeeded, but the actual schema was **unavailable**.
- `UNVERIFIED ...`: neither schema validation nor CLI runtime checks could be completed. This is not a definitive finding about the config's validity.
- `FAIL ...`: parse error, invalid schema, a schema rejection, or a CLI diagnostic failure.

Inspect the installed configuration and CLI separately with `opencode debug config` and `opencode debug agents`. `opencode debug config` lists configuration sources in V2; it does not necessarily validate any arbitrary file passed with `--config`.

## Sources

- [OpenCode V2 configuration documentation](https://opencode.ai/v2/docs/config)
- [Published OpenCode config schema](https://opencode.ai/config.json)
- [Schema fix PR #55524, merged October 14, 2026](https://github.com/anomalyco/opencode/pull/55524)
- [OpenCode V2 CLI diagnostics](https://opencode.ai/v2/docs/cli/commands/)
