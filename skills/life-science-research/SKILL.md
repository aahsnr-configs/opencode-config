---
name: life-science-research
description: Plan and assess reproducible life-science research, public literature lookups, and protein structure metadata with explicit evidence and provenance.
---

# Life science research

1. Specify the biological question, species, inputs, references, constraints, and intended output. Do not imply clinical suitability.
2. Read docs/LIFE-SCIENCES.md in the configuration repository for capability status and usage. Ask the user for its location if it is not available. The local lookup script is not an MCP server and is not installed by install.sh; run it from the repository checkout.
3. For public data, the user may run the lookup script for Europe PMC or AlphaFold DB. Review the returned provenance and primary references. AlphaFold DB returns existing predictions, not a new prediction; model confidence is not experimental validation.
4. For workflows, identify reference versions, software and container versions, resource needs, controls, and validation data before execution. Preserve inputs, commands, versions, checksums, logs, and parameters. Validate outputs against appropriate reference material.
5. Never state that an analysis, benchmark, database query, or experiment ran unless there is evidence. Respect the repository's explicit MCP policy, provider terms, data privacy requirements, and paid-compute approval rules.
