---
description: User-explicit Exa-only web research, without automatic MCP activation
agent: web-researcher
subagent: true
---

The human explicitly requests **Exa** research on: $ARGUMENTS

Only proceed if the `exa` MCP server has already been manually connected to this OpenCode backend, and the user explicitly intended Exa rather than generic web search. Each `exa_web_search_exa` or `exa_web_fetch_exa` operation must be approved individually with **Allow once**. Do not connect or enable MCP, use other providers, trigger autonomous research, or request permanent approval. Otherwise STOP and tell the human how to connect Exa manually. Remind the human to disconnect Exa after finishing.
