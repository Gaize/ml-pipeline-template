#!/usr/bin/env bash
# Scaffold the template into a temporary directory and check that it works.
set -euo pipefail

template_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

echo "==> Scaffolding into $workdir"
cd "$workdir"
cookiecutter "$template_root" --no-input project_name="Template Test"

generated="$(find "$workdir" -maxdepth 1 -type d -name '*-template-test' | head -1)"
if [ -z "$generated" ]; then
    echo "Scaffold produced no directory" >&2
    exit 1
fi
cd "$generated"

echo "==> ruff check"
uv run ruff check .
echo "==> ruff format --check"
uv run ruff format --check .
echo "==> import order"
uv run ruff check --select I .
echo "==> ty"
uv run ty check
echo "==> pytest"
uv run pytest -q
echo "==> explore"
uv run run-explore --no-permutation-test --no-progress

echo ""
echo "Template OK."
