# The layers

The pipeline has eight numbered modules in `src/pipeline/common/`. They run in
order. The numbers agree with the [Kedro data engineering
convention](https://docs.kedro.org/en/stable/faq/faq.html#what-is-data-engineering-convention).
Each layer answers one question about the condition of the data.

| Layer | Module | Contents |
|---|---|---|
| L01 Raw | `l01_raw.py` | Reads the source table without changes. |
| L02 Intermediate | `l02_intermediate.py` | Sets the types and makes the necessary columns. |
| L03 Primary | `l03_primary.py` | Removes data that the model cannot use, and records what it removed. |
| L04 Feature | `l04_feature.py` | Calculates the features. It does not use the label. |
| L05 Model input | `l05_model_input.py` | Joins the features to the labels and the groups. |
| L06 Models | `l06_models.py` | Defines the estimator, searches its parameters, and fits it. |
| L07 Model output | `l07_model_output.py` | Gives each row an out-of-fold score. |
| L08 Reporting | `l08_reporting.py` | Calculates the metrics and makes the figures. |

`explore.py` calls the layers in this order. Its body is the full experiment.

## Do not do work in the wrong layer

This structure fails when you do work one layer too early, because it is easier
there.

- **L01 reads the data. It does not filter, add, or convert.** A small L01 keeps
  its cache key stable, so an edit to a later layer does not read the source
  again.
- **L02 sets the types and makes the derived columns.** It makes the group
  column. All layers below L02 therefore get the same frame.
- **L03 removes rows and columns.** It returns a `FilterChain` that records the
  effect of each rule.
- **L04 makes the features and does not use the label.** A feature that comes
  from the label gives a score with no meaning.
- **L07 runs the model. L06 trains it, and L08 measures it.**

If you work in the wrong layer because it is easier, move the code.

## Where to make a change

| Objective | File to edit |
|---|---|
| Read a different dataset | `settings.data_path`, and `l02_intermediate.py` if the label or the group needs a calculation |
| Add a feature | `features.py` |
| Remove bad rows | `l03_primary.py` |
| Change the model or its grid | `make_estimator` and `PARAM_GRID` in `l06_models.py` |
| Change the folds | `settings.group_col` and `settings.training` |
| Change the operating threshold | `settings.reporting.threshold` |
| Add a metric or a figure | `reporting.py`, then `build_reporting` |

## Steps, subpipelines, and calculations

There are four levels. The level controls the use of the cache, and it controls
whether the aftereffects run.

1. **Pipeline** — the command-line program (`explore.py:run`). Its body is the
   sequence of layers, one line for each stage.
2. **Subpipeline** — `@subpipeline`. It joins steps together and uses no cache.
   Its aftereffects run at each call.
3. **Step** — `@step`. One stage, with a cache. Only the top-level step has
   default values.
4. **Calculation** — a function with no decorator. The step connects the pipeline
   to the library.

### Default values belong on the top-level step

KissML makes the cache key from the arguments of the step. A value that the body
reads from `settings` is not an argument. The cache therefore does not clear when
you change that value.

```python
# Correct. The default is an argument, so a change clears the cache.
@step_decorator
def load_raw(data_path: Path = settings.data_path) -> pd.DataFrame: ...

# Incorrect. The cache cannot see this change.
@step_decorator
def load_raw() -> pd.DataFrame:
    return pd.read_csv(settings.data_path)
```

If the result of a step depends on code that the arguments do not describe, make
a hash of that code and give it to the step. `architecture_fingerprint()` and
`source_fingerprint()` do this.

## Out-of-fold scores, and the two models

L07 gives each row a score from a model that did not use that row. L08 measures
these scores. The reported value is therefore not a measurement of the training
data.

`--submit` fits a second model on all rows with the same parameters. This is the
model that you would deliver. It has no score of its own. For this reason the two
models are in different places.

## To read a run

Each layer writes its artifacts under its own prefix: `01_raw/`, `04_feature/`,
`08_reporting/`. Aftereffects write these artifacts, and not the step bodies. A
run that uses the cache is therefore complete.
