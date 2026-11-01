# Release notes: Exa replaces Firecrawl

- Reuses the existing `exa` MCP server, rather than duplicating it. Removes the `firecrawl` server, permission rule, policy and manual controller allowlist entry. Nine MCP servers remain, all `disabled: true` and `codemode: false`.
- Converts `web-researcher` to Exa **default** tools only: `exa_web_search_exa` and `exa_web_fetch_exa`, both `ask`, after an explicit human request and manual server connection.
- Replaces `/firecrawl-research` with `/exa-research`. The old slash command may still exist on machines with earlier kits; the migration helper only archives the exact known old version.
- Updates full documentation, tests and checksums. The four uploaded original agent documents remain unchanged under `references/original-user-agents/` and are **not installed**.
- Offline tests are executed in a temporary environment. Live provider/model authentication, MCP OAuth, OpenCode runtime and OpenChamber UI are NOT verified by these tests.

Sources: https://github.com/exa-labs/exa-mcp-server ; https://opencode.ai/v2/docs/mcp-servers .
