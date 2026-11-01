# Zotero, SciSpace, deep research and learning

This extension is installed once for the OpenCode backend used by OpenChamber.
It adds executable integration helpers, two agents and eight commands. It does
not transfer ChatGPT accounts, OAuth, memory, subscriptions or proprietary UI.

## Install

From this checkout, review and install the configuration with the existing
`./install.sh --dry-run`, then `./install.sh --apply`. Existing conflicts require
review before `--apply --replace`; that option makes backups.

The Python package is a separate, explicit installation. For example:

```sh
python3 -m venv ~/.local/share/opencode-research-venv
~/.local/share/opencode-research-venv/bin/python -m pip install './integrations/research-tools[mcp]'
~/.local/share/opencode-research-venv/bin/opencode-research-tools doctor
```

Set the backend PATH to include the absolute `bin` path of that environment.
For OpenChamber-managed OpenCode use Settings → General → Environment variables;
then restart its backend. Enter the complete PATH value; do not assume shell
expressions or `~` are expanded in the UI. A separately launched OpenCode server
must receive its own environment. Project terminal environments alone do not
configure the shared OpenCode process.

The installed `zotero` MCP command is `opencode-research-tools serve-zotero`.
It is disabled by default and starts no HTTP listener. Only the human may connect
it through OpenCode/OpenChamber or the manual controller. Each tool call still
needs current-user provider/operation authorization and Allow once. Do not use
an approved shell call to circumvent denied MCP permissions. The existing
controller permits only one active server at a time; multi-provider work is
sequential unless that policy is separately changed.

The optional helpers use the official MCP Python SDK pinned at 1.30.0. Core CLI
clients and local state use Python's standard library. Python 3.10+ is required.
Test extras install jsonschema, PyYAML and json5. The separately bundled upstream
life-science scripts retain their own requests/matplotlib dependencies.

## Zotero

Run Zotero Desktop on the same computer as the OpenCode backend and enable
Settings → Advanced → Allow other applications on this computer to communicate
with Zotero. The bridge uses only `http://127.0.0.1:23119/api/` in local mode.
Cloud/server localhost does not refer to a laptop running Zotero. The integration
does not expose or forward Zotero's port, edit its preferences or read SQLite.

Commands include `/zotero`, `/deep-research` and `/explain-paper`. Supported tools
cover bounded search, items, collections, collection items, tags, children,
indexed fulltext, selected bibliography export, optional Better BibTeX lookups,
and reviewed native-JSON imports. Fulltext is Zotero's indexed text, not a PDF
viewer with guaranteed page citations. Collection/tag mutation and attachment
uploads are not exposed. File exports return content; saving it is a distinct
approved action. Existing bibliography files are never automatically replaced.

Optional Better BibTeX supplies real citekeys and selected Better BibTeX exports.
Keep updated collection exports can be configured by the human in Zotero. The
bridge does not create auto-exports or regenerate citation keys.

For explicitly selected Web API mode, set `ZOTERO_MODE=web`, `ZOTERO_USER_ID` and
`ZOTERO_API_KEY` in backend environment settings. Use a dedicated scoped key;
reads and imports use only the user's library. Group-library mode is not yet
implemented. Local mode needs no read key. Local write authorization is detected
through the Zotero server-ID capability and requires Zotero 10+; older clients
use manual import or explicitly configured Web mode.

Import workflow: review up to 50 native Zotero item objects; generate
`import_preview`; approve the exact objects and digest; invoke `import_items`.
The client checks exact DOI duplicates across bounded search pages, rejects
matches and shows Zotero's authorization dialog for supported local writes.
Entries without a DOI require manual title review. It does not claim complete
fuzzy duplicate detection. Inspect per-item API failures and the Zotero UI after
an import. No automatic retry is made after an ambiguous network failure.

## SciSpace

No endpoint is guessed. Published connector guidance says MCP access is through
ChatGPT/Claude directories, and the REST documentation index was readable but
its detailed request schemas were not retrievable during implementation. Direct
OpenCode authentication remains unverified and account-dependent.

If SciSpace supplies an official HTTPS MCP endpoint for your account/client,
run the following human-only setup utility with that actual URL:

```sh
python3 scripts/configure_research.py --config ~/.config/opencode/opencode.jsonc \
  --scispace-url "$SCISPACE_PROVIDER_CONFIRMED_URL" --provider-confirmed
```

This is a dry-run. Review before adding `--apply`. The utility accepts only
scispace.com HTTPS hosts, rejects embedded credentials/query strings, creates a
backup and atomically writes the configuration with the server still disabled.
JSONC comments are normalized away on apply (json5 is needed to parse JSONC).
It does not authenticate, test the endpoint or grant provider access. The human
then authenticates/connects in OpenCode/OpenChamber; read actual tool schemas
before use. `mcpctl.py` recognizes SciSpace only once it is configured.

`/scispace` also supports inspection of user-exported CSV or JSON tables through
`opencode-research-tools scispace-import`. It preserves analytical columns and
labels results as imported/unverified. This path is not a live SciSpace search.
There is no SciSpace REST adapter or imitation of its native interactive widget.
Do not call direct SciSpace access complete until your account passes live tests.

## Research workflows

`/deep-research` plans retrieval, records evidence, screens sources, verifies
citations and builds a synthesis. `/research-resume` reads a saved run before
continuing. `/research-status` inspects local state and does not authorize provider
polling. `/life-science` now selects the execution-capable deep-research agent;
the original research agent remains read-only for synthesis.

The new agent asks before shell execution and limits edit-tool outputs to
`research/**` and `learning/**`. Shell matching is an approval gate, not an OS
sandbox. Instructions prohibit shell-based workarounds. Git pushes and destructive
rm commands remain denied by explicit agent rules. No subagents are enabled.

The shared Exa endpoint explicitly exposes search, fetch and authenticated
agent_run. The restricted web-researcher agent still has only search and fetch.
Deep research can use agent_run after specific spending approval. Each poll
requires Allow once, and a running provider ID is reused rather than resubmitted.
External jobs may continue after the client disconnects. There is no automatic
polling, scheduled MCP task, hard dollar cap or assumed cancellation API.

Optional OpenAI API research uses the documented Responses API with built-in
web_search and background execution. Set OPENAI_API_KEY and
OPENAI_RESEARCH_MODEL explicitly, verify model/tool compatibility, review token
limits and approve spending. It uses no remote MCP and does not alter MCP approval
policy. Responses are returned intact, including annotations and usage. Retain
response IDs; requests are never automatically retried. Poll manually during an
approved task. Token limits are not complete cost limits. Local run cancellation
does not cancel the remote response. Check OpenAI project retention settings;
background retrieval may expire. This optional adapter has no live paid-job test.

## Learning

`/learn` teaches in small steps; `/quiz` asks one question at a time and waits;
`/explain-paper` covers methods, figures and limitations only to the extent the
source is actually available. The learn agent adapts hints and depth to responses.
Open-ended feedback is qualitative, not a calibrated mastery score. Exact-text
checks are used only for supplied objective answer keys.

Local progress is opt-in. Records include selected attempts and feedback, not
implicit ChatGPT memory. No reminders, schedules or remote sync are created.

## Durable records and exports

The CLI stores research and learning runs in private SQLite state under
`$XDG_STATE_HOME/opencode-research`, default `~/.local/state/opencode-research`.
Set OPENCODE_RESEARCH_STATE_DIR to choose another directory. Database writes use
transactions and expected revisions; stale writes fail instead of overwriting.
Do not put credentials or private material into exported research records.

Run `opencode-research-tools run` with a JSON object on stdin. Supported operations
are create, list, get, update and export. Full examples live in the installed
skills/deep-research/references/workflow.md and skills/learn/references/progress.md.
Exports return a JSON record, Markdown and evidence CSV as data. Zotero exports
supply real bibliography content. Save outputs explicitly after review. Generated
research/learning directories, SQLite files and Python build products are ignored
by Git. The record schema is schemas/research-run.schema.json.

## Troubleshooting and acceptance

- Missing CLI: fix the OpenCode backend PATH, not just the terminal PATH.
- Missing mcp SDK: install the `[mcp]` extra in the same interpreter environment.
- Zotero unreachable: check host topology, running desktop and local API setting.
- Zotero 403/401: check local preference versus local-write or Web API credentials.
- SciSpace unavailable: request supported provider access; exports remain usable.
- Provider timeout: report it; preserve any job ID; do not start a duplicate job.
- Revision conflict: reload state before updating; never silently overwrite it.
- Citation lacking full text: label the evidence limitation; do not invent pages.

See RESEARCH-AUDIT.md for actual validation results and remaining live-test gates.
