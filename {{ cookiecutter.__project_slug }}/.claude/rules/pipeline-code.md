---
paths:
  - "src/pipeline/**/*.py"
---

Before you write or change pipeline code, read and obey
@docs/conventions/pipeline-design.md and @docs/conventions/python-coding.md.

Three rules cause most errors:

- **Default values belong on the top-level step.** A step body that reads
  `settings.foo` is a cache defect. The value is not an argument, so a change to
  it does not clear the cache.
- **Each layer has one function.** L01 only reads. L04 does not use the label.
  L07 runs the model, L06 trains it, and L08 measures it.
- **Per-row results are columns on the frame**, not objects in a list.
