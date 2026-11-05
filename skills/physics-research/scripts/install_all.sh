#!/bin/bash
# Run directly from a terminal or systemd user service. No model calls.
set -uo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
state_dir="${XDG_DATA_HOME:-$HOME/.local/share}/opencode/physics-research-v5"
if [[ $# -gt 0 ]]; then
  if [[ $# -ne 2 || $1 != --state-dir ]]; then
    echo 'Usage: install_all.sh [--state-dir PATH]' >&2
    exit 2
  fi
  state_dir=$2
fi
python3 "$script_dir/physics_research.py" setup --apply --profile all --cuda --state-dir "$state_dir"
setup_status=$?
output_dir="$state_dir/acceptance-$(date -u +%Y%m%dT%H%M%SZ)-$$"
python3 "$script_dir/physics_research.py" acceptance --profile all --cuda --state-dir "$state_dir" --output-dir "$output_dir"
acceptance_status=$?
printf 'Setup exit: %s; acceptance exit: %s; results: %s\n' "$setup_status" "$acceptance_status" "$output_dir"
if [[ $setup_status -ne 0 || $acceptance_status -ne 0 ]]; then exit 1; fi
