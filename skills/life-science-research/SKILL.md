---
name: life-science-research
description: Coordinate the complete 50-skill public OpenAI Life Science Research plugin port for OpenCode, with explicit provenance and validation limits.
---

# Life science research in OpenCode

Load research-router-skill for broad or multi-source questions. For narrow lookups, load the appropriate database skill directly. All 50 source skills retain their bundled Python scripts and references; scripts and references are relative to the directory containing the selected SKILL.md. Run Python helpers with JSON on stdin as documented by that skill. Use a Python environment with requests installed; locus-to-gene plotting additionally uses matplotlib.

Resolve identifiers, species, assembly, tissue, units, and study context before combining evidence. Record query parameters, retrieval dates, sources, output paths and limitations. Distinguish association from causality and computed predictions from experimental observations. Never claim benchmark or biological validation merely because a helper succeeds.

Respect AGENTS.md. This port grants no model, account, paid compute, clinical data, or MCP authorization. Use only tools available in this OpenCode installation. Codex subagent references in upstream text describe optional coordination; use OpenCode's available task mechanism only when permitted. Do not invent missing agent APIs.

The source snapshot is file complete for the public plugin version 1.0.3. Hosted Rosalind Workbench features and other plugins are outside that snapshot. Read the repository docs/LIFE-SCIENCES.md for setup and the validation ledger; ask for the checkout location if needed.
