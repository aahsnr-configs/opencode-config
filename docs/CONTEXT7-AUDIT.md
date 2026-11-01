# Context7-assisted audit of the Exa/OpenChamber kit

**Date:** 2026-11-01. **Input:** `opencode-v2-openchamber-manual-mcp-exa-agents.zip` (71 members).  
**Scope:** Every shipped file was enumerated and checked for archive integrity, and text/program/config classes were inspected and exercised. This is not a claim that every possible runtime branch was executed.

## Evidence and limitations

- Context7 indexed sources: [OpenCode](https://context7.com/anomalyco/opencode) and [OpenChamber](https://context7.com/openchamber/openchamber), with [Context7's OpenCode integration guide](https://context7.com/docs/clients/opencode).
- The Context7 OpenCode index includes legacy V1 material. The authoritative **OpenCode V2** references used to resolve conflicts are [V2 config](https://opencode.ai/v2/docs/config), [agents](https://opencode.ai/v2/docs/agents), [MCP](https://opencode.ai/v2/docs/mcp-servers), [permissions](https://opencode.ai/v2/docs/permissions), [HTTP API](https://dev.opencode.ai/v2/docs/api), and [official published schema](https://opencode.ai/config.json).
- OpenChamber scheduling was checked against [official documentation](https://docs.openchamber.dev/scheduled-tasks/).
- **Context7 MCP was not authenticated or callable in this audit runtime.** Its public indexed documentation was accessed through web retrieval. No claim of a direct Context7 MCP lookup or actual model runtime test is made.

## Audit matrix

| Area | Files | Result | Notes |
| --- | ---: | --- | --- |
| Main configuration | 1 | Matches V2 documented shapes | `permissions` array, `mcp.servers`, `policies`, `compaction`, `tool_output`; no full downloadable-schema check in this environment |
| Agent profiles | 10 | Frontmatter and intended roles validated | 4 OpenAI model references are documented IDs, **not** verified to be available on user's account |
| Commands | 12 | Valid V2-style frontmatter | Agent references resolve locally; Exa command remains opt-in |
| Skills | 8 | Valid names/frontmatter; readable Markdown | Skill guidance is not an enforceable sandbox |
| Configuration/install scripts | 5+ | Syntax and isolated tests pass | Installer backs up conflicts; live OpenCode app not run |
| MCP controller | 1 | **Corrected** | Previous version allowed `pending` or `needs_auth` state to pass one-server-at-a-time guard; parser now fails closed |
| Documentation | All Markdown | Audited for outdated V1 commands, false Firecrawl activation, manual MCP caveats | Original user reference agents intentionally retain their pre-migration Claude/Firecrawl text |
| Archive/checksums | All | Rebuilt and CRC checked | No `__pycache__` or duplicate entries |

## Findings and corrections

1. **Fixed: MCP lifecycle race (moderate).** The manual controller previously checked only a few active status strings, excluding V2's documented `pending` and `needs_auth` states. `scripts/mcpctl.py` now uses the documented structured response, refuses unrecognized or duplicate entries, and blocks a second connection unless every other server is certainly inactive.
2. **Clarified: explicit-only MCP usage is not an absolute technical guarantee.** Disabled startup and runtime human activation are verifiable from configuration/controller. Per-call `ask` can be bypassed by a user's prior Allow always or client auto-approval mode; `AGENTS.md` is advisory. Do not use auto-approval, and remove saved approvals. OpenChamber may run a different embedded backend.
3. **Not a bug: the original agent sources mention Claude and Firecrawl.** `references/original-user-agents/` deliberately retains user uploads for provenance. The ACTIVE `web-researcher` uses Exa and the operational MCP config does not contain Firecrawl.
4. **Verification limit: models and integrations.** The model strings are syntactically valid and listed in OpenCode's catalog, but exact auth entitlements, OAuth interoperability, `/mcps`, OpenChamber Desktop integration, and live Exa MCP tool availability remain to be tested on your machine.
5. **Security caveat:** read-deny glob patterns are not a filesystem sandbox. A shell-enabled agent might access files and network outside the structured read tool; a permitted grep can expose sensitive content. Use separate OS permissions/sandboxing for high-sensitivity work.

## Reproducible checks

```bash
python3 validate.py
python3 -m unittest discover -s tests -v
bash doctor.sh --offline
bash install.sh --dry-run
# On a machine with OpenCode V2:
opencode debug config
opencode debug agents
opencode mcp list
# Full official schema, when browser-downloaded:
python3 scripts/validate_against_live_schema.py --schema-file ~/Downloads/config.json --require-schema
```

**Testing classification:** Static validation and mocked/isolated integration tests pass; real OpenCode V2 service, model inference, authenticated Context7 or Exa MCP server execution, and OpenChamber GUI were not exercised.
