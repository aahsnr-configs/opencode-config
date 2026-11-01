---
name: coding-quality
description: Implement, review, test, and document reliable coding changes in Git
  repositories with read-only review and approval gates.
---

> OpenCode V2 skill. Instructions only; tools and provider accounts must be connected separately.

# Coding Quality

1. Start by reading AGENTS.md, project documentation, file layout, and applicable tests.
2. Prefer the smallest correct patch; avoid modifying unrelated code.
3. Run targeted tests and lint only when permitted, using clearly bounded commands and recorded output.
4. Review final diff, assess security regressions, and separate verified test results from unrun checks.
5. Never commit, push, deploy, or open a pull request without the user's authorization.
6. When concurrent work is needed, prefer a new worktree and avoid modifying the base worktree.


**Explicit-only MCP gate:** This skill does not authorize MCP use. Do not connect or invoke MCP servers based on task matching. The user must explicitly name the MCP server and operation and approve each tool call; respect disconnected defaults.
