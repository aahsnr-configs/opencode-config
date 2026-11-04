#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
target="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
action=dry-run; replace=0; mode=copy
usage(){ echo 'Usage: ./install.sh [--dry-run] [--apply] [--replace] [--link]'; }
for opt in "$@"; do
  case "$opt" in
    --dry-run) action=dry-run;;
    --apply) action=apply;;
    --replace) replace=1;;
    --link) mode=link;;
    -h|--help) usage; exit 0;;
    *) printf 'Unknown option: %s\n' "$opt" >&2; usage >&2; exit 2;;
  esac
done
[[ -n "${HOME:-}" ]] || { echo 'HOME must be set' >&2; exit 2; }
# Refuse linked ancestors as well as linked files: otherwise mkdir/install can
# write outside the selected configuration tree through an existing directory.
check_directory_path() {
  local path="$1"
  while [[ "$path" != . ]]; do
    if [[ -L "$path" || ( -e "$path" && ! -d "$path" ) ]]; then
      echo "REFUSE symlink or non-directory parent: $path" >&2; exit 4
    fi
    [[ "$path" == / ]] && break
    if [[ "$path" == */* ]]; then path="${path%/*}"; path="${path:-/}"; else path=.; fi
  done
}
if [[ "$mode" == link ]]; then
  entries=(opencode.jsonc cli.json AGENTS.md agents commands skills)
  collisions=0; changed=0
  check_directory_path "$target"
  for f in "${entries[@]}"; do
    src="$root/$f"; dest="$target/$f"
    [[ -e "$src" ]] || { echo "REFUSE missing source: $src" >&2; exit 4; }
    if [[ -L "$dest" && "$(readlink -- "$dest")" == "$src" ]]; then
      echo "UNCHANGED: $dest"
    elif [[ -e "$dest" || -L "$dest" ]]; then
      changed=1
      if ((replace)); then echo "REPLACE (with backup): $dest"; else echo "CONFLICT: $dest"; collisions=1; fi
    else
      echo "NEW LINK: $dest -> $src"; changed=1
    fi
  done
  if [[ "$action" == dry-run ]]; then
    echo 'Dry-run only. To write: --link --apply ; to replace conflicts: --link --apply --replace.'
    exit 0
  fi
  if ((collisions)); then
    echo 'No changes made. Choose --link --apply --replace only after reviewing conflicts.' >&2; exit 3
  fi
  if (( ! changed )); then echo 'Already up-to-date; no changes needed.'; exit 0; fi
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  backup="${target}-backup-${stamp}-$$"
  mkdir -p -- "$target"
  # Move all conflicts to backup before creating any links.
  for f in "${entries[@]}"; do
    src="$root/$f"; dest="$target/$f"
    if [[ -L "$dest" && "$(readlink -- "$dest")" == "$src" ]]; then continue; fi
    if [[ -e "$dest" || -L "$dest" ]]; then
      mkdir -p -- "$backup"
      mv -- "$dest" "$backup/$f"
    fi
  done
  for f in "${entries[@]}"; do
    dest="$target/$f"
    if [[ -L "$dest" && "$(readlink -- "$dest")" == "$root/$f" ]]; then continue; fi
    ln -s -- "$root/$f" "$dest"
  done
  if [[ -d "$backup" ]]; then echo "Backups: $backup"; fi
  echo "Linked to $target . Changes to linked files affect the repository."
  exit 0
fi
mapfile -d '' files < <(cd "$root" && find agents commands skills -type f -print0 | sort -z)
files=(opencode.jsonc cli.json AGENTS.md "${files[@]}")
collisions=0
changed=0
for f in "${files[@]}"; do
  src="$root/$f"; dest="$target/$f"
  check_directory_path "${dest%/*}"
  if [[ -L "$dest" ]]; then
    echo "REFUSE symlink destination: $dest" >&2; exit 4
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "REFUSE non-file destination: $dest" >&2; exit 4
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
