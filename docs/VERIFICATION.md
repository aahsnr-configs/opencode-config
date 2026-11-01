# Verification report and acceptance matrix

Build date: 2026-11-01. Updated after user-reported agent diagnostic failure. The tests below are reproducible from the ZIP itself.

## Tested in the generation environment

| Test | What it checks | Result |
| --- | --- | --- |
| `python3 validate.py` | JSON parsing, documented V2 config shape, permission entries, ten agents, twelve commands, eight skills, example schedule disabled, script syntax | PASS |
| `python3 tests/test_doctor.py` | Mocked V2 success, missing agent detection, V1 command failure | PASS |
| `python3 tests/test_installer.py` | Default dry-run, install, idempotent rerun, no-overwrite conflict, backup+replace | PASS |
| `bash -n install.sh doctor.sh` | Shell syntax | PASS |
| `python3 -m compileall -q ...` | Python syntax | PASS |
| `sha256sum -c SHA256SUMS` | Every non-manifest file matches its checksum | PASS |
| `unzip -t` | Compressed archive integrity | PASS |
| Extraction and retest | Both Python zipfile extraction and Unix unzip extraction; tests run using bash to avoid executable-bit portability issues | PASS |

## Not testable from this isolated environment

- Full authoritative JSON Schema validation requires a retrievable official schema (or browser-saved JSON). Use `python3 scripts/validate_against_live_schema.py --schema-file ~/Downloads/config.json` if the site rejects Python requests. A CLI fallback is only a partial result.
- OpenCode CLI startup and its exact installed version (`opencode --version`, `opencode debug agents`, `python3 validate.py`, `opencode mcp list`, `opencode debug config`).
- OpenChamber Desktop's bundled OpenCode version and whether it loads global configuration identically to your system CLI.
- Authentication to a model provider, token/cost accounting, tool permission prompts, remote MCP OAuth and tool discovery.
- Remote tool behavior or external service actions (GitHub, Undermind, TickTick, Tamarind etc.).
- Scheduled execution in your local timezone with a running OpenChamber server.

No source can guarantee zero future bugs across specific runtime versions or third-party services. This release deliberately defaults to disabled external MCP servers and disabled scheduled tasks, with explicit OpenAI model IDs only for the four newly added specialty agents. Account-specific model availability is checked separately; no model inference occurs during installation.

## Corrected V2 CLI diagnostic

The old V1 commands (`opencode agent list` and `opencode debug skill`) have been removed. The corrected CLI diagnostic uses `opencode debug agents`, checks the ten expected custom agent IDs, and validates skill files offline. The CLI itself is not installed in the build environment; mocked V2/V1 command tests verify script behavior but cannot replace a real runtime test.

## Schema-validator regression tests

`python3 tests/test_live_schema_validator.py -v` tests HTTP 403 fallback, strict mode, no-CLI behavior, cached/explicit schema, invalid configuration, stale schema rejection, and JSONC parsing using a synthetic test schema. **These do not constitute validation against the full live schema**, which is unavailable for automated download in the isolated build environment.


## Added-agents regression checks

- `python3 tests/test_added_agents.py`: validates the four uploaded-agent conversions, model assignments, and explicit-only Exa permission surface.
- `python3 scripts/model_audit.py`: optional non-inference check against the locally configured `opencode models` catalog; unavailable in the isolated builder because no OpenCode CLI is installed.
- All MCP servers, including Exa, remain disabled at startup. Model access, Exa authorization, OpenChamber runtime and actual permission dialogs remain **untested live**.

## Exa replacement regression verification (2026-11-01)

- `python3 validate.py`: PASS (9 named disabled MCP servers; one `exa`, no Firecrawl server or policy).
- `python3 -m unittest discover -s tests -v`: PASS, **27 tests** including Exa-only agent tool permissions, explicit MCP controller, schema error fallback, and installer safety.
- Clean ZIP extraction into temporary HOME: PASS (new configuration installs and offline doctor checks pass).
- Controlled migration of the prior known `/firecrawl-research` command: PASS (dry-run first, `--apply` archives the exact recognized legacy file without touching modified commands).
- SHA-256 checksum manifest and ZIP integrity: PASS after packaging.
- **Not tested live:** actual `opencode debug agents`, provider entitlement to the configured OpenAI models, Exa MCP authentication/tool calls, OpenChamber's bundled engine, or third-party network connectivity. Run local doctor and approve one low-impact Exa call before relying on the workflow.
