# Explicit MCP release (2026-11-01)

- Every MCP entry remains `disabled: true`.
- Per-server `codemode: false` and per-tool permission `ask`, plus MCP resource approval.
- Unknown MCP services denied by a new `mcp.use` policy; OpenCode >= 2.2.3 required.
- Added experimental *runtime* manual connect/disconnect controller for one shared OpenCode V2 server.
- CLI `/mcps` and OpenChamber Settings → MCP documented as supported fallback.
- Existing agents, commands, skills, tests, 403 schema fallback and installer retained.
- Explicitly does not promise network connection only at moment of tool execution.
