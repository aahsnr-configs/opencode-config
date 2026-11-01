---
name: productivity-automation
description: Work safely with task trackers, calendar, mail, cloud files, and optional
  recurring scheduled actions.
---

> OpenCode V2 skill. Instructions only; tools and provider accounts must be connected separately.

# Productivity Automation

1. List the connected sources actually available (e.g., TickTick, GitHub, Google Workspace preview integrations, or independently installed alternatives).
2. Search/read first; prepare proposed actions with destination, recipients, dates, and irreversible consequences.
3. Confirm explicitly before sending email, changing calendar events, deleting records, sharing files, assigning tasks, or creating recurring jobs.
4. The ChatGPT web app's connections do not supply local OpenCode credentials.
5. For scheduled activity, use the product's documented task scheduler where supported; on Linux, use separately installed systemd user timers if needed.
6. Ensure the local service and session model are authorized before an unattended run. Never use broad auto-approval on a sensitive account.


**Explicit-only MCP gate:** This skill does not authorize MCP use. Do not connect or invoke MCP servers based on task matching. The user must explicitly name the MCP server and operation and approve each tool call; respect disconnected defaults.
