# Observability

A run must give useful information, and this includes a run where each step uses
the cache. Steps that use the cache and give no information make the pipeline
difficult to examine.

## Use aftereffects, not log statements

A log statement in a `@step` body runs only when the step runs. On a cache hit
you see nothing. An aftereffect is a callback on the return annotation of a step.
It runs each time the value becomes available, and this includes a value from the
cache.

```python
# Incorrect. This runs only on a cache miss.
@step_decorator
def join_features_and_labels(...) -> pd.DataFrame:
    logger.info("class distribution: %s", out[target_col].value_counts())
    return out

# Correct. This runs each time the value becomes available.
@step_decorator
def join_features_and_labels(...) -> Annotated[
    pd.DataFrame, ClassBalanceLogger(L_PRE, settings.target_col)
]:
    return out
```

Use an aftereffect for the class balance, the row counts, the survival of a
filter, the MLflow artifacts, and each summary that the user needs.

An aftereffect on a function with no decorator does nothing. It passes the type
check and it does not run. `tests/common/test_effects.py` finds this error.

## MLflow artifacts on a cache hit

If a step writes its metrics in its body, a run that uses the cache gives an
empty MLflow run. Put the metrics and the artifacts in an aftereffect that reads
the returned value. The MLflow run is then always complete.

## A report on more than one step belongs on the subpipeline

An aftereffect reads the result of one function. If a figure needs data from more
than one step, put the aftereffect on the subpipeline that returns them. A
subpipeline has no cache, so its aftereffects run at each call.

## Use tqdm, not a log statement in a loop

For a loop with many iterations, use `tqdm`.

1. Always set `total=`, so that the bar can show the remaining time.
2. Control it with a `show_progress: bool = False` argument on the top-level
   step. A progress bar is useful for a person and not useful in a log file.

## Report the effect of a filter

When code removes rows, report how many rows each rule removed. Do not report the
final count only. "Where did the data go?" is the usual question, and
`FilterChain` and `FilterReportEffect` answer it.

## Keep observability out of the logic

If a change to the reporting needs a different return type, or a new parameter
that only the logging uses, stop. Use an aftereffect. The code must not know that
you examine it.
