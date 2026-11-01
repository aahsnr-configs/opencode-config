# Explicit-only, runtime MCP activation — OpenCode V2 + OpenChamber

## Contract and limitations

1. Every named MCP server is stored in `mcp.servers` with `disabled: true`; none is intentionally connected at startup.
2. Every server has `codemode: false`: model-facing MCP tools appear individually, with `ask` permission for every execution.
3. A global `mcp.use` deny-all policy followed by explicit allow entries for the ten known names prevents surprise connections to *other* MCP servers. This requires OpenCode >= 2.2.3. This policy **does not enable** allowed names; they remain disabled until a human connects one.
4. Human activates a named server only when they are ready to use it. Neither task matching nor the agent should connect any server. A manual connection starts the actual transport; it is **not** a zero-time connection performed simultaneously with the subsequent tool call.
5. Even a connected server cannot execute an MCP tool without `ask` approval unless the user has pre-existing saved approvals or an agent/project configuration overrides the permission. Use **Allow once**, never **Allow always**. Existing saved approvals should be reviewed and cleared as appropriate.
6. Human explicitly disconnects after the task. The server stays connected until disconnect, restart, or process exit; background loops and scheduled tasks must remain MCP-free.

**Security boundary:** AGENTS.md is guidance, not a sandbox. The `ask` permission is a gate on ordinary MCP tool execution, but a shell-enabled agent can potentially contact the Internet directly or read files. For hard isolation disable shell or run in a restricted OS sandbox. OpenChamber integrations/plugins, external provider defaults, and project config can add additional servers; audit them separately. `mcp.use` policy (>=2.2.3) denies unknown names at the integration layer.

## Option A — OpenCode CLI without the controller

Start `opencode`. Open `/mcps` and manually select one named server → Connect. Authenticate if requested. In the user message explicitly name the provider and requested tool operation. At each invocation choose **Allow once**. When done return to `/mcps` and Disconnect. `disabled: true` in config remains unchanged. This is the simplest supported mechanism.

OpenCode documents `/mcps` for runtime manual connection/disconnection: https://opencode.ai/v2/docs/mcp-servers .

## Option B — OpenChamber Desktop

In OpenChamber Settings → MCP inspect the installed list. Do **not** select an integration catalog entry that automatically installs and activates duplicate MCP definitions. Keep every server OFF. Immediately before the specific requested use, switch the ONE required server on; approve the individual tool call; turn it off after the operation. The Settings toggle may persist `disabled` to disk, so recheck the global `opencode.jsonc` before restarting either client and restore `disabled: true` if needed. 

**Important:** Desktop may run its own embedded OpenCode instance. `mcpctl.py` controls only the server URL you specify, so do not assume it controls the Desktop instance unless you've confirmed the backend URL. If the Desktop version lacks the API or MCP toggle functionality, use its native UI or the shared-server web option below. 

## Option C — One shared backend for OpenCode CLI AND OpenChamber Web/PWA

This is the most deterministic cross-client option, because both clients access one OpenCode server and the same runtime MCP connection state:

Terminal A (OpenCode V2 server; local only):

```bash
# Use a secure passphrase: no passwords in committed files or shell history.
read -rsp 'OpenCode server password: ' OPENCODE_PASSWORD; printf '\n'; export OPENCODE_PASSWORD
opencode serve --hostname 127.0.0.1 --port 4096
```

Terminal B (OpenCode CLI, attach to the existing service):

```bash
read -rsp 'OpenCode password: ' OPENCODE_PASSWORD; printf '\n'; export OPENCODE_PASSWORD  # enter the same password as Terminal A
opencode --server http://127.0.0.1:4096
```

Terminal C (OpenChamber web server pointed at that exact backend; requires its authentication to be configured for the external service):

```bash
OPENCODE_HOST=http://127.0.0.1:4096 OPENCODE_SKIP_START=true openchamber
```

Confirm OpenChamber actually connected to the external backend. Its official server documentation warns that an invalid address causes it to start its *own* server instead. If OpenChamber cannot authenticate to an externally password-protected OpenCode server in your installed version, **do not disable backend authentication or expose the API to the network to make it work**. Instead use the OpenChamber-managed instance with its native MCP toggle (Option B).

Terminal D (human-only controller):

```bash
# Set matching OPENCODE_PASSWORD in this shell as well; never paste it into chat.
python3 scripts/mcpctl.py list
python3 scripts/mcpctl.py status
python3 scripts/mcpctl.py session consensus
```

`session` requires a human confirmation, connects the named server, and waits for ENTER. During that window make a user request that explicitly names the desired MCP server; approve each individual tool invocation with **Allow once**. Press ENTER to disconnect. `Ctrl+C` also triggers a disconnect attempt. The script does **not** start background work or run the model. API calls go only to loopback.

The controller uses published **experimental** OpenCode V2 routes: `POST /api/experimental/mcp/{name}/connect` and `/disconnect`, and `GET /api/mcp` for status: https://opencode.ai/v2/docs/api . Experimental routes may change, so use the native UI if your version returns 404/405. Manual activation is intentionally outside the agent.

## Important distinctions

| Requirement | Supported behavior |
|---|---|
| No remote MCP connect at startup | Yes, provided no other configs or catalog services enable one |
| No automatic server selection based on task | Not performed by configuration; instructions prohibit it, and only humans can connect in the documented workflow |
| Actual network connect precisely on tool call | **No**; connection occurs on the human's connect action |
| No individual MCP tool executes without user approval | Yes for ordinary tool routing when every permission remains `ask` and there are no saved Allow-always grants |
| Automatically disconnect after each MCP tool call | **No**; use the manual session controller or UI disconnect |
| Same state for CLI and OpenChamber | Yes only if both attach to the same OpenCode backend |

## Preconditions and troubleshooting

- `opencode --version` should be at least 2.2.3 for `mcp.use` policies. Inspect `opencode debug config` and startup warnings.
- Avoid `--auto` flags and auto-approved permissions. Revoke any previously saved Always permissions for individual MCP tools.
- Don't start a second OpenCode backend while assuming the first is being controlled. `mcpctl.py` deliberately requires a loopback URL.
- Do not enable MCP servers through OpenChamber's integrations catalog without inspecting their default ON status.
- Some remote servers need a separate initial OAuth sign-in and may behave differently on first connection. Authorize those manually; then disconnect again before normal use.
- Scheduled tasks, Session Goals, extensions, and other clients can make tool requests while a server is connected; permission prompts remain essential. For stricter isolation, pause such tasks during an active MCP session.

## Sources

- https://opencode.ai/v2/docs/mcp-servers
- https://opencode.ai/v2/docs/permissions
- https://opencode.ai/v2/docs/policies
- https://opencode.ai/v2/docs/api
- https://docs.openchamber.dev/mcp/
- https://docs.openchamber.dev/opencode-server/


## Exa web-researcher special case

There is only one `exa` definition, already present in this package. It remains disabled at startup. The restricted `web-researcher` subagent has no access to any tools except `exa_web_search_exa` and `exa_web_fetch_exa`; each requests approval. A human must deliberately connect Exa, invoke the agent with a request explicitly naming Exa, then disconnect afterward. See `docs/FOUR-AGENTS.md` and `docs/MIGRATE-TO-EXA.md`.

## Audit correction (2026-11-01)

The controller fails closed when another server reports `connected`, `pending`, or `needs_auth`; an unknown/malformed status also blocks manual activation. These status names follow the published V2 API. `ask` is not equivalent to requiring a new user request: avoid any auto-approval mode and clear saved Allow-always approvals.
