# Upgrading from earlier OpenCode/OpenChamber or Paseo kits

This release is **OpenCode V2 + OpenChamber only**. The installer does not install or remove Paseo, Kilo, OpenCode V1, or any prior agent configurations. The new bundle contains no Paseo or Kilo integration code.

1. Run `python3 validate.py` and `bash install.sh --dry-run`. Resolve any file conflicts.
2. If you previously installed a kit, compare `~/.config/opencode/opencode.jsonc` with this release before running `bash install.sh --apply --replace`.
3. Previous custom agents, commands, MCP entries, and skills not included in this release **remain on disk**. Review `~/.config/opencode/agents/`, `commands/`, and `skills/` and selectively archive obsolete files yourself. This installer deliberately never deletes files that might contain your work.
4. Check OpenChamber → Settings → Integrations for duplicate MCP server definitions. Do not enable duplicate personal/project configurations.
5. Check Desktop's bundled OpenCode backend version separately from a locally installed `opencode` CLI. This package is designed for documented V2 schema only.
6. The disabled example loop is never installed; schedules already registered in OpenChamber remain unchanged. Disable any old Paseo or systemd timers manually if they target the same task, to prevent duplicate execution.

Backups are written into a new sibling directory named `opencode-backup-YYYYMMDDTHHMMSSZ-PID` only when a different existing file is replaced. A backup is not a full snapshot of all of your older settings. Read `docs/TROUBLESHOOTING.md` for post-upgrade checks.
