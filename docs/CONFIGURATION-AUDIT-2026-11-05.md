# Configuration audit — 2026-11-05

This records the earlier, limited audit. The subsequent exhaustive review and
current results are in [the complete audit](CONFIGURATION-AUDIT-COMPLETE.md).

Installed CLI: `opencode v2.2.5`. This audit covers repository configuration,
agent and command routing, installer and diagnostic tooling, workflow skills,
and research integration code. Scientific API helper review was selective;
offline suites exercised the bundled helpers. Private runtime data, credentials,
session transcripts, and provider accounts were excluded.

## Fixed findings

1. **Git output options bypassed approval.** Global and specialty-agent rules
   allowed arbitrary `git diff`, `git log`, and, in some agents, `git show`
   arguments. A Git specialist reproduced file creation through `--output`
   under `/tmp`. These broad forms now require approval. Exact compact commands
   remain allowed: `git diff --stat`, `git diff --name-only`, and
   `git log --oneline -10`. This preserves concise inspection without permitting
   arbitrary options automatically. The unattended digest must use these exact
   commands or encounter an approval gate.
2. **Credential path coverage was incomplete.** The existing config-directory
   pattern did not cover data-directory or custom-directory `auth.json` files.
   A `*auth.json` direct-read denial now applies globally and after unrestricted
   read grants in specialty agents. Tests evaluate combined global and agent
   rules for every agent. This is a precautionary filename boundary, not proof
   of the location of any real credential store.
3. **Optimized Python could report validation success with checks removed.**
   `validate.py` now refuses optimized execution before its assertions run.
   Run it without `-O`, `-OO`, or `PYTHONOPTIMIZE`.

## Settings retained

The official V2 schema accepts the configuration. Native `permissions`,
`mcp.servers`, and compaction syntax are appropriate for V2. The current automatic
compaction, 8,000-token retained context, 15% buffer, and bounded tool output have
no demonstrated performance fault. No benchmark supports changing those budgets
or the selected models. MCP server definitions and policies were not changed.

## Remaining risks and limits

- Permissions are not an OS sandbox. Search, shell commands, Git content, plugins,
  and external tools can expose data beyond direct-read filename restrictions.
  Exact command permissions also do not neutralize repository Git configuration.
- `opencode.jsonc` uses a Superpowers Git tag; `cli.json` uses the Vim plugin's
  moving `beta` channel. Full commit hashes and exact npm versions improve
  reproducibility, but no replacement revision was independently verified here.
- `docs/WORKFLOW-SETUP.md` describes automatic Supermemory cloud capture. That
  behavior was not independently reverified in installed plugin code. Review
  plugin data handling before using private conversations. Agent MCP approvals
  do not establish control over plugin hooks.
- `scripts/configure_research.py` rejects a linked config file but does not check
  linked parent directories. Its human-operated setup path merits the same
  parent-path hardening used by the installer. It was not run or changed.
- Model entitlement, plugin loading, OpenChamber behavior, live scientific
  endpoints, and actual OpenCode approval dialogs were not tested. The private
  effective runtime configuration was not ingested.

## Verification

- `/tmp/opencode-audit-venv/bin/python -m unittest discover -s tests`:
  **86 tests run, 85 passed, 1 skipped**. The skip is the optional stdio MCP
  integration test; the environment lacks the MCP SDK. Loopback mock-server
  tests required execution outside the filesystem/network sandbox.
- `/tmp/opencode-audit-venv/bin/python validate.py`: **PASS**.
- `bash doctor.sh --offline`: **PASS**.
- `bash -n install.sh doctor.sh`: **PASS**.
- `/tmp/opencode-audit-venv/bin/python scripts/validate_against_live_schema.py --cache /tmp/opencode-audit-config-schema.json --require-schema`:
  **PASS**, full validation against the downloaded official V2 schema.
- `git diff --check`: **PASS**, performed by the Git specialist.

The three new regression tests failed before the fixes and passed afterward.
Permission tests model the documented ordered wildcard rules; they do not invoke
the installed OpenCode permission engine. Existing user edits were preserved.
No commits, deployment, provider job, or live MCP activation was performed.

## Sources

Context7 resolved `/anomalyco/opencode` and retrieved V2 permission merging,
migration, and v2.2.5 compaction documentation. Exa returned six official sources.
V1 search results were distinguished from native V2 documentation:

- [V2 configuration](https://opencode.ai/v2/docs/config)
- [V2 plugins and exact-version behavior](https://opencode.ai/v2/docs/plugins)
- [V1-to-V2 migration](https://opencode.ai/v2/docs/migrate-v1/)
- [Permission source documentation](https://github.com/anomalyco/opencode/blob/dev/services/www/src/docs/content/permissions.mdx)
- [Official schema](https://opencode.ai/config.json)

Documentation branches and the live schema can advance beyond the installed
binary. Static validation and retrieved documentation are evidence of supported
shape, not a guarantee of runtime behavior or provider access.
