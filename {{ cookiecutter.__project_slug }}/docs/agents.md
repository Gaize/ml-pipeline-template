# Notes for a coding agent

Four mechanisms in this repository help an agent to do correct work.

**Rules load automatically.** Each file in `.claude/rules/` lists path patterns
under `paths:`. An edit to a file that matches a pattern loads the related
conventions. A rule that nobody writes down does not exist. If you correct the
agent twice about one subject, add the correction to `docs/conventions/`.

**The lint hook reports errors immediately.** `.claude/hooks/lint-python.sh` runs
after each write to a `.py` file. It runs ruff format, ruff check, the import
sort, and `ty`. If one of them fails, the hook exits with status 2 and the agent
receives the output. The hook does not apply rule F401, because the removal of an
unused import can break code that is not complete. `just lint-check` finds those.

**Aftereffects keep a cached run complete.** An agent runs the pipeline many
times, and most steps use the cache. Log statements inside a step body run only
on a cache miss, so a second run would give an empty MLflow run. Aftereffects run
each time a value is made available, and this includes values from the cache.
Keep this behaviour when you add code.

An aftereffect on a function without a decorator does nothing. It passes the type
check and it does not run. `tests/common/test_effects.py` reads the syntax tree
and fails if an aftereffect is in the wrong place.

**`HYPOTHESIS.md` gives the agent a goal.** An agent that receives the
instruction "make the model better" makes the number better. An agent that
receives a question and a condition that can fail it can decide when it is
finished, and it can report a negative result.

## To make the pipeline autonomous

The pipeline runs one experiment for each command. To run experiments without a
person, the agent must read the hypothesis, select a change, run it, read the
result, and stop. This part is your work.

- `mlflow.search_runs()` gives a DataFrame of all runs with their parameters and
  metrics. Use it to read the history of the loop.
- The cache makes each run fast, but it can give an old result. `features.py` and
  the estimator have fingerprints, so an edit to them clears the cache. Code that
  they call does not have a fingerprint.
- A run without a `git_hash` tag has no known source code. The tree was not
  clean, or the directory is not a git repository. Do not use that run as
  evidence.
- The permutation test answers one question only. It shuffles the labels against
  fixed out-of-fold scores, so it shows if the order of the scores is better than
  chance. Its null value stays at 0.5 even if the split is incorrect.
