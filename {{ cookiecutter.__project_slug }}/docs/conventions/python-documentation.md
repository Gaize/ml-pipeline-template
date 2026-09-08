# Documentation conventions

The base standard is the [Google Python Style Guide,
§3.8](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
If this file and that guide disagree, obey this file.

Write all documents in simple English. Use short sentences. Use the active voice.
Use one idea in each sentence. Do not use idioms or figures of speech.

## The rules

- **A docstring is necessary** for each function that is public, complex, or not
  obvious. A reader must be able to call the function without a read of its body.
- **The format** is one summary line that ends with a period, then an empty line,
  then more text and the sections `Args:`, `Returns:`, and `Raises:`.
- **Use one line if one line is sufficient.** Add a section only for an argument
  or a result that the name and the type do not explain. A unit, a limit, or an
  effect on other data is sufficient reason. A repeat of the name is not.
- **You can omit `Returns:`** if the function returns `None`, or if the summary
  line starts with "Return" and describes the value.
- **A class docstring says what the object is.** Write "The address of a shop.",
  not "Class that represents an address."
- **Each module starts with a docstring.** A test module needs one only if it has
  something that is not obvious.
- **Write a comment only for code that is difficult.** Do not describe code that
  a reader can read.

## Limits

Documentation is code that you cannot test. It has a cost, and therefore it has a
limit.

| Item | Limit |
|---|---|
| One docstring | The summary line and 3 lines of text |
| One `Args:`, `Returns:`, or `Raises:` entry | 1 line |
| One comment | 2 lines |
| A module docstring | 5 lines |
| Comments and docstrings in a new file | Less than 25% of the lines that are not empty |

Use more than 3 lines only to give a unit, a limit, or an effect that the
signature does not show. `settings.py` does not obey the 25% limit, because each
value must have a docstring. Its docstrings obey the 3-line limit.

More text than the limit is a defect. Correct it with a deletion.

## Describe the behaviour, not the signature

The code has type annotations. Do not repeat a type.

```python
# Incorrect
alpha: float, the alpha value.
# Correct
alpha: The total probability outside the interval. 0.05 gives 95% bounds.
```

## A comment says what the code is

| Question | Location of the answer |
|---|---|
| What is this, and what does it do? | The comment |
| How did the code get here, and why did it change? | The git history and the pull request |

Do not use these words in a comment: "refactored", "improved", "better", "new",
"old", "legacy", "previously", "used to", "now", "moved from", "use this
instead". A comment that only a person who saw the change can understand is
history. Delete it.

## Do not put research in the code

A comment says what the code is. It does not say how you found a value, what you
measured, or what the other options were. That information is a result, and it
belongs in the report or the pull request. A result in the source code goes to
each reader, and nobody corrects it.

Test: if the sentence answers "how do we know this?", it is a result. Move it.

## A docstring is a statement that you must be able to prove

If a docstring states a fact, a reader uses that fact and does not read the code.
You must therefore prove the fact against the source, in this repository, on this
branch.

If you cannot prove it, do not state it. Describe what the code does with the
value. This is most important for a value that you copied. A docstring with an
incorrect meaning hides the value, because each later reader trusts it.

## Give a source, and give only a good source

If a comment states a fact — a limit, a formula, or a definition — give the
source. Use published work, a standard, or official documentation.

- **Give the source of the specific fact.** The reference is next to the value,
  and it must contain that value.
- **Give only a source that you read.** If you know a result because another
  paper mentions it, name the paper that you read.
- **A conversation is not a source.** If a discussion is the only support, find
  the primary source, or write that it is a project decision.
- **A fact needs a source. A decision needs only the reason for it.**

## An example must run

Each example in a docstring is real code that gives the result that you state. An
example that does not run teaches an error.

## Change the documentation in the same commit as the code

A docstring that is not correct is a defect.

## Before you commit

- [ ] Each docstring and comment is inside the limits.
- [ ] Each `Args:` and `Returns:` entry is necessary, and none repeats a type.
- [ ] Each docstring line is a complete sentence.
- [ ] No comment uses a word from the list above.
- [ ] No comment answers "how do we know this?".
- [ ] Each stated fact has a source, or you removed the statement.
- [ ] Each example runs.
