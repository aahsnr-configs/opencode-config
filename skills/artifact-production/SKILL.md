---
name: artifact-production
description: Produce and validate requested DOCX, PDF, XLSX, PPTX, Markdown, CSV,
  charts, diagrams, and other local deliverables.
---

> OpenCode V2 skill. Instructions only; tools and provider accounts must be connected separately.

# Artifact Production

1. Honor the requested final file format and user-provided editable templates.
2. For local outputs, choose appropriate installed tools: python-docx, ReportLab, openpyxl, python-pptx, matplotlib, or other audited libraries.
3. Read the required library's format guidance before making the file. For PDF verify pages and rendered layout; for XLSX check formulas, sheet names, and styles; for slides ensure nothing is cropped.
4. Check that the requested output file exists, then report its absolute location and what was validated.
5. A named ChatGPT template plugin is not identical to a locally available template file. Do not invent proprietary assets.
6. Ask approval before overwriting, uploading, sharing, or publishing files.


**Explicit-only MCP gate:** This skill does not authorize MCP use. Do not connect or invoke MCP servers based on task matching. The user must explicitly name the MCP server and operation and approve each tool call; respect disconnected defaults.
