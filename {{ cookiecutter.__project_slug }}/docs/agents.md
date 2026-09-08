# The agent-facing surface

This repository is built to be worked on by a coding agent. That is a claim
about its structure, not a feature you switch on. Four things do the work.

## 1. Conventions load themselves

Each file in `.claude/rules/` lists path patterns in its frontmatter under
`paths:`. Editing `src/pipeline/common/l04_feature.py` loads the pipeline-design
and coding conventions into context; editing a test loads the testing rules. The
agent does not have to remember to read them, and you do not have to paste them.

The consequence: **a convention that is not written down does not exist.** If you
correct the agent twice on the same thing, the correction belongs in
`docs/conventions/`, not in the next prompt.

## 2. The lint hook closes the loop

`.claude/hooks/lint-python.sh` runs on every write to a `.py` file: ruff format,
ruff check --fix, import sort, and `ty`. Any of the four failing exits 2, which
returns the output to the agent in the same turn, attached to the edit that
caused it.

It deliberately skips the unused-import rule (F401), because stripping an import
mid-edit breaks code the agent is halfway through writing. `just lint-check`
catches those.

## 3. Aftereffects make a cached run legible

An agent iterating on an experiment will re-run the pipeline many times, and most
steps will hit cache. If logging lived inside step bodies, the second run would
produce an empty MLflow run and the agent would conclude nothing happened.

Aftereffects run whenever a value is materialized, **including from cache**, so
every run is fully populated regardless of how much was reused. This is the
single most important thing to preserve when you extend the pipeline.

The trap: an aftereffect on an undecorated function is inert. It type-checks, it
raises nothing, and it never runs. `tests/common/test_effects.py` walks the AST
and fails if one is misplaced, because nothing else would tell you.

## 4. HYPOTHESIS.md is the goal the agent checks itself against

An agent given "improve the model" will improve the number it is shown. An agent
given a hypothesis, a metric, a baseline, and a stated bar can tell whether it is
finished — and can report a negative result instead of manufacturing a positive
one.

Write down what would change your mind before you start.

## Building on this

The scaffold runs one experiment when you invoke it. Making it autonomous — read
the hypothesis, decide what to try, run it, read the result, decide what to try
next, and stop when the bar is met or the ideas run out — is the part left to
you.

Some things worth knowing before you start:

- **MLflow is queryable.** `mlflow.search_runs()` returns a DataFrame of every
  run with its parameters and metrics. That is how a loop reads its own history
  instead of re-deriving it.
- **The cache makes iteration cheap, and lies if you let it.** `features.py` and
  the estimator are fingerprinted, so editing them re-keys the cache. Code they
  call is not: a step whose result depends on something its arguments do not
  describe returns the old answer at full speed until you fingerprint that too.
- **A run without a `git_hash` tag has no code it can be traced to** — the tree
  was dirty, or was not a git repository. Do not treat it as evidence.
- **The permutation test asks a narrow question.** It shuffles the labels against
  fixed out-of-fold scores, so it tests whether the ranking beats chance. Its null
  sits at 0.5 whether or not the split leaks, because nothing refits. Detecting
  leakage this way needs a different test: permute the labels and re-run the whole
  cross-validation, and watch the null rise above chance.
