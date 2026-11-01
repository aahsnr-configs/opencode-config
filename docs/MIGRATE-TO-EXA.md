# Upgrade: retire Firecrawl and use Exa only

This package already has an Exa server named `exa`. It **removes** the old `firecrawl` entry, uses nine MCP servers rather than ten, and updates `web-researcher` to the official Exa default tools.

## Safe upgrade from the previous archive

1. Inspect the diff between your existing `~/.config/opencode/opencode.jsonc` and the new `opencode.jsonc`.
2. Run `python3 validate.py` and `bash install.sh --dry-run`.
3. After reviewing conflicts, use `bash install.sh --apply --replace` to back up and replace the current installed `opencode.jsonc`, `AGENTS.md`, agents and commands. The installer **does not delete stale commands**.
4. The previous `/firecrawl-research` file can still be discovered because an upgrade does not remove unrelated user files. Run `python3 scripts/retire_legacy_firecrawl.py` to check whether the old command exactly matches the prior release. If the dry run says it is safe, run `python3 scripts/retire_legacy_firecrawl.py --apply`. This archives rather than deletes the command. **If modified, the helper refuses to touch it**; archive it yourself after review.
5. Confirm `opencode debug config`, `opencode debug agents`, and `opencode mcp list`; the only Exa server entry should be `exa`, disabled until human connection. If using OpenChamber Desktop, check its own backend version and MCP settings.
6. For explicit Exa research, human connects `exa`, explicitly invokes `/exa-research` or `@web-researcher`, approves each individual tool call with *Allow once*, then disconnects.

## Agent permissions and authentication

Official Exa default tools: `web_search_exa`, `web_fetch_exa`. OpenCode V2 permission names have the configured server prefix: `exa_web_search_exa`, `exa_web_fetch_exa`. Optional `agent_run` and advanced tools are deliberately excluded. Exa may permit anonymous access with limits; higher limits require separate account authentication. No ChatGPT app OAuth is inherited.

**Security boundary:** `AGENTS.md` instructions and tool `ask` permissions are defense-in-depth, not an OS sandbox; check for saved persistent approvals and unexpected project-local settings. The manual activation script controls only the OpenCode backend configured by its `--url` option.

Primary docs: https://github.com/exa-labs/exa-mcp-server and https://opencode.ai/v2/docs/mcp-servers .
