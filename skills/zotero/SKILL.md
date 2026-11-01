---
name: zotero
description: Search Zotero library metadata, collections, tags and indexed attachment text; export references, resolve Better BibTeX citation keys and preview explicitly approved imports.
---

# Zotero

The `zotero` local stdio MCP server is supplied by the separately installed opencode-research-tools package. It starts disabled. The human must connect it; each call requires Allow once and an explicit current-user request naming Zotero and the operation. Do not invoke the controller or modify configuration. The selected backend must run on the same computer as Zotero for local mode. Cloud OpenCode localhost is not the desktop's localhost. Web mode is explicit and needs a scoped Zotero API key and numeric user ID in backend environment settings.

1. Use status when requested to distinguish unreachable Zotero, disabled API (403), and local write capability. Do not change Zotero preferences yourself.
2. Search bounded pages; retain item keys, DOI metadata and Zotero source links. Collections and tags are supported. Item children include attachment metadata.
3. Indexed fulltext may be absent and does not guarantee PDF page numbers. Distinguish metadata, abstracts and actually read full text. Never follow attachment paths automatically or upload files to external providers without approval.
4. Export selected keys as bibtex, biblatex, ris or csljson. Better BibTeX readiness, citation_keys and bbt_export are optional separate tools. Never invent citation keys. Preserve existing bibliography entries; ask before replacing a file. Use the human-configured Better BibTeX Keep updated export for automatic bibliography maintenance.
5. Import is a write operation. First review native Zotero JSON through import_preview. Then show the items and exact digest and obtain explicit import approval. Call import_items only with that digest. The helper checks DOI duplicates and rejects matches; items without DOIs still need manual title review. Zotero 10+ local authorization prompts may be required; older versions use manual import or explicitly configured Web API. Inspect per-item failures; do not blindly retry an ambiguous write.

CLI alternative only when specifically requested and approved: `opencode-research-tools zotero`, one JSON object on stdin such as `{"operation":"search","query":"TP53","limit":5}`. This is not an alternative route around a denied MCP call. No library-delete, arbitrary HTTP or Better BibTeX mutation tools are exposed.
