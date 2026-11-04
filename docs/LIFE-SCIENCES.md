# Life Sciences Research for OpenCode and OpenChamber

## Scope and completeness

The integration contains every file from the 50 skill directories of the public OpenAI Life Science Research plugin 1.0.3 at commit `0722921d5542fc593105c27bd52630babd8b8c2a`. The original source inventory and hashes remain in [upstream-lock.json](../life-sciences/upstream-lock.json). Local variant-resolution and output-safety corrections are recorded in [opencode-adaptations.json](../life-sciences/opencode-adaptations.json). Integrity checks require exact upstream hashes for unchanged files and exact adapted hashes for corrected files. This is completeness for that pinned plugin, not demonstrated scientific parity with the entire hosted OpenAI ecosystem.

The public plugin provides source-specific API helpers and research routing. GPT-Rosalind access, Workbench molecular viewers, guided NGS execution, hosted jobs, commercial providers and other ChatGPT plugins are separate capabilities. This repository does not implement them. The original report's custom STAR/GATK/Nextflow/container architecture and benchmark claims are also not delivered by this plugin.

## Setup

1. Create a Python **3.11+** environment and install `life-sciences/requirements.txt`. `requests` is needed by API scripts; `matplotlib` is used by optional locus-to-gene plots. Dependencies use bounded ranges, not a fully reproducible lock; record the resolved versions for research runs.
2. Run `./install.sh --dry-run`. Review existing configuration conflicts before using `--apply` or the existing opt-in `--replace` behavior. This installs the complete skill folders and command under the selected XDG OpenCode configuration directory. It does not install Python dependencies.
3. Ensure OpenCode/OpenChamber uses that configuration directory and can run the selected Python interpreter. OpenChamber documents `OPENCODE_CONFIG_DIR` for config discovery and Settings → General → Environment variables for its backend environment. A shell virtual environment is not automatically inherited by a separately launched app.
4. In OpenCode invoke `/life-science <question>`. In OpenChamber use `/` at the start to select the command or `$` to select a skill. For broad questions choose `research-router-skill`; use specific database skills for narrow questions.
5. Read the selected SKILL.md. Resolve its script path relative to that file, then invoke it by absolute path from the research project. Most helpers use JSON stdin; the locus mapper uses flags or `--input-json`. Put mapper output paths in a new approved `research/` run directory. When using `--input-json`, put the output settings inside that JSON: the mapper ignores output flags in that mode. Follow the OpenCode wrapper's execution rules when upstream examples assume a different working directory. Helpers call public APIs directly; this bundle has no MCP server. Existing manual MCP policy remains in force for separately connected services.

Example without network execution during installation:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
python3 -m pip install -r life-sciences/requirements.txt
python3 -m unittest discover -s tests -p 'test_*life_sciences.py'
python3 -m unittest discover -s tests -p 'test_life_sciences*.py'
python3 -m unittest discover -s tests -p 'test_variant_resolution.py'
```

For example, from a research project (replace the absolute skill path with the one OpenCode reports):

```sh
python /absolute/config/opencode/skills/locus-to-gene-mapper-skill/scripts/map_locus_to_gene.py \
  --trait-query 'type 2 diabetes' --no-include-figures \
  --mapping-output-path research/run-001/mapping.json \
  --summary-output-path research/run-001/summary.md \
  --figure-output-dir research/run-001/figures --print-result
```

This example makes public API requests when executed. Raw-response saving is opt-in; use new approved output paths. Helpers refuse existing files and symlinks rather than overwriting them. Default raw outputs use private temporary directories, so use the returned path. Mapper output files remain direct writes; use a fresh run directory. Cross-build variant resolution now rejects uncertain allele mappings and ambiguous multi-allelic rsIDs instead of choosing the first available allele. Resolve these cases with a validated variant-normalization/liftover workflow.

The earlier `life-sciences/lookup.py` utility remains available for Europe PMC searches and AlphaFold metadata. It is a supplementary utility, not the core router. It remains in the checkout rather than the global installer destination.

An optional [OpenChamber project example](../examples/openchamber/life-sciences.project.json) supplies a draft starter. Merge it manually into a research project's `.openchamber/project.json` after installing the skills; it is not auto-installed and creates no background tasks.

## Verification limits

Offline tests check all 161 upstream/adapted hashes, parse every upstream Python source, exercise the supplementary lookup and corrected helpers with controlled responses, and validate base config metadata. The runtime suite checks a temporary XDG installation byte-for-byte, executes all 50 installed entrypoints with non-network inputs, and runs the three bundled upstream suites (16 behavioral tests) in isolation. See the current audit for installed OpenCode and live-probe results. These checks do not establish all-source availability, biological accuracy, provider quotas, or hosted feature parity.

See [LIFE-SCIENCES-AUDIT.md](LIFE-SCIENCES-AUDIT.md) for findings and [UPSTREAM-NOTICE.md](../life-sciences/UPSTREAM-NOTICE.md) for attribution and the unresolved upstream license status. Review scripts and endpoint terms before using sensitive data or redistributing upstream content.

## Primary references checked

- https://github.com/openai/plugins/tree/0722921d5542fc593105c27bd52630babd8b8c2a/plugins/life-science-research
- https://openai.com/index/introducing-gpt-rosalind/
- https://help.openai.com/en/articles/20001193-gpt-rosalind-for-life-sciences-research
- https://opencode.ai/v2/docs/skills/
- https://opencode.ai/v2/docs/commands/
- https://docs.openchamber.dev/skills/
- https://docs.openchamber.dev/chat-input/
- https://docs.openchamber.dev/environment/
- https://docs.openchamber.dev/repository-config/
