#!/usr/bin/env bash
# OpenCode V2 CLI diagnostic. Does not invoke model inference or enable MCPs.
set -uo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
mode=runtime
show_details=0
usage() {
  cat <<'EOF'
Usage: ./doctor.sh [--offline] [--details]
  --offline  Validate bundled files only (no OpenCode CLI commands).
  --details  Print captured OpenCode command output (may contain sensitive data).
OpenCode V2 supports 'opencode debug agents', not 'opencode agent list'.
EOF
}
for opt in "$@"; do
  case "$opt" in
    --offline) mode=offline ;;
    --details) show_details=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$opt" >&2; usage >&2; exit 2 ;;
  esac
done
printf 'Validating bundled OpenCode V2 files...\n'
python3 "$root/validate.py" || exit 1
if [[ "$mode" == offline ]]; then
  echo 'PASS: offline checks. CLI/agent discovery was intentionally skipped.'
  exit 0
fi
if ! command -v opencode >/dev/null 2>&1; then
  echo 'NOTICE: no opencode executable found in PATH; CLI checks skipped.' >&2
  echo 'Run ./install.sh --apply and install OpenCode V2 on this host before rerunning.' >&2
  exit 2
fi
printf 'Using OpenCode executable: %s\n' "$(command -v opencode)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/opencode-doctor.XXXXXXXX")" || exit 2
trap 'rm -rf -- "$tmp"' EXIT
umask 077
check() {
  local label="$1" key="$2"; shift 2
  printf 'Checking: %s\n' "$label"
  if "$@" >"$tmp/$key.log" 2>&1; then
    printf 'PASS: %s\n' "$label"
    if ((show_details)); then cat "$tmp/$key.log"; fi
    return 0
  else
    local rc=$?
    printf 'FAIL: %s (exit code %s)\n' "$label" "$rc" >&2
    printf '  Command:' >&2
    printf ' %q' "$@" >&2
    printf '\n' >&2
    if ((show_details)); then
      cat "$tmp/$key.log" >&2
    else
      printf '  Add --details to view the captured output locally. Do not share output without redacting credentials.\n' >&2
    fi
    return 1
  fi
}
check 'CLI version' version opencode --version || exit 3
check 'configuration source discovery' config opencode debug config || exit 3
check 'agent discovery (OpenCode V2)' agents opencode debug agents || {
  echo 'Use: opencode debug agents (V2), not: opencode agent list (V1).' >&2
  echo 'If your CLI lacks this command, compare opencode --version and opencode debug --help.' >&2
  exit 3
}
missing=0
for agent in chat work coder research reviewer digest compactor explore-scout git-gh web-researcher; do
  if grep -Fwq -- "$agent" "$tmp/agents.log"; then
    printf 'PASS: agent %s discovered\n' "$agent"
  else
    printf 'FAIL: custom agent %s not found in OpenCode discovery output\n' "$agent" >&2
    missing=1
  fi
done
if ((missing)); then
  printf '%s\n'     'Check ~/.config/opencode/agents/ and opencode debug config.'     'Install with ./install.sh --apply or --apply --replace after inspecting conflicts.'     'If CLI and OpenChamber Desktop differ, verify their runtime versions.' >&2
  exit 4
fi
# OpenCode V2 does not publish the V1 "opencode debug skill" subcommand.
# Skill paths and frontmatter were checked offline by validate.py.
check 'MCP inventory' mcp opencode mcp list || exit 3
echo 'PASS: CLI diagnostics completed. Skills were checked locally; verify skill loading in a real session.'
echo 'This does not test model authentication, live MCP OAuth, or OpenChamber.'

# Inspect active MCP state separately with: python3 scripts/mcpctl.py status
