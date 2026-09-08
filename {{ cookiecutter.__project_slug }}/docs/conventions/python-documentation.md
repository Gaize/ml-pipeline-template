# Documentation conventions

The base standard is the [Google Python Style Guide, §3.8](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
Where this file and the guide conflict, this file wins.

## The rules we enforce

- **A docstring is mandatory** for every function that is public, non-trivial, or
  has non-obvious logic. It must let a reader call the function without reading
  its body.
- **Format:** a one-line summary ending in a period, then a blank line, then
  elaboration and any `Args:`, `Returns:`, `Raises:` sections.
- **Default to the one-line docstring.** Add sections only for a parameter or
  return whose meaning a competent reader cannot get from the name, the type, and
  the summary. Units, invariants, mutation, and I/O qualify; restating the name
  does not.
- **`Returns:` may be omitted** when the function returns `None`, or when the
  summary line already starts with "Return" and describes the value.
- **Class docstrings describe what an instance is** ("The address of a shop."),
  not "Class that represents...".
- **Every module starts with a docstring.** Test modules only need one when there
  is something non-obvious to say.
- **Inline comments are for tricky code only.** Never describe what the code
  plainly does; assume the reader knows Python.

## Budgets

Documentation is code you cannot test. It has a cost, so it has a budget.

| Unit | Budget |
|---|---|
| One docstring | summary line + ≤ 3 lines of prose |
| One `Args:`/`Returns:`/`Raises:` entry | 1 line |
| One inline comment | ≤ 2 lines |
| Module docstring | ≤ 5 lines |
| Comment + docstring lines in a file you create | < 25% of non-blank lines |

Exceed three lines only to state a unit, an invariant, or a side effect the
caller cannot see from the signature. `settings.py` is exempt from the ratio,
because a docstring on every tunable is required; its docstrings still obey the
three-line budget.

Over budget is a defect, not a style preference. Fix it by deleting.

## Document behaviour, not the signature

The code is annotated, so **never restate a type**.

```python
# Bad
beta: float, the beta value.
# Good
beta: Weight on recall relative to precision; below 1 favours precision.
```

## Comments state what the code is, not how it got here

| Question | Where it belongs |
|---|---|
| What is this, and what does it do? | The comment |
| How did we get here, and why did we change it? | Git history, the PR |

**Red flags — rewrite in the present tense if you write any of these:**
"refactored", "improved", "better", "new", "old", "legacy", "previously", "used
to", "now", "moved from", "use this instead".

A comment that only makes sense to someone who remembers the change that
introduced it is history. Delete it.

## No research narrative in code

A comment states what the code is. It never walks through how a value was
determined, what was measured, or what the alternatives were. That is a
*finding*, and it belongs in the PR or the report — a durable place where it can
be revised. A finding pasted into source is read by everyone forever and revised
by no one.

Test: if the sentence answers "how do we know this?" rather than "what is this?",
it is a finding. Move it.

## A docstring is a claim you must be able to defend

When a docstring asserts a fact — what a threshold means, what a column contains —
a reader acts on it without reading the code. So it must be something you have
verified against the source, in this repository, on this branch.

If you cannot verify it, do not assert it. Describe what the code does with the
value instead. This matters most for values copied from elsewhere: a docstring
asserting a false meaning makes the value invisible, because every later reader
trusts it and stops looking.

## Cite authoritative sources, and only authoritative sources

When a comment makes a factual claim — a threshold, a formula, a definition —
cite published authority: peer-reviewed work, a standard, or official
documentation.

- **Cite the specific claim.** The citation sits next to the number it supports
  and must actually contain it.
- **Cite only what you read.** If you know a result because another paper cites
  it, credit the paper you read.
- **Conversations are not sources.** If the only backing is a discussion, either
  find the primary source or state it as a project decision without a borrowed
  citation.
- **A claim asserts something about the world and needs authority; a decision
  records a choice and needs only to name what it was based on.**

## Examples must be runnable

Any example in a docstring is real, copy-pasteable code that produces the stated
output. An untested example teaches the wrong thing with borrowed authority.

## Docs change in the same commit as the code

A stale docstring is a bug, not a follow-up.

## Before you commit

- [ ] Every docstring and comment is within budget.
- [ ] Every `Args:`/`Returns:` entry earns its place; nothing restates a type.
- [ ] Every docstring line is a complete sentence understandable without the body.
- [ ] No red-flag words; every comment says what the code is, not how it got here.
- [ ] Nothing answers "how do we know this?" — that is a finding, and it moves.
- [ ] Every factual assertion is verified against a source, or it is not asserted.
- [ ] Examples run as written.
