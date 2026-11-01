# Security model and limitations

1. OpenCode permissions are **not filesystem sandboxing**. `shell`, browser automation, and third-party MCP tools may bypass a naive file restriction. Run untrusted repositories inside an OS container or restricted account.
2. The configuration starts with a global `* → ask` policy, then permits read/search/skill/question, denies direct reads for common secret paths, and asks for file edits, shell, external-directory, web, MCP code-mode execution. Client approval handling can differ, so test with harmless actions first.
3. Global deny examples for secrets can be bypassed by reads through another tool. Never depend on filename globs for sensitive secrets; restrict filesystem access and environment credentials.
4. All MCP servers start `disabled: true`. OAuth permissions and remote-side write permissions are independent of local prompt rules; limit scopes at the provider.
5. Git pushes and `rm -rf` are denied by common shell patterns, but compound commands and arbitrary tools can still have side effects. Require human confirmation and keep backups.
6. An enabled MCP tool may modify external state. Consider the name, tool schemas, the actual permission prompt, and provider security settings before approving.
7. Do not publish OpenChamber's port to the internet without strong password/TLS/tunnel controls. Prefer loopback-only local operation.
8. Scheduled tasks or goal loops incur model charges/usage. The example task is disabled and contains a model placeholder. Browser closure does not end OpenChamber server jobs; stopping the server does.
9. Never use `opencode run --auto` for unattended jobs in this kit; it autoapproves non-denied permissions.
