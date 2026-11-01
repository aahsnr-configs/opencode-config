#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
target="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
action=dry-run; replace=0
usage(){ echo 'Usage: ./install.sh [--dry-run] [--apply] [--replace]'; }
for opt in "$@"; do
  case "$opt" in
    --dry-run) action=dry-run;;
    --apply) action=apply;;
    --replace) replace=1;;
    -h|--help) usage; exit 0;;
    *) printf 'Unknown option: %s\n' "$opt" >&2; usage >&2; exit 2;;
  esac
done
[[ -n "${HOME:-}" ]] || { echo 'HOME must be set' >&2; exit 2; }
mapfile -d '' files < <(cd "$root" && find agents commands skills -type f -print0 | sort -z)
files=(opencode.jsonc AGENTS.md "${files[@]}")
collisions=0
changed=0
for f in "${files[@]}"; do
  src="$root/$f"; dest="$target/$f"
  if [[ -L "$dest" ]]; then
    echo "REFUSE symlink destination: $dest" >&2; exit 4
  fi
  if [[ -e "$dest" ]]; then
    if cmp -s -- "$src" "$dest"; then echo "UNCHANGED: $dest"; continue; fi
    changed=1
    if ((replace)); then echo "REPLACE (with backup): $dest"; else echo "CONFLICT: $dest"; collisions=1; fi
  else echo "NEW: $dest"; changed=1; fi
done
if [[ "$action" == dry-run ]]; then
  echo 'Dry-run only. To write: --apply ; to replace existing different files: --apply --replace.'
  exit 0
fi
if ((collisions)); then
  echo 'No changes made. Choose --apply --replace only after reviewing conflicts.' >&2; exit 3
fi
if (( ! changed )); then echo 'Already up-to-date; no changes needed.'; exit 0; fi
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="${target}-backup-${stamp}-$$"
# Stage all files first; refuse writable-destination collisions before creating staged files.
stage="$(mktemp -d "${TMPDIR:-/tmp}/opencode-kit.XXXXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
for f in "${files[@]}"; do mkdir -p -- "$stage/$(dirname -- "$f")"; cp -- "$root/$f" "$stage/$f"; done
for f in "${files[@]}"; do
  dest="$target/$f"
  if [[ -e "$dest" && ! -L "$dest" ]] && ! cmp -s "$stage/$f" "$dest"; then
    mkdir -p -- "$backup/$(dirname -- "$f")"
    cp -p -- "$dest" "$backup/$f"
  fi
done
# Not an atomic transaction across all files; backups exist before replacements.
for f in "${files[@]}"; do
  dest="$target/$f"
  if [[ -e "$dest" ]] && cmp -s "$stage/$f" "$dest"; then continue; fi
  mkdir -p -- "$(dirname -- "$dest")"
  install -m 0644 -- "$stage/$f" "$dest"
done
if [[ -d "$backup" ]]; then echo "Backups: $backup"; fi
echo "Installed to $target . No credentials or MCP logins were configured."
echo 'Zotero/research helpers require a separate Python package install; see docs/RESEARCH-SETUP.md.'
