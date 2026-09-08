---
paths:
  - "src/pipeline/common/l0*.py"
  - "src/pipeline/common/effects.py"
  - "src/pipeline/common/visualization.py"
---

Before writing or modifying a step, an effect, or a figure, read and follow
@docs/conventions/observability.md.

**Never log from inside a step body.** It runs only on a cache miss, so a rerun
that hits cache produces an empty MLflow run. Attach an aftereffect to the return
annotation instead.

**An aftereffect on an undecorated function never runs.** It type-checks and does
nothing. If you add one, confirm the function carries `@step_decorator`, `@step`,
or `@subpipeline`.
