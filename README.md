# ml-pipeline-template

A cookiecutter template for machine-learning experiments. A coding agent can work
in the pipeline that it makes.

Each generated pipeline runs from start to end on a supplied dataset. It has
eight numbered layers, cached steps, cross-validated hyperparameter search,
out-of-fold scoring, and an MLflow run with metrics and figures.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)
- [cookiecutter](https://cookiecutter.readthedocs.io/) — install it with
  `uv tool install cookiecutter`

## Make a pipeline

Run cookiecutter on a clone of this repository. Start in the directory where you
want the pipeline.

```bash
cookiecutter ~/repos/ml-pipeline-template
```

Cookiecutter asks for a project name and a description. It makes a directory with
a virtualenv. Go into the directory and run the experiment.

```bash
cd my-experiment
just explore
just mlflow-ui
```

Make one pipeline for each idea. Each pipeline keeps its own environment, its own
cache, and its own MLflow experiment. An experiment that you ran last week
therefore runs again correctly.

## Contents of a generated pipeline

| Path | Description |
|---|---|
| `src/pipeline/common/l0*.py` | The eight layers, L01 Raw to L08 Reporting |
| `src/pipeline/explore/explore.py` | The experiment, from start to end |
| `src/pipeline/settings.py` | Each configurable value, with a docstring |
| `HYPOTHESIS.md` | The question, the approach, and the test that can fail it |
| `docs/layers.md` | The function of each layer, and where to add code |
| `docs/agents.md` | The parts that a coding agent uses |
| `docs/conventions/` | The rules that the code obeys |
| `.claude/` | Rules for each path, and a lint hook |

## The supplied dataset

The Oxford Parkinson's Disease Detection dataset from UCI (CC BY 4.0, 195 rows).
A new pipeline can therefore run immediately.

The dataset also shows why the split must use groups. Each of the 32 subjects
made six or seven recordings, and the subject key is inside a text column. If the
split ignores subjects, the model can identify the speaker and not the condition.
The ROC AUC is 0.844 with subject groups and 0.909 without them.

Read `data/ATTRIBUTION.md` in a generated pipeline for the sources.

To use your own data, set `settings.data_path`.

## License

This repository has no license yet.

Two conditions apply. A generated pipeline uses
[KissML](https://github.com/lou-k/kissml), which has a CC BY-NC-ND 4.0 license.
The supplied dataset has a CC BY 4.0 license and needs attribution.
