# ml-pipeline-template

A scaffold for reproducible machine-learning experiments, built to be worked on
by a coding agent.

`cookiecutter` this repository and you get a pipeline that runs end to end on a
bundled dataset: eight numbered layers, cached steps, cross-validated
hyperparameter search, out-of-fold scoring, and a full MLflow run with metrics,
figures, a learning curve, and a permutation test.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- [cookiecutter](https://cookiecutter.readthedocs.io/) — `uv tool install cookiecutter`

## Create a pipeline

Run cookiecutter against a clone of this repository, from wherever you want the
pipeline to live:

```bash
cookiecutter ~/repos/ml-pipeline-template
```

You are asked for a project name and a one-line description. The result is a
directory named for today's date and your project — `2026-09-04-my-experiment` —
with its own virtualenv, already synced. Enter it and run the experiment:

```bash
cd 2026-09-04-my-experiment
just explore
just mlflow-ui
```

One idea, one pipeline. Scaffold a new one for the next idea rather than editing
the last one — each keeps its own environment, its own cache namespace, and its
own MLflow experiment, so an experiment you ran last week still reproduces.

## What is in a generated pipeline

| Path | What it is |
|---|---|
| `src/pipeline/common/l0*.py` | The eight layers, L01 Raw through L08 Reporting |
| `src/pipeline/explore/explore.py` | The experiment: the dataflow, top to bottom |
| `src/pipeline/settings.py` | Every tunable, each with a docstring |
| `HYPOTHESIS.md` | What the experiment tests, and what would count as an answer |
| `docs/layers.md` | What each layer is for and where to add code |
| `docs/agents.md` | The agent-facing surface, and what to preserve |
| `docs/conventions/` | The rules the code follows |
| `.claude/` | Path-scoped rules and a lint hook |

## The bundled dataset

The Oxford Parkinson's Disease Detection dataset from UCI (CC BY 4.0, 195 rows).
It is here so a fresh pipeline runs immediately, and because it teaches
something: each of its 32 subjects contributed six or seven recordings, and the
subject key is hidden inside a string column rather than given as its own. A
split that treats rows as independent lets the model recognise the speaker
instead of the condition.

Because several rows describe one speaker, `group_col` is `subject` and there is
no second option. Run it ungrouped and ROC AUC rises from **0.844** to **0.909** —
not a better model, the same model scored on people it has already heard. See the
generated `data/ATTRIBUTION.md` for the sources and the published critique.

Point `settings.data_path` at your own data when you have some.

## License

Not yet licensed.

Two things to settle before one is chosen: generated pipelines depend on
[KissML](https://github.com/lou-k/kissml), which is CC BY-NC-ND 4.0
(non-commercial, no derivatives), and the bundled dataset is CC BY 4.0 with its
own attribution in `data/ATTRIBUTION.md`.
