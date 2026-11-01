> Updated: Never turn MCP connections on globally as part of normal startup. Use `docs/EXPLICIT-MCP.md` for explicit runtime connection and individual call approvals.

# Integrations and plugin portability matrix

The endpoints below have been checked against published documentation as of 2026-11-01, **not against your account or from inside a running OpenCode instance**. All are disabled in the shipped `opencode.jsonc`.

| Provider | Included configuration | Caveats |
| --- | --- | --- |
| Context7 | `context7` | Docs retrieval; service limits may apply. |
| Exa | `exa` | Search and page fetch; anonymous limited use, account or key for more. |
| Consensus | `consensus` | Academic evidence; OAuth or relevant plan may be required. |
| alphaXiv | `alphaxiv` | OAuth; search and library changes depend on account. |
| Undermind | `undermind` | **Special case:** no dynamic client registration; may require pre-registered client or CIMD-compatible OAuth client. Do not assume generic OpenCode OAuth succeeds. |
| Tamarind Bio | `tamarind` | Paid/scientific compute and jobs; `protocol: auto` supports protocol negotiation; test catalog only before submitting. |
| GitHub | `github` | Uses GitHub's `/mcp/readonly` endpoint. Still confirm tool scopes and authorization. OpenChamber has a separate Git host integration. |
| TickTick | `ticktick` | Can create/change/delete tasks. Review scopes and actions before use. |
| Playwright | `playwright` | Local isolated headless browser. Downloads npm package at first use; requires Node/npm and compatible browser installation. |

Not preconfigured with guessed URLs: SciSpace, Rowan MCP, Zotero Desktop, Google Workspace, or the dozens of public life-sciences APIs. Use OpenChamber Settings → Integrations or add a provider's current verified endpoint. Rowan can be used with its official Python SDK; Zotero via its local API/CLI after separate installation. Life-sciences REST/GraphQL APIs are best exposed through focused Python scripts or skills, not as unverified MCP endpoints. Google's Workspace MCP is developer preview with eligibility requirements and requires its own OAuth. Do not put access tokens in JSON config or repository files.

## Enable one service

1. **Do not permanently change `disabled` to `false`.** For an explicitly named server, use `/mcps` in OpenCode, OpenChamber Settings → MCP, or the manual `mcpctl.py session NAME` against your selected local backend; disconnect when done. See `docs/EXPLICIT-MCP.md`.
2. `opencode mcp list` checks connection status. For eligible OAuth providers use `opencode mcp auth NAME` or OpenCode's `/mcps` UI.
3. Make an *explicitly read-only*, small test request and confirm the result. Test account writes separately with confirmation.
4. If authentication fails, use `opencode mcp debug NAME`; inspect provider docs, not generic token workarounds.
5. Re-disable services when not in use to reduce token overhead.

## Known equivalents not imported automatically

- Installed ChatGPT plugins: Exa, Consensus, alphaXiv, Undermind, SciSpace, GitHub, TickTick, Tamarind Bio, Rowan and research skills were visible during planning. This is **not** a guaranteed full account inventory.
- ChatGPT Automations → OpenChamber Scheduled Tasks or an optional Linux systemd user timer.
- ChatGPT Chat → OpenChamber Chats + `chat` agent.
- ChatGPT Work → OpenChamber Session Goals + `work` agent.
- Codex-like development → OpenChamber Projects/Worktrees + `coder`/`reviewer` agents.
- Personal memory → explicit user-managed knowledge files, not a shared ChatGPT memory database.
- ChatGPT templates → local skill instructions and legally accessible reference templates; the ZIP does not contain the proprietary template artifacts.

## Additional recommended OpenChamber catalog integrations

Prioritize Context7, Exa, Playwright, GitHub and Zotero. Add Gmail, Google Drive, Google Calendar only when required and apply write approval; Notion, Linear, Figma, Supabase, Sentry, Slack are task-dependent. OpenChamber's catalog is the safer discovery mechanism for services that change endpoints or OAuth setup.

## Primary official references

- https://opencode.ai/v2/docs/mcp-servers
- https://docs.openchamber.dev/integrations/
- https://exa.ai/mcp
- https://github.com/Consensus-NLP/consensus-mcp
- https://www.alphaxiv.org/docs/mcp
- https://www.undermind.ai/mcp/reference
- https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/customize-copilot/extend-copilot-with-tools-and-context/set-up-the-github-mcp-server
- https://help.ticktick.com/articles/7438129581631995904
- https://app.tamarind.bio/api-docs/mcp-server


## Exa (manual research only)

The configured `exa` remote server points to `https://mcp.exa.ai/mcp` with `disabled: true` and `codemode: false`. Exa's *default* hosted MCP tools are `web_search_exa` and `web_fetch_exa` (normalized OpenCode permission names `exa_web_search_exa` and `exa_web_fetch_exa`). The restricted `web-researcher` subagent can use only these two tools after a human has manually connected Exa and explicitly asked for Exa research. All calls require per-call **Allow once** approvals. No automatic task-driven connection or provider substitution. See `docs/FOUR-AGENTS.md`.
