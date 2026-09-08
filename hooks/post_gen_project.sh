#!/usr/bin/env bash
# Rename the generated directory to YYYY-MM-DD-<slug> and install its virtualenv.
set -euo pipefail

slug="{{ cookiecutter.__project_slug }}"
parent="$(cd .. && pwd)"
target="$parent/$(date +%Y-%m-%d)-$slug"

n=1
while [ -e "$target" ]; do
    target="$parent/$(date +%Y-%m-%d)-$slug-$(printf '%02d' "$n")"
    n=$((n + 1))
done

cd ..
mv "$slug" "$target"
cd "$target"

# A failed sync leaves a usable directory, so warn rather than discarding the
# scaffold that cookiecutter would delete on a non-zero exit.
if command -v uv >/dev/null 2>&1; then
    uv sync || echo "WARNING: 'uv sync' failed. Fix the environment and re-run it." >&2
else
    echo "uv is not installed; skipping 'uv sync'. See https://docs.astral.sh/uv/" >&2
fi

echo ""
echo "Created $target"
echo "Next: cd $(basename "$target") && just explore"
