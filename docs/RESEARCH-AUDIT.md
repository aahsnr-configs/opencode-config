# Research integration audit

Audit date: 2026-11-01. Starting branch: life-sciences-foundation at
6a4f14f80aeaf7d6e037adddbfbb3744f5a62ff5. Scope: Zotero, supported SciSpace
connection setup/export inspection, deep research, learning and affected tooling.

## Implemented and checked

| Area | Evidence |
| --- | --- |
| Package | Standard-library core; official MCP Python SDK 1.30.0 optional dependency; editable install, wheel build, standalone wheel invocation and dependency check succeeded |
| Configuration | FULL validation against the live https://opencode.ai/config.json V2 schema passed; offline inventory/metadata validation passed |
| Tests | All 57 repository unittest cases passed in the isolated Python 3.12 environment with test dependencies installed; installer and doctor script checks also passed; a separate isolated-XDG install matched every agent, command and skill file byte for byte |
| Zotero protocol | Real stdio MCP initialization, tool discovery, preview invocation and invalid-key rejection passed using the installed MCP SDK |
| Zotero client | Controlled responses test bounded read URLs, local authorization headers, reviewed-digest gate, DOI duplicate rejection, older-client write refusal and restricted Better BibTeX methods |
| Research state | Real SQLite persistence, revision conflicts, valid/invalid transitions, evidence deduplication, report reference integrity, provider job-ID reuse and exports tested |
| Learning state | Objective exact-text grading and qualitative-only open-ended feedback tested |
| SciSpace | CSV/JSON export preservation and human-confirmed endpoint setup dry-run/apply with backup tested; no guessed remote URL or REST payload shipped |
| Optional OpenAI | Controlled tests verify explicit spending/configuration gates, single submission, full response/citation preservation and built-in web_search request shape |
| HTTP | Real loopback redirect test confirms credentials are not forwarded to a redirected request; provider requests have bounded size, timeouts and no automatic retries |
| Permissions | Ordered-rule tests verify approval for execution, edit restrictions, push denial, subagent denial and disabled server defaults |
| Upstream skills | All 161 pinned upstream file hashes remain verified by the existing integrity tests |
| Git | Diff whitespace check passed; generated runtime/build state excluded from tracked content |

The stdout messages about manual connections in the unit suite come from local
mock servers. They are not actual provider-account connections.

## Baseline defects corrected

- Replaced hard-coded inventory counts with an explicit agents/commands/skills/server manifest.
- Updated exact Exa and MCP inventory tests for the intentional authenticated agent_run exposure and disabled Zotero server.
- Corrected a legacy migration test that asserted an archived upload existed even though it is absent from the starting branch. The replacement checks the actual safety behavior: refusing an unknown command preserves its bytes and creates no archive. Documentation no longer claims that artifact is preserved.
- Installed declared test dependencies for validation. The five earlier schema-test failures caused by missing jsonschema no longer occur in the test environment. Dependencies are now declared in the package test extra and CI.
- `/life-science` now selects deep-research, which can request approval to execute scientific helpers; the original research agent remains read-only.

## Live-test and scope limits

No Zotero Desktop instance or user library was available in this environment.
Zotero search/export/import API behavior was tested with controlled responses,
not a real user library. Web mode, Better BibTeX and Zotero 10 authorization need
live acceptance on the user's backend. Group libraries, collection mutations,
attachment uploads, PDF viewing and fuzzy duplicate matching are not implemented.

SciSpace's official connector guide says access is limited to ChatGPT/Claude
connector directories. Its API documentation index was readable through Exa,
but detailed request-schema pages could not be fetched and direct access returned
HTTP 503. Therefore no unverified REST adapter or remote URL was fabricated.
The human-run configurator enables a future provider-confirmed MCP endpoint while
leaving it disabled; successful authentication/tool execution remains a provider
and account acceptance gate. Export inspection is usable without that gate, but
is not a live search. This is not a claim of completed direct SciSpace access.

No paid Exa Agent or OpenAI API job was launched. Their live account permissions,
quotas, model compatibility, costs and job cancellation are unverified. The optional
OpenAI adapter is a Responses API web-research transport, not a promise of ChatGPT
Deep Research product parity. It preserves full API output rather than asserting
that model-generated claims or citations are valid. It provides manual start and
retrieve only, no cancellation API or unattended polling.

No OpenCode or OpenChamber executable was available. Configuration is schema-valid,
but interactive tool permission prompts, command discovery, OAuth and model-driven
tutoring behavior still require actual-client acceptance. The tutoring instructions
implement documented learning behaviors; they do not reproduce proprietary UI,
account memory, voice or a calibrated learning assessment.

Shell and MCP permissions are approval controls, not OS isolation. Local SQLite
state and selected outputs are explicit user data, separate from the source repo.
A local cancelled run does not cancel a provider job. Output-token limits do not
constitute a provider-enforced dollar cap. No scientific benchmark was run.

## Verification sources

Exa was used for source discovery and page retrieval; Context7 was used for
OpenCode V2 permissions/MCP configuration and the official MCP SDK 1.30.0 tool
registration API. Sources accessed on the audit date:

- https://www.zotero.org/support/dev/web_api/v3/local_api
- https://www.zotero.org/support/dev/web_api/v3/basics
- https://retorque.re/zotero-better-bibtex/exporting/json-rpc/
- https://retorque.re/zotero-better-bibtex/exporting/auto/
- https://app.notion.com/p/SciSpace-MCP-35dd9e352ef580d2b482c7cc88842d03
- https://docs.api.scispace.com
- https://exa.ai/docs/get-started/exa-mcp
- https://developers.openai.com/api/docs/guides/tools-web-search
- https://developers.openai.com/api/docs/guides/background
- https://help.openai.com/en/articles/11780217-using-study-mode-in-chatgpt
- https://opencode.ai/v2/docs/mcp-servers
- https://opencode.ai/v2/docs/agents
- https://opencode.ai/v2/docs/permissions
- https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0
- https://docs.openchamber.dev/environment/
- https://docs.openchamber.dev/skills/
- https://docs.openchamber.dev/repository-config/

These document checks establish an implementation basis, not successful account
access. See RESEARCH-SETUP.md for installation, environment and acceptance steps.
