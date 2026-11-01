# Troubleshooting and runtime acceptance checks

## First checks

```bash
opencode --version
opencode debug config
opencode debug agents
python3 validate.py
opencode mcp list
opencode models
```

These diagnostics should not submit a paid model request. `opencode models` can contact provider metadata. Model names are chosen after provider login, not hard-coded in the kit.

## OpenChamber Desktop versus Web/PWA

- Desktop bundles a matching OpenCode binary. It may not be the same version as a separately installed system CLI. Check the backend version in the app and compare. If your installed CLI and Desktop disagree, test settings with each backend separately.
- Web/PWA requires an installed OpenCode V2 and Node.js >=24.14; start on localhost, check `openchamber status` / `openchamber logs` if it cannot connect.
- If using a separately launched server, see https://docs.openchamber.dev/opencode-server/ for `OPENCODE_HOST` and `OPENCODE_SKIP_START`.
- Do not install a second instance of an MCP integration through OpenChamber if it is already configured in your OpenCode file.

## Config not loading

Check `~/.config/opencode/opencode.jsonc`, project-level `opencode.jsonc` and `.opencode/opencode.jsonc`; project and managed policies may override global settings. OpenCode V2 `opencode debug config` lists configuration sources, not necessarily the fully resolved settings. The `debug agents` command lists discovered agents.

## Authentication issues

Use `/connect` and model picker or the provider's documented login flow for model authorization. MCP OAuth uses `opencode mcp auth NAME` or `/mcps`. Neither inherits ChatGPT web-account plugin sessions. Undermind needs specific OAuth client registration, so generic MCP authentication may fail.

## Unexpected tool permissions

`permissions` is an ordered array: the last matching rule wins. Agent rules append after global rules. Test edit denial in `chat` and access prompts in `work` with harmless operations. Do not assume shell restrictions cover third-party MCP writes.

## Scheduling

Use OpenChamber Scheduled Tasks UI first. A scheduled task requires an authenticated model and a running OpenChamber server. The example loop has `enabled: false` and a model placeholder; edit before testing with Run now.

## Agent discovery failed in old doctor.sh

The original command `opencode agent list` was from OpenCode V1; in V2 use `opencode debug agents`. The original `opencode debug skill` check was also V1-specific. Run `bash doctor.sh --details` for local diagnostics; avoid sharing unredacted output. If the six custom agents are missing, verify `~/.config/opencode/agents` and review config source precedence, then restart/reload the V2 service if appropriate (`opencode reload`). An installed CLI version different from the OpenChamber-bundled runtime may show different results.
