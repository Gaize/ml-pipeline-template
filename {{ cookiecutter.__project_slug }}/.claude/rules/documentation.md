---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "docs/**/*.md"
  - "*.md"
---

Before writing a docstring, a comment, or a document, read and follow
@docs/conventions/python-documentation.md.

Budgets: a docstring is a summary line plus at most three lines of prose; a module
docstring is at most five lines; a file you create is under 25% comment and
docstring lines. `settings.py` is exempt from the ratio only.

Comments say what the code **is**, not how it got here. No research narrative —
that is a finding, and it belongs in the report.

A docstring or document asserting a fact is a claim you must defend against a
source you have actually read.
