> **Latest changes:** Four user-supplied specialty agents are included; Exa is the web-research MCP (no duplicate server); MCP connections are strictly manual by default. Read [EXPLICIT MCP](docs/EXPLICIT-MCP.md) before invoking any server. This package requires OpenCode V2 2.2.3+ for its global MCP policies.

# OpenCode V2 + OpenChamber — manual-on-demand MCP release

**Audit date:** 2026-11-01 (Context7-assisted documentation review)  
**OS target:** Linux (including Fedora); macOS/Windows differ for installation.  
**GUI:** OpenChamber Desktop (recommended) or OpenChamber Web/PWA.  
**Agent engine:** OpenCode **V2**, not Kilo, Paseo or legacy OpenCode V1.

## What is in this ZIP

- `opencode.jsonc` — global V2 config with conservative ordered permissions, automatic compaction, output caps, and optional MCP servers disabled.
- `AGENTS.md` — global instructions; `agents/*.md` — Chat, Work, Coder, Research, Reviewer, Digest, Compactor, Explore Scout, Git/GitHub and Web Researcher.
- `commands/*.md` — quick answers, work, code implementation, audit, research, file generation and planning.
- `skills/*/SKILL.md` — academic research, artifact production, browser research, coding QA, productivity, references, science, workflow routing.
- `docs/` — service compatibility, security, upgrading, troubleshooting and sources.
- `examples/` — optional project instructions and an **off-by-default** OpenChamber task.
- `install.sh` — dry-run installer with collision detection, backups and no model calls; `validate.py` — offline validation; `tests/` — installer smoke test.

## Why OpenChamber

OpenChamber is purpose-built for OpenCode and provides chats, projects, diffs, worktrees, Session Goals, scheduled tasks, integrations and an agent-controllable browser in the desktop surface. It is **not** your ChatGPT web account; apps installed in ChatGPT are separate from OpenChamber account connectors.

## Installation (recommended order)

1. Read `QUICKSTART.md` and `docs/SECURITY.md`.
2. Install `npm install -g @opencode/cli` if needed. Verify `opencode --version`. Official V2 entry point: https://opencode.ai/v2/docs .
3. From the unpacked folder, run `python3 validate.py`, then `bash install.sh --dry-run`. Check conflicts. To write, `bash install.sh --apply`; intentional replacement requires `--apply --replace` and creates a timestamped backup.

   For live sync from a stable repository checkout, preview `bash install.sh --link`, then run `bash install.sh --link --apply`. Existing conflicting entries require `--replace`, which moves them to a backup. Replacing an `agents`, `commands`, or `skills` directory moves the entire directory, including any personal files, out of the active configuration. Managed files and directories are linked into `${XDG_CONFIG_HOME:-$HOME/.config}/opencode`; other top-level entries remain untouched. Edits through the links change the checkout, and switching branches changes the active files immediately. Moving the checkout breaks the links. OpenCode may need restarting to reload changes. To return to copies, review and remove the links manually, then run the normal installer.
4. Run `bash doctor.sh` for the V2 CLI checks. It calls `opencode debug config`, `opencode debug agents`, and `opencode mcp list`; skill files are validated offline. Resolve any errors before making a model call.
5. Start `opencode`; connect a permitted model provider and select a model. No hard-coded model ID is included because availability and billing differ.
6. Install OpenChamber **Desktop** from https://docs.openchamber.dev/install/ (Fedora `.rpm` or an AppImage). Desktop has its own bundled OpenCode runtime; confirm it loads your global configuration and compare versions. For browser/PWA, Node.js 24.14+ and system OpenCode are required. Follow the official installer rather than a prebuilt unverified install command.
7. In OpenChamber check Settings → Agents for all ten profiles, Settings → MCP for disabled servers and Settings → Integrations for any extra catalog apps. Do not duplicate server definitions.
8. Start with the `chat` agent; use `work` for deliverables, `coder` for code changes, and `research` for peer-reviewed evidence. The `reviewer` is a subagent; `/audit-change` asks `coder` to invoke it.

## Scheduled work

Use OpenChamber's native Scheduled Tasks UI; the example in `examples/openchamber` is **not installed or enabled**. Replace its `model` placeholder and set `enabled: true` only after inspecting it. Run once manually before leaving it scheduled; the server must be running and scheduled work consumes model tokens.

## MCP/plugin portability

All nine MCP definitions **remain disabled persistently**; runtime connections are manual and temporary. Keep all servers disabled by default. Connect one named server only upon an explicit user action, and disconnect it immediately after the approved calls. See `docs/EXPLICIT-MCP.md`. Undermind requires a client ID registration/CIMD strategy; authentication may not work in the generic OpenCode OAuth flow without additional provider support. Tamarind can submit computational jobs with real cost: test catalog queries only until explicitly authorized. The GitHub server uses the documented read-only route by default. See `docs/INTEGRATIONS.md` for scope and cautions.

## Security limitations

The config is cautious, not a hardened OS sandbox. The shell, custom code and external MCP servers can bypass filename restrictions. Keep sensitive operations in containers or separate OS users; inspect provider scopes and require approvals for external writes.

## Verification and guarantees

This package passes offline JSON, YAML, V2 permission and MCP structure checks, mocked CLI discovery, install dry-run/backup, shell syntax and ZIP integrity tests. It is **not possible to guarantee zero runtime issues** without your specific OpenCode/OpenChamber versions, account access and enabled services. See `docs/TROUBLESHOOTING.md` for runtime acceptance checks.

## Final audit commands

```bash
bash doctor.sh                       # offline validation + non-model CLI checks if CLI exists
python3 tests/test_installer.py    # safe temporary-home installer tests
python3 scripts/validate_against_live_schema.py   # optional; handles HTTP 403 with cache / CLI fallback
# For browser-downloaded schema: --schema-file ~/Downloads/config.json
```

For the exact verification scope and limitations, see `docs/VERIFICATION.md`. The installer does not delete retired agent files from previous kits; see `docs/UPGRADE.md`.

## 2026-11-01 doctor.sh correction

The prior doctor used `opencode agent list` and `opencode debug skill`, which are legacy commands absent from the documented OpenCode V2 CLI. This release uses `opencode debug agents`; see `docs/V2-DIAGNOSTIC-FIX.md`.


## HTTP 403 when fetching the schema (2026-11-01 fix)

The OpenCode site may block Python requests to `https://opencode.ai/config.json` even though the configuration is fine. The revised validator tries browser-like headers, then reuses a saved schema, and only then offers a clearly labeled *partial* CLI check. It will **never** label that fallback as full JSON Schema validation. Read [docs/SCHEMA-403-FIX.md](docs/SCHEMA-403-FIX.md) for commands and a manual browser-download route.


## Explicit-only MCP quick commands

```bash
python3 scripts/mcpctl.py list
python3 scripts/mcpctl.py status
python3 scripts/mcpctl.py session exa   # human-only: opens a connection window
```

The `session` command connects Exa only after you type the exact server name in a terminal and disconnects when you press Enter. Both OpenCode and OpenChamber can use that same runtime state **only when connected to the same server**. Independently running GUI and CLI instances require separate activation. MCP tools never run automatically without a per-call approval, assuming you have no saved allow-always approvals. See `docs/EXPLICIT-MCP.md`.


## Added user agents (this release)

Four uploaded agents were migrated from Claude-style metadata to **OpenCode V2** `mode`, `model`, and ordered `permissions` rules; their original documents are preserved unmodified in `references/original-user-agents/`. See `docs/FOUR-AGENTS.md`.

| Agent | Model | Invocation | Permissions |
|---|---|---|---|
| `compactor` | `openai/gpt-6-luna` | `@compactor` / `/handoff` | Read-only handoff + safe Git inspection |
| `explore-scout` (uploaded Explore) | `openai/gpt-6-luna` | `@explore-scout` / `/scout` | Read/Glob/Grep only; no network |
| `git-gh` | `openai/gpt-6-luna` | `@git-gh` / `/git-inspect` | `git` and `gh` only; writes ask; push denied |
| `web-researcher` | `openai/gpt-6-luna` | `@web-researcher` / `/exa-research` | Manual **Exa** MCP only; per-call approval |
| `sol-advisor` | `openai/gpt-6.1-sol#high` | `@sol-advisor` | Read-only advice on difficult decisions |

**Model availability varies by OpenAI account/provider**, and the model IDs in source documentation are not a guarantee that your ChatGPT OAuth login offers them. Run `opencode models`, or `python3 scripts/model_audit.py` (requires PyYAML), then replace any unavailable `model:` field with an available OpenAI model. Selecting an OpenCode Console model is a different billing route from ChatGPT sign-in.

The `coder` agent uses `openai/gpt-6.1-terra#medium`; confirm that your provider offers the model and variant. Every subagent invocation requires prior user approval.

For project-specific context across sessions, use `/memory` to review or update a `PROJECT-MEMORY.md` file at the project root. This is a user-managed file, not automatic model memory. Review its contents before sharing or committing it; never store secrets.

See [workflow setup](docs/WORKFLOW-SETUP.md) for plugin status, compact Git inspection, and Vim editor support.

**Manual Exa activation:** All nine servers remain `disabled: true` on disk, including `exa`. Only connect Exa via the human-operated `/mcps` UI or `python3 scripts/mcpctl.py session exa`; then explicitly ask for **Exa** research and choose **Allow once** for every search/fetch call. A user request for generic web research must *not* activate Exa automatically. The previous `/firecrawl-research` command must be retired from an older installation (see `docs/MIGRATE-TO-EXA.md`).

Run `python3 tests/test_added_agents.py` and `bash doctor.sh --offline` before using the new agents.

## Firecrawl-to-Exa migration notice

This release removes the Firecrawl MCP definition and replaces the old research slash command with `/exa-research`. Because the installer intentionally leaves obsolete user files alone, review `docs/MIGRATE-TO-EXA.md` to archive the previous `/firecrawl-research` command safely.

## Latest audit and MCP-controller hardening

See [docs/CONTEXT7-AUDIT.md](docs/CONTEXT7-AUDIT.md). The MCP controller now refuses a second connection during pending authentication/initialization and rejects malformed status responses. Static checks do not guarantee runtime compatibility.

## Life-sciences research

The integration includes the complete 50-skill public OpenAI Life Science Research plugin 1.0.3 snapshot with all 161 skill files, plus recorded local correctness and output-safety adaptations. See [setup and scope](docs/LIFE-SCIENCES.md) and the [current readiness audit](docs/LIFE-SCIENCES-READINESS.md). Hosted OpenAI platform features and scientific validation remain outside this port.

## Research integrations and learning

Zotero, optional provider-confirmed SciSpace access, resumable deep research and learning workflows are documented in [RESEARCH-SETUP.md](docs/RESEARCH-SETUP.md). See [RESEARCH-AUDIT.md](docs/RESEARCH-AUDIT.md) for tested behavior and live-access limits.

## Mathematics and numerical methods

See [Math Research](docs/MATH-RESEARCH.md) for `/math-research`, `/numerical-research`, isolated CPU/CUDA environments, and the deterministic terminal installer. Installation invokes no models or AI APIs; planning and requested troubleshooting still use tokens.
