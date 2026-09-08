# Observability

The goal: a run produces useful signal **even when every step hits cache**.
Silent cached steps are how observability quietly rots.

## Use aftereffects, not inline logging

**Logging inside a `@step` body only runs when the step actually executes.** On a
cache hit you see nothing. An aftereffect is a callback attached to a step's
return annotation that runs whenever the value is materialized, cache included.

```python
# Bad — fires only on a cache miss
@step_decorator
def join_features_and_labels(...) -> pd.DataFrame:
    logger.info("class distribution: %s", out[target_col].value_counts())
    return out

# Good — runs on every materialization
@step_decorator
def join_features_and_labels(...) -> Annotated[
    pd.DataFrame, ClassBalanceLogger(L_PRE, settings.target_col)
]:
    return out
```

Use them for class balance, row counts, filter survival, MLflow artifacts, and
any "what just happened" summary the user wants regardless of cache state.

**An aftereffect on a plain function is inert.** It type-checks, raises nothing,
and never runs. `tests/common/test_effects.py` guards against this, because
nothing else would tell you.

## MLflow artifacts even on a cache hit

If a step logs its metrics inside its body, a cached rerun produces an empty
MLflow run. Move metric and artifact logging into an aftereffect that takes the
returned value. The tracking surface is then always populated, however much was
reused.

## Multi-step reporting belongs on the subpipeline

An aftereffect sees one function's return value. A visualization that needs data
from several steps goes on the subpipeline that returns them — its effects see
the whole result and fire on every call, because a subpipeline is never cached.

## Prefer tqdm to per-iteration logging

For any loop with a non-trivial iteration count — folds, search iterations —
use `tqdm`, not `logger.info`.

1. **Always set `total=`** so the bar can show an ETA.
2. **Gate it behind a `show_progress: bool = False` argument** on the top-level
   step. Progress bars are good interactively and noise everywhere else; the
   caller decides.

## Filtering observability

When something drops rows, **log how many survived each rule**, not just the final
count. "Where did all my data go?" is the most common debugging question — answer
it before it is asked. That is what `FilterChain` and `FilterReportEffect` are for.

## Don't couple observability into business logic

If an observability change requires restructuring a step's return type or adding
a parameter that exists only for logging, stop and use an aftereffect. Logging
should be additive; the code path should not know it is being watched.
