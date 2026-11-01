---
name: workflow-router
description: Route requests to relevant local capabilities and independently connected
  MCP services without assuming access to ChatGPT plugins.
---

> OpenCode V2 skill. Instructions only; tools and provider accounts must be connected separately.

# Workflow Router

1. Distinguish conversation, coding, long-form work, academic research, artifacts, productivity, and scientific compute.
2. Check whether the necessary model, local tool, API, or MCP connection is really installed, enabled, authenticated, and authorized.
3. Select no more than the tools needed. Do not enable all MCPs just because they are configured.
4. ChatGPT-installed plugin state, memories, chat history, and OAuth do not transfer automatically.
5. Verify responses from connected sources, document any missing credentials or permissions, and provide links for externally sourced claims.
6. Require explicit authorization before outbound messages, external changes, publication, paid jobs, or privileged commands.
7. Prefer brief tool results and isolate expensive investigations in their own sessions.


**Explicit-only MCP gate:** This skill does not authorize MCP use. Do not connect or invoke MCP servers based on task matching. The user must explicitly name the MCP server and operation and approve each tool call; respect disconnected defaults.
