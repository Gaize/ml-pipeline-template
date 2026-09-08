#!/usr/bin/env bash
# Install the virtualenv for the new pipeline.
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
    # A failed sync leaves a usable directory. Cookiecutter deletes the project
    # if this hook exits with an error, so report the failure and continue.
    uv sync || echo "WARNING: 'uv sync' failed. Correct the environment, then run it again." >&2
else
    echo "uv is not installed. Skipped 'uv sync'. See https://docs.astral.sh/uv/" >&2
fi

echo ""
echo "Next: cd {{ cookiecutter.__project_slug }} && just explore"
