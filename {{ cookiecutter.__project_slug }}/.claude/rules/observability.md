---
paths:
  - "src/pipeline/common/l0*.py"
  - "src/pipeline/common/effects.py"
  - "src/pipeline/common/visualization.py"
---

Before you write or change a step, an effect, or a figure, read and obey
@docs/conventions/observability.md.

**Do not write a log statement in a step body.** It runs only on a cache miss, so
a run that uses the cache gives an empty MLflow run. Put an aftereffect on the
return annotation.

**An aftereffect on a function with no decorator does not run.** It passes the
type check and it does nothing. If you add one, make sure that the function has
`@step_decorator`, `@step`, or `@subpipeline`.
