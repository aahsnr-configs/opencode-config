> **MCP safety:** No server connects automatically. To activate one deliberately use the manual `/mcps` UI, OpenChamber Settings → MCP, or the included `mcpctl.py` runtime controller. See `docs/EXPLICIT-MCP.md`.

# Quick start — OpenCode V2 + OpenChamber

```bash
# 1. Install OpenCode V2 on Linux (only if needed)
npm install -g @opencode/cli
opencode --version

# 2. Extract this ZIP. In the extracted directory:
python3 validate.py
bash install.sh --dry-run
bash install.sh --apply

# 3. First inspect the system without any model calls
bash doctor.sh                         # OpenCode V2 commands + agent discovery
opencode debug agents              # manual confirmation
opencode debug config              # configuration SOURCES, not merged JSON

# 4. Start the CLI to connect a model provider
opencode
```

In the CLI, use `/connect` and the model selector as documented. ChatGPT sign-in may offer model use for eligible plans, but never imports plugin access.

**Recommended UI:** Install OpenChamber Desktop from https://docs.openchamber.dev/install/ . Linux RPM/AppImage builds are provided; its bundled OpenCode binary may differ from the separate CLI version. Confirm backend compatibility and use OpenChamber Settings → Agents/MCP/Integrations to inspect connections.

**Browser UI alternative:** Requires Node.js 24.14+. Follow the official OpenChamber install page, then run with a UI password from an environment variable (not a literal argument). Do not expose a server publicly without hardening.

**MCP use (explicit only):** Keep `disabled: true` for all servers. Use `/mcps` in OpenCode or Settings → MCP in OpenChamber to connect a specifically named server, or run `python3 scripts/mcpctl.py session consensus` against a known local OpenCode backend. Use **Allow once** for each individual tool call, then disconnect. Do not activate servers simply because a task sounds relevant. Full walkthrough: `docs/EXPLICIT-MCP.md`.

**Schedules:** Use OpenChamber Scheduled Tasks, not an always-on CLI command. Copy `examples/openchamber/repo-digest.loop.md` into a specific repository's `.agents/loops/`, replace the model placeholder, manually enable, and test **Run now**. The OpenChamber server must remain running.

To run local sanity checks after installing the CLI: `bash doctor.sh`. Use `bash script.sh` instead of `./script.sh` when your archive extractor does not preserve Unix executable bits. For full online JSON Schema verification (optional), install Python package `jsonschema`, then run `python3 scripts/validate_against_live_schema.py`.

If `bash doctor.sh` reports a CLI error, run `bash doctor.sh --details` locally for more information. The output may include sensitive configuration; redact before sharing. See `docs/V2-DIAGNOSTIC-FIX.md`.


**If schema verification reports HTTP 403:** the current script handles this without falsely reporting a configuration error. For full validation, open `https://opencode.ai/config.json` in your browser, save its JSON as `~/Downloads/config.json`, and run `python3 scripts/validate_against_live_schema.py --schema-file ~/Downloads/config.json`. See `docs/SCHEMA-403-FIX.md`.


## Four added agents

Run `opencode models` and `python3 scripts/model_audit.py` (requires PyYAML) to confirm the OpenAI models are actually available. Then: `@compactor`, `@explore-scout`, `@git-gh`, and—only after the human explicitly connects Exa and requests Exa by name—`@web-researcher`. Matching slash commands: `/handoff`, `/scout`, `/git-inspect`, `/exa-research`. See `docs/FOUR-AGENTS.md`.

If upgrading from the Firecrawl package, read `docs/MIGRATE-TO-EXA.md` to retire the obsolete `/firecrawl-research` command after installing the new `/exa-research`.

**Audit:** See `docs/CONTEXT7-AUDIT.md`. Avoid client auto-approval or saved Allow-always permissions when using the manual-only MCP workflow.
