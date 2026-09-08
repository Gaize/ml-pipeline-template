#!/usr/bin/env bash
# Format, fix, and type check a Python file after it is written.
# Skips F401 so a half-finished edit does not lose imports it is about to use;
# `just lint-check` catches those.
set -uo pipefail

[ -n "${CLAUDE_SKIP_LINT:-}" ] && exit 0

file=$(cat - | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)
case "$file" in
    *.py) ;;
    *) exit 0 ;;
esac
[ -f "$file" ] || exit 0

root="$(dirname "$file")"
while [ "$root" != "/" ] && [ ! -f "$root/pyproject.toml" ]; do
    root="$(dirname "$root")"
done
[ -f "$root/pyproject.toml" ] || exit 0

cd "$root" || exit 0

status=0
run() {
    local out
    if ! out=$("$@" 2>&1); then
        echo "$out" >&2
        status=1
    fi
}

run uv run ruff format "$file"
run uv run ruff check --fix --extend-ignore F401 "$file"
run uv run ruff check --select I --fix "$file"
run uv run ty check "$file"

# Exit 2 feeds the output back to the agent as a correction.
[ $status -eq 0 ] || exit 2
exit 0
