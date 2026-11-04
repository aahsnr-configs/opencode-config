---
name: life-science-research
description: Coordinate the complete 50-skill public OpenAI Life Science Research plugin port for OpenCode, with explicit provenance and validation limits.
---

# Life science research in OpenCode

Load research-router-skill for broad or multi-source questions. For narrow lookups, load the appropriate database skill directly. All 50 source skills retain their bundled Python scripts and references. Resolve scripts and references relative to the directory containing the selected SKILL.md, then invoke scripts by absolute path while keeping the working directory in the research project. Never change into the global skill directory to produce research artifacts.

Use Python 3.11+ with requests installed; locus-to-gene plotting additionally uses matplotlib. Most helpers accept JSON on stdin. The locus mapper is an exception: invoke its absolute scripts/map_locus_to_gene.py path with --input-json research/input.json or documented CLI flags. Use --help to inspect its CLI without network activity. When using an input file, set mapping_output_path, summary_output_path and figure_output_dir inside the approved research/ tree in that JSON; output flags are only applied by the mapper when no --input-json is supplied. For flag-based runs, set all three output flags explicitly. Disable optional figures with --no-include-figures when unnecessary. Override upstream examples that assume a different working directory.

Raw responses are opt-in. Supply a new, approved research/ output path when saving them. Existing output files and symlinks are refused; choose a new filename. Default raw output locations use private temporary directories; report the returned path rather than assuming an upstream /tmp filename. The mapper writes its named outputs directly, so select a new run directory to preserve earlier research.

Variant lookups must preserve assembly, REF and ALT. Cross-build resolution rejects ambiguous alleles and mappings; report the error instead of substituting the first overlapping rsID or alternate allele. These checks do not replace validated liftover or biological interpretation.

Resolve identifiers, species, assembly, tissue, units, and study context before combining evidence. Record query parameters, retrieval dates, sources, output paths and limitations. Distinguish association from causality and computed predictions from experimental observations. Never claim benchmark or biological validation merely because a helper succeeds.

Respect AGENTS.md. This port grants no model, account, paid compute, clinical data, or MCP authorization. Use only tools available in this OpenCode installation. Codex subagent references in upstream text describe optional coordination; use OpenCode's available task mechanism only when permitted. Do not invent missing agent APIs.

The source snapshot is file complete for the public plugin version 1.0.3, with local correctness and output-safety adaptations recorded in life-sciences/opencode-adaptations.json in the checkout. Hosted Rosalind Workbench features and other plugins are outside that snapshot. Read the repository docs/LIFE-SCIENCES.md for setup and the validation ledger; ask for the checkout location if needed.
