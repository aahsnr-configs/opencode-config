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


If that optional online schema check returns HTTP 403, follow [SCHEMA-403-FIX.md](SCHEMA-403-FIX.md). A blocked download is not evidence that the V2 configuration is wrong.
