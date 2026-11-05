#!/usr/bin/env bash
# Standalone installation and acceptance; no model, agent, or provider calls.
set -u
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
state=${1:-${XDG_DATA_HOME:-$HOME/.local/share}/opencode/math-research-v2}
python3 "$script_dir/math_research.py" setup --plan --profile all --cuda --state-dir "$state" >/dev/null || exit 1
# A prior setup may already be downloading a profile. Wait without model polling.
if [ -f "$state/setup.lock" ]; then
  flock --wait 7200 "$state/setup.lock" true || exit 1
fi
python3 "$script_dir/math_research.py" setup --apply --profile all --cuda --state-dir "$state"
setup_status=$?
run_dir="$state/acceptance-$(date -u +%Y%m%dT%H%M%SZ)-$$"
python3 "$script_dir/acceptance.py" --state-dir "$state" --output-dir "$run_dir" --cuda
acceptance_status=$?
printf 'Setup exit: %s; acceptance exit: %s; report: %s/summary.json\n' "$setup_status" "$acceptance_status" "$run_dir"
if [ "$setup_status" -ne 0 ] || [ "$acceptance_status" -ne 0 ]; then
  exit 1
fi
