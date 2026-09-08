---
paths:
  - "src/pipeline/**/*.py"
---

Before writing or modifying pipeline code, read and follow
@docs/conventions/pipeline-design.md and @docs/conventions/python-coding.md.

The three rules broken most often:

- **Defaults belong on the top-level step.** Reading `settings.foo` inside a step
  body is a cache bug: the value never moves the hash, so the cache does not
  invalidate when it changes.
- **Layer roles are not interchangeable.** L01 loads and does nothing else. L04
  never sees the label. L07 runs the model, L06 trains it, L08 evaluates it.
- **Per-row results are columns on the frame**, not objects in a list.
