# OpenCode research tools

Python 3.10+ package for the approved research integration. Install with
`python -m pip install './integrations/research-tools[mcp]'` from the repository
root. No installation step connects providers or imports Zotero items.

`opencode-research-tools doctor` performs offline capability checks. Other
commands consume JSON stdin: zotero, run, scispace-import and optional
openai-research. serve-zotero starts the explicitly enabled stdio server.

See ../../docs/RESEARCH-SETUP.md and the installed skill references for operations,
credentials, imports, persistence, approval gates and current limits. Importing
the Python package performs no I/O. Public core code uses the standard library;
the stdio server uses the official MCP SDK optional dependency.
