# Iteration archive

This archive combines historical audit, fix, release, and verification records. Each section preserves its source document. Findings describe the version or iteration named in that record and may differ from current guidance. The configuration coverage data remains in [CONFIGURATION-AUDIT-COVERAGE.json](CONFIGURATION-AUDIT-COVERAGE.json).

## Contents

- [CONFIGURATION-AUDIT-2026-11-05.md](#configuration-audit-2026-11-05)
- [CONFIGURATION-AUDIT-COMPLETE.md](#configuration-audit-complete)
- [CONTEXT7-AUDIT.md](#context7-audit)
- [LIFE-SCIENCES-AUDIT.md](#life-sciences-audit)
- [LIFE-SCIENCES-READINESS.md](#life-sciences-readiness)
- [RESEARCH-AUDIT.md](#research-audit)
- [RELEASE-NOTES-EXA.md](#release-notes-exa)
- [RELEASE-NOTES-v2.md](#release-notes-v2)
- [RELEASE-NOTES-v3.md](#release-notes-v3)
- [RELEASE-NOTES-v4.md](#release-notes-v4)
- [SCHEMA-403-FIX.md](#schema-403-fix)
- [V2-DIAGNOSTIC-FIX.md](#v2-diagnostic-fix)
- [VERIFICATION.md](#verification)
- [VERIFICATION-EXPLICIT.md](#verification-explicit)

<a id="configuration-audit-2026-11-05"></a>

## CONFIGURATION-AUDIT-2026-11-05.md

# Configuration audit — 2026-11-05

This records the earlier, limited audit. The subsequent exhaustive review and
current results are in [the complete audit](ITERATION-ARCHIVE.md#configuration-audit-complete).

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

---

<a id="configuration-audit-complete"></a>

## CONFIGURATION-AUDIT-COMPLETE.md

# Complete configuration audit — 2026-11-05

All **262 requested files present at the start of this audit were content-reviewed**.
This supersedes the earlier limited audit. Confirmed defects were fixed, and the
final offline suite ran **147 tests: 146 passed, one optional test skipped**.

## Coverage

| Scope | Reviewed files |
| --- | ---: |
| `agents/` | 13 |
| `commands/` | 22 |
| `docs/` | 24 |
| `examples/` | 3 |
| `integrations/` | 11 |
| `life-sciences/` | 5 |
| `schemas/` | 2 |
| `scripts/` | 5 |
| `skills/` | 176 |
| `opencode.jsonc` | 1 |
| **Total** | **262** |

[The coverage manifest](CONFIGURATION-AUDIT-COVERAGE.json) records every original
path, its final SHA-256, reviewer, and whether it changed after initial inspection.
The two new audit artifacts are listed separately to avoid a self-referential
checksum. Generated bytecode, caches, build outputs and installed dependencies
were excluded. No credentials, private runtime research/learning records, or
session transcripts were ingested.

Review covered all text and code, not just file inventory. Exact duplicate content
was reviewed once and mapped to every copy: 30 generic REST clients and five
variant resolvers. Skill files were also checked by exact source segments where
whole-file contents differed. Focused reviewers checked the resulting fixes.

## Applied fixes

1. **Command routing:** `/memory` now selects `work`, whose edit permission asks
   for approval. The previous default `chat` agent denied all edits.
2. **Credential-safe failures:** REST and specialized scientific clients no
   longer return raw Requests exception text containing URLs, query credentials,
   or invalid header values. Requests errors are handled before `ValueError`,
   since some Requests exceptions inherit both classes.
3. **Network boundaries:** generic REST clients reject foreign-origin absolute
   paths and credential-bearing base URLs. Scientific requests refuse automatic
   redirects, close responses, and stream at most 5 MiB before parsing. Query
   narrower resources or pages when a limit is reached; the limit is not a
   total-duration or OS memory guarantee.
4. **Malformed responses:** excessive JSON nesting and invalid object/row shapes
   return structured errors. Boolean values no longer pass as integer limits;
   numeric timeout checks reject nonfinite values where applicable.
5. **BLAST safety:** RID values cannot become traversal filenames. ZIP members,
   aggregate uncompressed bytes and manifest size are bounded; duplicate
   manifest references are rejected before repeated payload expansion.
6. **Output protection:** raw savers and mapper outputs reject linked parents.
   Mapping JSON and summaries use exclusive creation; figures require a new
   directory. Existing outputs are rejected before mapper retrieval begins.
7. **Setup and local state:** state access, human setup and legacy-command
   archival reject linked/dangling/non-directory ancestors. Checks operate on
   lexical paths before resolution. Intentional directory links require callers
   to supply canonical paths. Multiple file writes are not an atomic transaction,
   and these preflight checks do not defeat concurrent path replacement.
8. **JSONC parsing:** the manual controller's config parser accepts comments and
   trailing commas through optional `json5`, with a clear error when unavailable.
   It was tested as a parser against synthetic files; no real MCP activation was
   performed.
9. **GTEx pagination:** totals use server metadata when available. Partial pages
   are flagged, and unknown totals are `null` rather than a falsely complete
   page length. This does not automatically issue extra requests.
10. **NCBI XML:** bounded attributes survive compaction, preserving record IDs
    and PMC archive link formats/URLs.
11. **Allele correctness:** the mapper rejects multiallelic or conflicting
    placements instead of choosing the last ALT or first position. Ambiguous
    assemblies remain unresolved with explicit warnings and degraded status.
12. **Evidence attribution:** ordinary RefSNP gene membership no longer becomes
    ClinVar support. Clinical evidence is `not_assessed`. Colocalisation without
    verified gene attribution remains locus context and contributes zero to
    gene scores. Plot contributions use the same coding component as scoring.
13. **Request reuse:** 46 source skills now reuse saved, timestamped evidence
    rather than repeating requests solely because a conversation is long. BLAST
    guidance also preserves RID reuse and its minimum polling intervals.
14. **Installation and documentation:** copy installs omit Python/test caches.
    Current docs correct server/agent counts and model-selection claims. Dated
    reports retain historical results with corrections where needed.

The upstream lock still preserves all **161 original provenance records**.
The adaptation ledger records exact installed hashes and reasons for **107
adapted files**, including scientific instructions and bundled test fixtures.
No integrity check was removed or relaxed. The mapper's old multiallelic success
fixture became a biallelic success case plus an explicit ambiguity rejection test.

## Verification

- `/tmp/opencode-audit-venv/bin/python -m unittest discover -s tests`:
  **147 run, 146 passed, 1 skipped**. The skip is the optional stdio integration
  test requiring the MCP SDK. Loopback mock servers required execution outside
  the sandbox. MCP-related test output refers to mocks, not live providers.
- `bash doctor.sh --offline`: **PASS**; includes `validate.py` metadata checks.
- `bash -n install.sh doctor.sh`: **PASS**.
- AST parsing and JSON parsing across all matching covered sources: **PASS**.
- `/tmp/opencode-audit-venv/bin/python scripts/validate_against_live_schema.py --cache /tmp/opencode-audit-config-schema.json --require-schema`:
  **PASS**, full validation against the downloaded official V2 schema.
- All upstream/adapted provenance checks and installed helper suites: **PASS**.
- `git diff --check`: **PASS**, performed by the Git specialist.

The 61 new regressions cover the fixes above with synthetic responses and
temporary files. An early output-path test inadvertently entered a live lookup;
it was interrupted and replaced with a failing retrieval mock. Final tests do
not require scientific provider access. Initial test failures due to stale
adaptation hashes were resolved by recording the actual reviewed changes, while
retaining the original hashes.

## Retained settings and remaining limits

Native V2 configuration, bounded tool output, 8,000 retained compaction tokens
and a 15% buffer remain appropriate in shape for installed `opencode v2.2.5`.
No benchmark justifies changing those budgets or the selected models. MCP server
definitions and policies were not changed.

- Filename permissions and path preflights are not an OS sandbox. Git configuration,
  plugins and approved external tools remain separate execution/data boundaries.
- Superpowers uses a Git tag, and the CLI Vim plugin uses `beta`. Replacing them
  with exact verified revisions is a reproducibility option; no revision was
  substituted without compatibility evidence.
- Upstream Supermemory documentation describes automatic conversation capture.
  The exact installed plugin's behavior and account state were not inspected.
  Review plugin privacy separately from MCP approval prompts.
- The state-listing method still deserializes complete records. Projection or
  pagination could improve large stores, but no private dataset was read or
  benchmarked and no SQLite JSON-extension dependency was introduced.
- Mapper scores and confidence labels are uncalibrated heuristics. With unsupported
  clinical and gene-colocalisation contributions removed, the current attainable
  maximum is 0.71, below the unchanged `High` threshold. Missing evidence is not
  rescaled to manufacture confidence. HPA enrichment remains unimplemented.
- Live endpoint availability, scientific validity, provider entitlement, plugin
  loading, real OpenCode approval dialogs and OpenChamber integration remain
  unverified. This audit does not establish biological or clinical validation.

## Primary documentation checked

The review used current public documentation, distinguishing V2 from legacy V1:

- [OpenCode V2 configuration](https://opencode.ai/v2/docs/config),
  [agents](https://opencode.ai/v2/docs/agents),
  [commands](https://opencode.ai/v2/docs/commands),
  [skills](https://opencode.ai/v2/docs/skills),
  [permissions](https://opencode.ai/v2/docs/permissions), and
  [plugins](https://opencode.ai/v2/docs/plugins).
- [Requests streaming and response handling](https://docs.python-requests.org/en/latest/user/quickstart/).
- [GTEx OpenAPI schema](https://gtexportal.org/api/v2/openapi.json), including
  `PaginationInfo.numberOfPages`, `page`, and `totalNumberOfItems`.
- [GTEx API guidance](https://gtexportal.org/home/apiPage), including sequential
  request handling and paginated V2 results.
- [NCBI variant data construction](https://clinicaltables.nlm.nih.gov/apidoc/snps/v3/doc.html).
- [Open Targets colocalisation](https://platform-docs.opentargets.org/gentropy/colocalisation),
  which describes comparisons of credible sets rather than automatic gene attribution.
- [Supermemory capture documentation](https://github.com/supermemoryai/opencode-supermemory/blob/main/README.md).

Public documentation and live schemas can advance independently of the installed
binary. Source review and offline tests provide evidence of the fixed behaviors,
not a guarantee against every future defect or service change.

---

<a id="context7-audit"></a>

## CONTEXT7-AUDIT.md

# Context7-assisted audit of the Exa/OpenChamber kit

> **Archived audit record.** Counts and verification results below describe the named archive, not the current checkout. References to preserved files under `references/original-user-agents/` do not apply to this checkout: that archive is absent. See [FOUR-AGENTS.md](FOUR-AGENTS.md) for the correction and the [current configuration audit](ITERATION-ARCHIVE.md#configuration-audit-complete) for current scope and results.

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

---

<a id="life-sciences-audit"></a>

## LIFE-SCIENCES-AUDIT.md

# Life Sciences Research integration audit

This is the historical import audit. For the current correctness fixes, adapted
source hashes, runtime evidence and remaining readiness gates, see
[ITERATION-ARCHIVE.md#life-sciences-readiness](ITERATION-ARCHIVE.md#life-sciences-readiness). Claims below that all
source files are unmodified describe the original import, not today's adapted
helpers.

Date: 2026-11-01. Base: aahsnr-configs/opencode-config commit
5ead2f0a6d3b83addee6dc8282ec6b66817a7bb9. Implementation branch:
life-sciences-foundation. Scope: all files added or changed from this base.

## Verdict

**Public plugin file parity: PASS for version 1.0.3. Whole hosted ecosystem feature parity: NOT ESTABLISHED. Scientific validation: NOT PERFORMED.**

The previous implementation was materially incomplete: it exposed only two public
lookups and a planning command. This audit adds every file under the 50 upstream
skill directories: 161 files, verified with Git blob SHA-1 hashes against the
recursive tree at openai/plugins commit 0722921d5542fc593105c27bd52630babd8b8c2a.
The source snapshot contains 50 SKILL.md files, supporting Python helpers,
references and Codex UI metadata. No source-skill files were modified.

## Findings and corrections

| Finding | Action or remaining constraint |
| --- | --- |
| Missing public research skills and their helper files | Imported the entire pinned 161-file inventory; upstream-lock.json is executable test input |
| Research command only invoked a generic planning skill | Routes through the public research-router or matching source skill |
| Python dependencies undocumented | Added requests and optional matplotlib requirements and environment instructions |
| Validation assumed only nine skills | Updated expected inventory to 59 total skills (nine existing integration/base skills plus 50 upstream skills) |
| No OpenChamber-specific guidance | Added documented command/skill picker and environment guidance plus optional draft-starter example |
| Unclear licensing | Preserved source attribution and recorded absence of a root or plugin license in inspected upstream tree; no permissive license asserted |
| No complete source integrity check | Added per-file upstream hash and Python parse checks |
| Source-to-platform adaptation | Preserved source text; wrapper explains optional Codex subagent references and available OpenCode task mechanism |

## Evidence collected

- Base metadata validator: PASS.
- Six life-science tests: PASS, including 161-file integrity and parsing all upstream Python files.
- Existing installer checks: PASS (dry-run, conflicts, backup/replace, idempotency).
- Temporary XDG installation: all 161 upstream files match checkout bytes.
- Full repository suite: 37 tests; six baseline failures persist. One expects the absent base file references/original-user-agents/web-researcher.md. Five schema tests require jsonschema in their subprocess environment. These are not recorded as passing or silently removed.
- Live Europe PMC probe: HTTP 200 with response bytes. This was a transport probe, not full adapter validation.
- Live AlphaFold DB probe: timed out after five seconds.
- OpenCode/OpenChamber executables: unavailable; no runtime discovery or model/task execution verified.

## Boundaries that prevent a whole-ecosystem completion claim

| Capability | Status |
| --- | --- |
| Public Life Science Research 1.0.3 skills, helper scripts and references | All files present; hash verified and installer verified |
| Every source API endpoint and credentials | Not exhaustively tested; upstream APIs can change independently |
| Multi-source biological conclusions | Require task-specific evaluation; no result generated by this audit |
| GPT-Rosalind models and access controls | Not supplied by this repository; eligibility and provider support required |
| Rosalind Workbench structural/sequence viewers and guided FASTQ/bulk/scRNA workflows | Not implemented by this port |
| Tamarind, Rowan, commercial compute, wet-lab assays and other standalone plugins | Separate integrations/accounts; base configuration does not establish parity |
| Report's custom STAR/GATK/SAMtools adapters, containers and Nextflow workflows | Not implemented; separate from the public plugin snapshot |
| Report's GIAB/ENCODE/docking benchmark figures | Unverified; no underlying data or logs supplied |

The upstream Codex plugin manifest and icon are intentionally excluded from
OpenCode installation because this platform discovers skill directories directly.
The 161-file lock covers all operational skill content, including its UI metadata.
This is not an independent scientific or security audit of every upstream helper.
Some source helpers accept arbitrary endpoint URLs; review requests before use.

## Source verification

Exa was used to locate official OpenAI, OpenCode and OpenChamber pages. Context7
was used for OpenCode V2 skill discovery, bundled relative paths and command
configuration. The GitHub API supplied the exact source tree and blob hashes.
See LIFE-SCIENCES.md for primary-source links and UPSTREAM-NOTICE.md for attribution.

## Pinned skill inventory

- `alphafold-skill`
- `bgee-skill`
- `bindingdb-skill`
- `biobankjapan-phewas-skill`
- `biorxiv-skill`
- `biostudies-arrayexpress-skill`
- `cbioportal-skill`
- `cellxgene-skill`
- `chebi-skill`
- `chembl-skill`
- `civic-skill`
- `clinicaltrials-skill`
- `clinvar-variation-skill`
- `efo-ontology-skill`
- `encode-skill`
- `ensembl-skill`
- `epigraphdb-skill`
- `eqtl-catalogue-skill`
- `eva-skill`
- `finngen-phewas-skill`
- `genebass-gene-burden-skill`
- `gnomad-graphql-skill`
- `gtex-eqtl-skill`
- `gwas-catalog-skill`
- `hmdb-skill`
- `human-protein-atlas-skill`
- `ipd-skill`
- `locus-to-gene-mapper-skill`
- `metabolights-skill`
- `mgnify-skill`
- `ncbi-blast-skill`
- `ncbi-clinicaltables-skill`
- `ncbi-datasets-skill`
- `ncbi-entrez-skill`
- `ncbi-pmc-skill`
- `opentargets-skill`
- `pharmgkb-skill`
- `pride-skill`
- `proteomexchange-skill`
- `pubchem-pug-skill`
- `quickgo-skill`
- `rcsb-pdb-skill`
- `reactome-skill`
- `research-router-skill`
- `rhea-skill`
- `rnacentral-skill`
- `string-skill`
- `tpmi-phewas-skill`
- `ukb-topmed-phewas-skill`
- `uniprot-skill`

## Later research-extension audit

See [ITERATION-ARCHIVE.md#research-audit](ITERATION-ARCHIVE.md#research-audit) for the subsequent Zotero/SciSpace/research/learning extension and current repository checks. The six baseline test failures recorded above are historical; the later isolated environment resolves dependencies and corrects the absent-archive assertion.

---

<a id="life-sciences-readiness"></a>

## LIFE-SCIENCES-READINESS.md

# Life-sciences integration readiness audit

Date: 2026-11-05. Scope: the OpenCode port of the public OpenAI Life Science
Research plugin 1.0.3, pinned at
`0722921d5542fc593105c27bd52630babd8b8c2a`.

## Verdict

The complete 50-skill payload is present, installs correctly, and passes the
offline execution and regression checks below. Confirmed local correctness and
filesystem-safety defects have been fixed. This evidence does not establish an
error-free production system: all-source API compatibility, model-driven task
execution, OpenChamber behavior and scientific accuracy remain unverified.

## Findings fixed

| Finding | Correction and proof |
| --- | --- |
| First overlapping rsID could replace the requested REF/ALT and query a different variant | Five resolver copies require exact native chromosome, position, REF and ALT; preserve each assembly's alleles; reject ambiguous rsIDs and uncertain cross-build mappings. Regression fixtures include two overlapping variants with different alleles. |
| Malformed coordinates escaped as Python tracebacks | All five cohort/GTEx callers emit structured `invalid_input` JSON. Native target-build inputs remain offline. |
| Predictable shared `/tmp` filenames could follow symlinks or overwrite prior exports | Raw exporters use unique private default directories and exclusive file creation; existing files and symlinks are refused. Filesystem failures, including missing query files and cohort temporary-directory creation, produce JSON errors. |
| Wrapper prescribed the wrong mapper interface and working directory | Helpers execute by absolute path from the research project. Mapper uses flags or an input file with explicit approved output paths. JSON input file settings take precedence over the mapper's output flags. |
| Original tests checked hashes and syntax without running imported helpers | New runtime tests check all 161 installed files byte-for-byte, execute 50 installed entrypoints with offline inputs, and execute all three bundled upstream suites. |
| CI omitted runtime dependencies and checks on main pushes | Approved update adds `main` and explicitly installs `life-sciences/requirements.txt`. |

Original hashes remain unchanged in `life-sciences/upstream-lock.json`.
`life-sciences/opencode-adaptations.json` records the original and installed
hashes and reasons for all adapted files, including instructions, helpers and bundled tests. See [the complete audit](ITERATION-ARCHIVE.md#configuration-audit-complete) for current totals. The integrity test requires exact
recorded hashes, unique adaptation paths, a matching upstream commit and original
hashes, and no unexplained changes. The other 108 files remain byte-identical to
the pinned snapshot. Upstream attribution and bundled upstream tests are retained.

## Verification

Environment: Python 3.13.17, OpenCode v2.2.5, requests 2.34.2, matplotlib 3.11.2,
jsonschema 4.26.0, json5 0.17.3 and PyYAML 6.0.3. Python 3.11+ is required by
the integration; other interpreter versions were not tested in this audit.

Focused commands passed:

```sh
python -m unittest discover -s tests -p 'test_*life_sciences.py'
python -m unittest discover -s tests -p 'test_life_sciences*.py'
python -m unittest discover -s tests -p test_variant_resolution.py
python3 validate.py
bash doctor.sh --offline
shellcheck install.sh doctor.sh
bash -n install.sh doctor.sh
```

The broader permitted suite ran 69 tests: 68 passed and one MCP SDK test was
skipped because that SDK was absent. The 16 bundled upstream behavioral tests
also passed through the installed-tree subprocess harness. Controller tests were
excluded to honor the prohibition on agent execution of `mcpctl.py`. Reproduce
the permitted suite with the declared test and runtime dependencies installed:

```sh
python - <<'PY'
import unittest
from pathlib import Path
loader = unittest.TestLoader()
suite = unittest.TestSuite()
for path in sorted(Path('tests').glob('test_*.py')):
    if path.name != 'test_explicit_mcp.py':
        suite.addTests(loader.discover('tests', pattern=path.name))
result = unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(not result.wasSuccessful())
PY
```

The temporary audit environment did not install the MCP SDK, so the stdio MCP
test did not execute. No MCP server was enabled or invoked by this audit.

An isolated XDG installation passed real `opencode debug config --standalone`
and `opencode debug agents --standalone` checks; `deep-research` was discovered.
The managed-service diagnostic initially failed because port 49374 was already
occupied. No existing service settings were changed.

Fresh standalone skill/command inventory calls returned only built-ins or empty
lists. Inspection of the installed binary shows agent listing waits for plugin
initialization while skill/command listing does not. Both singular and plural
directory layouts are supported. A follow-up test used one persistent localhost
server, an isolated XDG installation, and a newly generated temporary password;
it requested `/api/agent` before `/api/skill` and `/api/command` for the same
directory. **All 50 pinned skills, the `deep-research` agent and the
`life-science` command were discovered.** This confirms the initial short-lived
inventory results were caused by initialization timing rather than missing
payloads. Existing credentials were not read or printed. The temporary server
was stopped after verification; no service configuration was changed.

Live read-only probes and actual corrected REST helper executions returned
`ok=true`, HTTP 200, and valid JSON for:

- UniProt: `https://rest.uniprot.org/uniprotkb/P04637.json`
- Ensembl: `https://rest.ensembl.org/info/ping`
- AlphaFold: `https://alphafold.ebi.ac.uk/api/prediction/P00520`

These public example requests used no saved raw responses, private identifiers,
MCP or paid compute. They establish adapter execution for these three requests,
not universal endpoint or scientific correctness.

## Remaining release gates

- Verify all source-specific API contracts and representative successful queries
  for the intended production workloads, including pagination and error paths.
- Validate model-driven routing and an end-to-end research task on the deployment
  host; this audit made no inference calls. OpenChamber was not tested.
- Cross-build conversion deliberately rejects reverse-strand, unanchored and
  ambiguous allele cases. It is not a general liftover implementation. Native
  explicit target-build coordinates are syntactically checked, not validated
  against a reference genome.
- Mapper outputs remain direct writes: select a fresh run directory. Generic
  HTTP helpers still accept caller-selected endpoints and buffer responses;
  compact summaries do not guarantee bounded download size. Review workloads
  before sending sensitive inputs or requesting large payloads.
- Record resolved dependencies for research reproducibility; requirements are
  bounded ranges rather than a frozen deployment lock.
- Upstream redistribution licensing remains unresolved as described in
  `life-sciences/UPSTREAM-NOTICE.md`. This audit does not grant additional rights.

Hosted Rosalind models, Workbench viewers, NGS pipelines and commercial plugins
are outside the public plugin snapshot and this port.

---

<a id="research-audit"></a>

## RESEARCH-AUDIT.md

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

---

<a id="release-notes-exa"></a>

## RELEASE-NOTES-EXA.md

# Release notes: Exa replaces Firecrawl

> **Archived release record.** Counts and verification results below describe that release, not the current checkout. The earlier claim that `references/original-user-agents/` is preserved does not apply to this checkout: that archive is absent. See [FOUR-AGENTS.md](FOUR-AGENTS.md) for the correction and the [current configuration audit](ITERATION-ARCHIVE.md#configuration-audit-complete) for current scope and results.

- Reuses the existing `exa` MCP server, rather than duplicating it. Removes the `firecrawl` server, permission rule, policy and manual controller allowlist entry. Nine MCP servers remain, all `disabled: true` and `codemode: false`.
- Converts `web-researcher` to Exa **default** tools only: `exa_web_search_exa` and `exa_web_fetch_exa`, both `ask`, after an explicit human request and manual server connection.
- Replaces `/firecrawl-research` with `/exa-research`. The old slash command may still exist on machines with earlier kits; the migration helper only archives the exact known old version.
- Updates full documentation, tests and checksums. The four uploaded original agent documents remain unchanged under `references/original-user-agents/` and are **not installed**.
- Offline tests are executed in a temporary environment. Live provider/model authentication, MCP OAuth, OpenCode runtime and OpenChamber UI are NOT verified by these tests.

Sources: https://github.com/exa-labs/exa-mcp-server ; https://opencode.ai/v2/docs/mcp-servers .

---

<a id="release-notes-v2"></a>

## RELEASE-NOTES-v2.md

# Release notes — agent-discovery correction (2026-11-01)

- **Fix**: `doctor.sh` uses `opencode debug agents` (V2), not `opencode agent list` (V1).
- **Fix**: removes unsupported `opencode debug skill` command and checks bundled skill metadata in `validate.py` instead.
- **Improvement**: checks all six expected custom agents in runtime discovery output, distinguishes missing files from invalid CLI commands, and reports troubleshooting steps.
- **Improvement**: `doctor.sh --details` shows full local diagnostics; treat output as potentially sensitive.
- **Improvement**: mocked V2 and V1 CLI tests and extra offline configuration contract assertions.
- **Documentation**: fixes V2 command references, explains `debug config` reports configuration sources, not merged settings.
- **Configuration**: `opencode.jsonc` remains semantically unchanged. Its top-level fields, permission rule shape and values, MCP server definitions and compaction settings were cross-checked with the live official OpenCode V2 schema at https://opencode.ai/config.json (2026-11-01). The complete official schema could not be downloaded into the build container, so full machine-executed schema validation is deferred to `python3 scripts/validate_against_live_schema.py` on a connected machine.
- **Caveat**: OpenCode CLI and OpenChamber Desktop were not executed in this environment. Runtime behavior may differ by installed version and customized configuration.

---

<a id="release-notes-v3"></a>

## RELEASE-NOTES-v3.md

# Schema-validator HTTP 403 fix — 2026-11-01

- Browser-like HTTP request headers added for public JSON Schema download.
- Successful schema downloads are cached for later offline use.
- New `--schema-file` option accepts JSON saved by the user's browser, avoiding Python network requests entirely.
- New `--offline`, `--cache`, `--config`, and `--require-schema` options.
- Correct distinction between full schema validation, partial CLI fallback, and unavailable verification.
- Explicit stale V1 schema detection to avoid misleading failures on valid V2 fields.
- JSONC support via optional `json5` module.
- Ten new regression tests for error cases, cache, schema checks, and JSONC.
- **No changes made to `opencode.jsonc`, agents, permissions, or MCP server settings.**
- Live V2 CLI, network 403 behavior on the user's machine, and full official schema-validation could not be executed in the isolated build environment.

See `docs/ITERATION-ARCHIVE.md#schema-403-fix`.

---

<a id="release-notes-v4"></a>

## RELEASE-NOTES-v4.md

# Explicit MCP release (2026-11-01)

- Every MCP entry remains `disabled: true`.
- Per-server `codemode: false` and per-tool permission `ask`, plus MCP resource approval.
- Unknown MCP services denied by a new `mcp.use` policy; OpenCode >= 2.2.3 required.
- Added experimental *runtime* manual connect/disconnect controller for one shared OpenCode V2 server.
- CLI `/mcps` and OpenChamber Settings → MCP documented as supported fallback.
- Existing agents, commands, skills, tests, 403 schema fallback and installer retained.
- Explicitly does not promise network connection only at moment of tool execution.

---

<a id="schema-403-fix"></a>

## SCHEMA-403-FIX.md

# Fix: HTTP 403 while validating OpenCode V2 configuration

## What happened

The previous `scripts/validate_against_live_schema.py` used Python's default `urllib.request.urlopen("https://opencode.ai/config.json")` request. Some website/CDN security filters deny that request with `HTTP Error 403: Forbidden`. A 403 is a **schema-download failure**, not a failure of `opencode.jsonc` validation.

The schema is still documented at <https://opencode.ai/config.json>. OpenCode merged PR #55524 on October 14, 2026, to publish a unified schema accepting V1 and V2 field forms. The current schema contains the OpenCode V2 `permissions`, `mcp.servers`, `agents`, and `compaction.keep.tokens` properties.

## Replacement script

Run from the extracted package directory:

```bash
python3 -m pip install jsonschema
python3 scripts/validate_against_live_schema.py
```

The script now makes a browser-style request, caches a successfully retrieved **public schema** at `${XDG_CACHE_HOME:-~/.cache}/opencode-v2/config-schema.json`, and reuses this cache on connection errors. It rejects the old V1-only schema if returned by a proxy.

### If the website still returns 403

Open <https://opencode.ai/config.json> in your normal web browser, save the raw JSON as `~/Downloads/config.json`, and run:

```bash
python3 scripts/validate_against_live_schema.py --schema-file "$HOME/Downloads/config.json"
```

This performs full Draft 2020-12 schema validation **without using Python's network connection**. The `--schema-file` must contain the actual full schema, not an HTML error page.

Use a custom config path if you edited the installed file:

```bash
python3 scripts/validate_against_live_schema.py \
  --config "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/opencode.jsonc" \
  --schema-file "$HOME/Downloads/config.json"
```

### Work offline / use a previous download

```bash
python3 scripts/validate_against_live_schema.py --offline
```

If the cache is absent, it performs a CLI fallback (where possible) and clearly labels the result **PARTIAL**. The fallback is *not* equivalent to full schema validation. With `--require-schema`, missing schema always returns a nonzero exit status:

```bash
python3 scripts/validate_against_live_schema.py --require-schema
```

For JSONC comments/trailing commas rather than plain JSON, additionally install `json5`:

```bash
python3 -m pip install json5
```

## Interpretation of status messages

- `PASS: FULL ...`: `jsonschema` accepted the selected config against the retrieved, cached, or manually supplied V2 JSON Schema.
- `PARTIAL ...`: config parsed, and the local OpenCode configuration diagnostic succeeded, but the actual schema was **unavailable**.
- `UNVERIFIED ...`: neither schema validation nor CLI runtime checks could be completed. This is not a definitive finding about the config's validity.
- `FAIL ...`: parse error, invalid schema, a schema rejection, or a CLI diagnostic failure.

Inspect the installed configuration and CLI separately with `opencode debug config` and `opencode debug agents`. `opencode debug config` lists configuration sources in V2; it does not necessarily validate any arbitrary file passed with `--config`.

## Sources

- [OpenCode V2 configuration documentation](https://opencode.ai/v2/docs/config)
- [Published OpenCode config schema](https://opencode.ai/config.json)
- [Schema fix PR #55524, merged October 14, 2026](https://github.com/anomalyco/opencode/pull/55524)
- [OpenCode V2 CLI diagnostics](https://opencode.ai/v2/docs/cli/commands/)

---

<a id="v2-diagnostic-fix"></a>

## V2-DIAGNOSTIC-FIX.md

# OpenCode V2 agent-discovery diagnostic correction

## Root cause

The previous `doctor.sh` issued `opencode agent list`, a legacy command. Current OpenCode V2 documentation instead specifies `opencode debug agents`. It also does **not** list the previous `opencode debug skill` command. The failure alone is not evidence that your agent files or configuration were rejected.

Source: https://opencode.ai/v2/docs/cli/commands/ and https://opencode.ai/v2/docs/agents/.

## Correct runtime checks

```bash
opencode --version
opencode debug --help
opencode debug config     # lists configuration sources
opencode debug agents     # should include chat, coder, work, research, reviewer, digest
opencode mcp list
bash doctor.sh                # automated check with explicit error messages
bash doctor.sh --details      # local full output; REDACT before sharing
```

`python3 validate.py` statically checks the eight bundled skills. In V2, a skill should be tested by loading it through the agent's `skill` tool in a normal session, not by the V1 `debug skill` command.

## If agents are missing

1. Confirm the active binary really is OpenCode V2 (`opencode --version` and `opencode debug --help`).
2. Verify `~/.config/opencode/agents/chat.md`, `work.md`, `coder.md`, `research.md`, `reviewer.md`, and `digest.md` exist. If you use `XDG_CONFIG_HOME`, check `$XDG_CONFIG_HOME/opencode/agents` instead.
3. Run `opencode debug config` to see which configuration sources OpenCode loads. In the V2 CLI, this displays sources, not a resolved JSON object.
4. See whether project-level or managed configuration overrides the global files. Review `OPENCODE_DISABLE_PROJECT_CONFIG` if project agents are missing.
5. Try `opencode reload` after editing files; restart the local app/service if the runtime caches outdated configuration.
6. If OpenChamber Desktop differs from your shell, compare its bundled OpenCode version and configuration path with your installed CLI.

## Configuration contract checked 2026-11-01

The packaged `opencode.jsonc` uses V2 schema fields `$schema`, `default_agent`, `update`, `share`, `snapshots`, `compaction`, `tool_output`, `permissions`, and `mcp.servers` and uses valid enums. Key values were cross-checked manually with the official live schema at https://opencode.ai/config.json and the V2 documentation.

The full online Draft 2020-12 JSON schema validation cannot be executed in this isolated build environment. To verify against the actual authoritative schema on your machine:

```bash
python3 -m pip install jsonschema
python3 scripts/validate_against_live_schema.py
```

No live model or OAuth calls are part of the kit's diagnostics.


If that optional online schema check returns HTTP 403, follow [ITERATION-ARCHIVE.md#schema-403-fix](ITERATION-ARCHIVE.md#schema-403-fix). A blocked download is not evidence that the V2 configuration is wrong.

---

<a id="verification"></a>

## VERIFICATION.md

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

---

<a id="verification-explicit"></a>

## VERIFICATION.md-explicit

# Explicit MCP package verification

Checked November 1, 2026. These are **offline** checks, not a claim of live service compatibility.

- All nine static MCP definitions start `disabled: true` and `codemode: false`.
- Every named MCP tool `NAME_*` is explicitly `ask`, and MCP resource operations also require approval.
- Global `mcp.use` allowlist denies unknown MCP services (OpenCode 2.2.3 or newer).
- The human-operated runtime controller cannot use a non-loopback server and requires interactive terminal confirmation.
- Controller regression tests run against a mock local HTTP server and verify connect, disconnect, session cleanup, cancellation, off-by-default configuration and non-network list.
- Existing installer, schema-403, diagnostics, agents, commands and skills tests pass offline.
- Complete ZIP is checked for CRC and checksum integrity.

Not tested: live OpenCode V2 implementation of experimental API endpoints, OpenChamber Desktop backend URL, OAuth credentials, model inference, actual MCP server behavior and live official schema validation (the schema URL may reject scripted downloads). The runtime endpoints are documented but experimental.

Sources: https://opencode.ai/v2/docs/mcp-servers ; https://opencode.ai/v2/docs/api ; https://opencode.ai/v2/docs/policies ; https://docs.openchamber.dev/mcp/ ; https://docs.openchamber.dev/opencode-server/ .

---

