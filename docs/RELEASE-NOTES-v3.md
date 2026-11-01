# Schema-validator HTTP 403 fix — 2026-11-01

- Browser-like HTTP request headers added for public JSON Schema download.
- Successful schema downloads are cached for later offline use.
- New `--schema-file` option accepts JSON saved by the user's browser, avoiding Python network requests entirely.
- New `--offline`, `--cache`, `--config`, and `--require-schema` options.
- Correct distinction between full schema validation, partial CLI fallback, and unavailable verification.
- Explicit stale V1 schema detection to avoid misleading failures on valid V2 fields.
- JSONC support via optional `json5` module.
- Ten new regression tests for error cases, cache, schema checks, and JSONC.
- **No changes made to `opencode.jsonc`, agents, permissions, or MCP server settings.**
- Live V2 CLI, network 403 behavior on the user's machine, and full official schema-validation could not be executed in the isolated build environment.

See `docs/SCHEMA-403-FIX.md`.
