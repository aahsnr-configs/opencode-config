# Release notes — agent-discovery correction (2026-11-01)

- **Fix**: `doctor.sh` uses `opencode debug agents` (V2), not `opencode agent list` (V1).
- **Fix**: removes unsupported `opencode debug skill` command and checks bundled skill metadata in `validate.py` instead.
- **Improvement**: checks all six expected custom agents in runtime discovery output, distinguishes missing files from invalid CLI commands, and reports troubleshooting steps.
- **Improvement**: `doctor.sh --details` shows full local diagnostics; treat output as potentially sensitive.
- **Improvement**: mocked V2 and V1 CLI tests and extra offline configuration contract assertions.
- **Documentation**: fixes V2 command references, explains `debug config` reports configuration sources, not merged settings.
- **Configuration**: `opencode.jsonc` remains semantically unchanged. Its top-level fields, permission rule shape and values, MCP server definitions and compaction settings were cross-checked with the live official OpenCode V2 schema at https://opencode.ai/config.json (2026-11-01). The complete official schema could not be downloaded into the build container, so full machine-executed schema validation is deferred to `python3 scripts/validate_against_live_schema.py` on a connected machine.
- **Caveat**: OpenCode CLI and OpenChamber Desktop were not executed in this environment. Runtime behavior may differ by installed version and customized configuration.
