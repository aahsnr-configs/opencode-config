# Life Sciences Research for OpenCode and OpenChamber

## Scope and completeness

The integration now contains every file from the 50 skill directories of the public OpenAI Life Science Research plugin 1.0.3 at commit `0722921d5542fc593105c27bd52630babd8b8c2a`. The machine-readable source inventory is [upstream-lock.json](../life-sciences/upstream-lock.json). All 161 Git blob hashes match upstream. Source scripts are unchanged. This is file completeness for that pinned plugin, not demonstrated runtime or scientific parity with the entire hosted OpenAI ecosystem.

The public plugin provides source-specific API helpers and research routing. GPT-Rosalind access, Workbench molecular viewers, guided NGS execution, hosted jobs, commercial providers and other ChatGPT plugins are separate capabilities. This repository does not implement them. The original report's custom STAR/GATK/Nextflow/container architecture and benchmark claims are also not delivered by this plugin.

## Setup

1. Create a Python environment and install `life-sciences/requirements.txt`. `requests` is needed by API scripts; `matplotlib` is used by optional locus-to-gene plots. Dependencies use bounded ranges, not a fully reproducible lock; record the resolved versions for research runs.
2. Run `./install.sh --dry-run`. Review existing configuration conflicts before using `--apply` or the existing opt-in `--replace` behavior. This installs the complete skill folders and command under the selected XDG OpenCode configuration directory. It does not install Python dependencies.
3. Ensure OpenCode/OpenChamber uses that configuration directory and can run the selected Python interpreter. OpenChamber documents `OPENCODE_CONFIG_DIR` for config discovery and Settings → General → Environment variables for its backend environment. A shell virtual environment is not automatically inherited by a separately launched app.
4. In OpenCode invoke `/life-science <question>`. In OpenChamber use `/` at the start to select the command or `$` to select a skill. For broad questions choose `research-router-skill`; use specific database skills for narrow questions.
5. Read the selected SKILL.md and run helpers from that skill directory with the documented JSON input. Helpers call public APIs directly; this bundle has no MCP server and requires no automatic MCP activation. Existing manual MCP policy remains in force for separately connected services.

Example without network execution during installation:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r life-sciences/requirements.txt
python3 -m unittest discover -s tests -p 'test_*life_sciences.py'
```

The earlier `life-sciences/lookup.py` utility remains available for Europe PMC searches and AlphaFold metadata. It is a supplementary utility, not the core router. It remains in the checkout rather than the global installer destination.

An optional [OpenChamber project example](../examples/openchamber/life-sciences.project.json) supplies a draft starter. Merge it manually into a research project's `.openchamber/project.json` after installing the skills; it is not auto-installed and creates no background tasks.

## Verification limits

Offline tests check all 161 source hashes, parse every upstream Python source, exercise the supplementary lookup with controlled responses, and validate base config metadata. A temporary XDG installation was also checked byte-for-byte for all 161 files. No real OpenCode/OpenChamber executable is available here. A live Europe PMC probe returned HTTP 200; an AlphaFold DB probe timed out. This is not an all-source availability test. Authentication, provider quotas and scientific results remain unverified. File equality does not establish API correctness or biological validation.

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
