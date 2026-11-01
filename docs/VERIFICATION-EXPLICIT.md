# Explicit MCP package verification

Checked November 1, 2026. These are **offline** checks, not a claim of live service compatibility.

- All nine static MCP definitions start `disabled: true` and `codemode: false`.
- Every named MCP tool `NAME_*` is explicitly `ask`, and MCP resource operations also require approval.
- Global `mcp.use` allowlist denies unknown MCP services (OpenCode 2.2.3 or newer).
- The human-operated runtime controller cannot use a non-loopback server and requires interactive terminal confirmation.
- Controller regression tests run against a mock local HTTP server and verify connect, disconnect, session cleanup, cancellation, off-by-default configuration and non-network list.
- Existing installer, schema-403, diagnostics, agents, commands and skills tests pass offline.
- Complete ZIP is checked for CRC and checksum integrity.

Not tested: live OpenCode V2 implementation of experimental API endpoints, OpenChamber Desktop backend URL, OAuth credentials, model inference, actual MCP server behavior and live official schema validation (the schema URL may reject scripted downloads). The runtime endpoints are documented but experimental.

Sources: https://opencode.ai/v2/docs/mcp-servers ; https://opencode.ai/v2/docs/api ; https://opencode.ai/v2/docs/policies ; https://docs.openchamber.dev/mcp/ ; https://docs.openchamber.dev/opencode-server/ .
