---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "docs/**/*.md"
  - "*.md"
---

Before you write a docstring, a comment, or a document, read and obey
@docs/conventions/python-documentation.md.

Write in simple English. Use short sentences and the active voice. Use one idea
in each sentence.

Limits: a docstring is a summary line and 3 lines of text. A module docstring is
5 lines. A new file has less than 25% comment and docstring lines. Only
`settings.py` does not obey the 25% limit.

A comment says what the code is, and not how it got there. Do not put research in
the code. That is a result, and it belongs in the report.

If a docstring or a document states a fact, you must be able to prove the fact
against a source that you read.
