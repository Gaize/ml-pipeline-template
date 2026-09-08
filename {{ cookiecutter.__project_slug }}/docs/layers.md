# The layers

The pipeline is eight numbered modules in `src/pipeline/common/`, run in order.
The numbering follows [Kedro's layered data engineering
convention](https://docs.kedro.org/en/stable/faq/faq.html#what-is-data-engineering-convention).
Each layer answers one question about how far the data has come.

| Layer | Module | What lives here |
|---|---|---|
| L01 Raw | `l01_raw.py` | Load the source table unchanged. |
| L02 Intermediate | `l02_intermediate.py` | Type it, and derive the columns later layers need. |
| L03 Primary | `l03_primary.py` | Drop what cannot be modelled; record what was dropped. |
| L04 Feature | `l04_feature.py` | Compute features. No labels. |
| L05 Model input | `l05_model_input.py` | Join features to labels and groups. |
| L06 Models | `l06_models.py` | Define, search, and fit the estimator. |
| L07 Model output | `l07_model_output.py` | Score every row out of fold. |
| L08 Reporting | `l08_reporting.py` | Metrics, threshold, figures. |

`explore.py` calls them in that order, and its body is the whole experiment.

## Layer roles are not interchangeable

The most common way this structure decays is doing work one layer early because
it is convenient there.

- **L01 loads. It does not filter, enrich, or cast.** Keeping it narrow keeps its
  cache key stable, so editing a later layer never re-reads the source.
- **L02 is where typing and derivation happen.** The group column is derived here,
  so every layer below sees the same frame whether grouping is on or off.
- **L03 drops rows and columns**, and returns a `FilterChain` recording what each
  rule removed. "Where did my data go?" is answered before anyone asks.
- **L04 produces features and never sees the label.** A feature computed from the
  target is the fastest way to a score that means nothing.
- **L07 runs the model. It does not train one** — that is L06 — **and it does not
  evaluate** — that is L08.

If you are working in the wrong layer because it is easier, move it.

## Where to add things

| You want to | Edit |
|---|---|
| Read a different dataset | `settings.data_path`, and `l02_intermediate.py` if the label or group needs deriving |
| Add a feature | `features.py` |
| Drop bad rows | `l03_primary.py` |
| Change the model or its grid | `make_estimator` and `PARAM_GRID` in `l06_models.py` |
| Change how folds are made | `settings.group_col`, `settings.training` |
| Add a metric or figure | `reporting.py`, then wire it into `build_reporting` |

## Steps, subpipelines, and computes

Four levels, and the level decides whether a thing is cached and whether its
aftereffects run.

1. **Pipeline** — the CLI (`explore.py:run`). Its body is the dataflow: one line
   per stage, in layer order.
2. **Subpipeline** — `@subpipeline`. Composes steps and caches nothing. Its
   aftereffects fire on every call, which is why cross-step reporting lives here.
3. **Step** — `@step`. One cached stage. Defaults sit on the top-level step only.
4. **Compute** — undecorated maths. The step is the seam between the pipeline and
   the library.

### Defaults belong on the top-level step

KissML caches a step's return value by hashing its arguments. A value read from
`settings` inside a body never moves the hash, so the cache will not invalidate
when you change it.

```python
# Correct — the default is on the step, so changing it re-keys the cache
@step_decorator
def load_raw(data_path: Path = settings.data_path) -> pd.DataFrame: ...

# Wrong — the cache cannot see this setting change
@step_decorator
def load_raw() -> pd.DataFrame:
    return pd.read_csv(settings.data_path)
```

When a step's output depends on code its arguments do not describe — the
estimator definition, the feature code — hash that source and pass it in.
`architecture_fingerprint()` and `source_fingerprint()` do this.

## Out-of-fold scoring, and the two models

L07 scores each row with a model fitted on the folds that excluded it. Those are
the scores L08 evaluates, so the reported number is not a model grading its own
training data.

`--submit` fits a *second* model, on every row, using the same hyperparameters.
That is the model you would ship. It has no honest score of its own, which is
exactly why the two live in different places.

## Reading a run

Every layer writes its artifacts under its own prefix — `01_raw/`,
`04_feature/`, `08_reporting/`. Because the logging happens in aftereffects
rather than step bodies, a fully-cached rerun still produces a complete MLflow
run.
