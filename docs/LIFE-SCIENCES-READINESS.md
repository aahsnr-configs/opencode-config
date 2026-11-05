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
hashes and reasons for all adapted files, including instructions, helpers and bundled tests. See [the complete audit](CONFIGURATION-AUDIT-COMPLETE.md) for current totals. The integrity test requires exact
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
