# Four new OpenCode V2 specialty agents — migration and usage

Source files: `compactor.md`, `Explore.md`, `git-gh.md`, `web-researcher.md`, copied unchanged into `references/original-user-agents/`. The files in `agents/` are corrected OpenCode **V2** definitions.

## Model choices and compatibility

- `compactor`: `openai/gpt-6.1-sol#high`, favoring accurate high-effort handoff reconstruction. It is not OpenCode's built-in `compaction` agent.
- `explore-scout`, `git-gh`, and `web-researcher`: `openai/gpt-6-luna`, an economical fast model suited to focused tasks. This approximates the uploaded Haiku choices, not an accuracy or speed benchmark.
- `openai/...` means OpenAI provider credentials, such as an eligible ChatGPT subscription sign-in. It is **not** the `opencode/...` pay-as-you-go provider; those require independent provider connection and possible charges.
- Before first use: `opencode models` and `python3 scripts/model_audit.py`. If an ID is unavailable to your connection, manually edit each agent's `model:` to a working OpenAI model in the catalog. Optional `#high` variant requires separate verification; if unsupported remove `#high`.
- The uploaded `tools:`, `effort:`, and `omitClaudeMd:` fields are Claude-specific and are intentionally removed. In V2, per-agent `permissions:` with `action/resource/effect` and `model: provider/model[#variant]` is authoritative.

## Invocation examples

- `@compactor Summarize the current task from the following transcript/file paths and git status ...`
- `/handoff We are fixing a packaging failure; review these files and produce a 400-word handoff...`
- `@explore-scout Find the Python installer entry points and tests; return file:line ranges.`
- `/scout Find every codepath involved in Fedora spec handling.`
- `@git-gh Inspect the current branch, status, and diff. Do not commit or push.`
- `/git-inspect Check the current PR and CI statuses using gh only.`
- `/exa-research Search Exa for the latest OpenCode V2 agent documentation and cite the official references.`

## Explicit Exa MCP, without auto-connect

Exa is already configured as the `exa` server using the official `https://mcp.exa.ai/mcp` endpoint. **Do not add a duplicate.** Its default MCP tools are `web_search_exa` and `web_fetch_exa`; the OpenCode V2 permission action names are `exa_web_search_exa` and `exa_web_fetch_exa`. Only these two actions are available to this web-researcher agent, and both require per-call approval.

1. The *human* manually connects Exa through `/mcps`, OpenChamber Settings → MCP, or `python3 scripts/mcpctl.py session exa` on the correct backend.
2. The *human* explicitly requests `@web-researcher` or `/exa-research` and names Exa in the request. Generic research does not authorize this agent or activate Exa.
3. Approve each Exa search/fetch with **Allow once**. Never approve permanently.
4. Human disconnects Exa after finishing. Do not run this workflow in scheduled/background tasks.

Exa supports limited anonymous usage and separate OAuth/API-key authentication for expanded access. Authentication is not inherited from ChatGPT. Exa's optional `agent_run` and advanced search capabilities are excluded from this agent. See https://github.com/exa-labs/exa-mcp-server and https://exa.ai/mcp .

The archived original uploaded web-researcher agent is preserved *unchanged* in `references/original-user-agents/web-researcher.md` as a source document. It is NOT an installed agent and its Firecrawl requirements do not apply to the converted agent.

## Security adjustments made during migration

- The Git/gh agent has a shell-only Git and GitHub CLI allowlist with approval before mutable operations; global Git push denial remains enforced.
- The Explore scout denies `shell`, `edit`, `execute` and all network/MCP tools. It does not shadow V2's built-in lowercase `explore`.
- Compactor only performs read-only Git commands and native read/glob/grep, never `cat` through shell (which could expose secret files); it cannot read a caller's unavailable conversation.
- Web Researcher is **not proactively invoked**, despite the uploaded source description. That change follows your later explicit-only MCP instruction.

## Documentation reviewed

- https://opencode.ai/v2/docs/agents
- https://opencode.ai/v2/docs/models
- https://opencode.ai/v2/docs/providers
- https://opencode.ai/v2/docs/permissions
- https://opencode.ai/v2/docs/mcp-servers
- https://opencode.ai/v2/docs/compaction
- https://github.com/exa-labs/exa-mcp-server
