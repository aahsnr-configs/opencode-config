---
name: scispace
description: Use an independently authenticated provider-confirmed SciSpace MCP connection for scholarly discovery and analytical columns, or inspect user-exported SciSpace CSV/JSON tables when direct access is unavailable.
---

# SciSpace

ChatGPT's SciSpace account and tools are not inherited by OpenCode. Published SciSpace guidance restricts its listed MCP connector to ChatGPT/Claude; detailed REST request schemas were not retrievable during implementation. No remote endpoint or REST payload is guessed or shipped as a working connection.

The human may configure an official endpoint supplied by SciSpace for their account/client using scripts/configure_research.py from the config checkout. This is a human-run dry-run/apply utility, not an agent action. It leaves the server disabled. Never run it or the MCP controller as an agent. Once manually connected, each call still requires explicit current-user provider/operation authorization and Allow once.

If actual SciSpace tools are available, read their live schemas first. Use a full natural-language research question for paper search. Retain provider paper IDs, which are not DOI strings. Use those IDs and the original question when requesting supported analytical columns. Do not assume that live tool names or columns equal those in another client. Distinguish provider-generated summaries from original paper evidence and metadata/abstract access from full-text access. State when direct access is blocked.

For supplied exports, `opencode-research-tools scispace-import` reads JSON stdin with `text` (the exported table contents) and `format` (`csv` or `json`). It preserves arbitrary columns and marks results as unverified exported data. Use an approved shell call, not interpolated user text in a shell command. Verify DOI/title metadata before adding rows to a research run. Export inspection is not a live SciSpace search and must not be described as one.

Do not upload private PDFs, start paid tasks, or create accounts merely to test a connection. SciSpace's native UI widgets are not emulated; use normal OpenChamber tables and exported artifacts.
