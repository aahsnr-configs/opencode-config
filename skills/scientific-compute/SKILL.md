---
name: scientific-compute
description: Plan chemical, molecular, structure, and bioinformatics calculations
  with Tamarind Bio or Rowan, requiring approval for compute spend.
---

> OpenCode V2 skill. Instructions only; tools and provider accounts must be connected separately.

# Scientific Compute

1. Identify molecules, proteins, sequences, structures, units, methods, assumptions, and deliverables.
2. Tamarind Bio remote MCP (https://mcp.tamarind.bio/mcp) offers catalog discovery and job workflows once separately authenticated. Rowan offers a Python SDK and may offer MCP according to workspace configuration.
3. Start with no-spend capability/schema checks. Do not submit paid jobs or lab assays to validate an MCP connection.
4. Ask permission after providing job parameters, estimated cost, expected outputs, and failure/cancellation behavior.
5. Keep provenance, job IDs, versions, scientifically relevant limitations, and inputs; never claim a result until returned by a real tool.
6. Validate biological and chemical outputs independently where feasible.


**Explicit-only MCP gate:** This skill does not authorize MCP use. Do not connect or invoke MCP servers based on task matching. The user must explicitly name the MCP server and operation and approve each tool call; respect disconnected defaults.
