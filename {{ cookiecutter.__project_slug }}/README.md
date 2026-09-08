# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Setup

You must have [uv](https://docs.astral.sh/uv/) and
[just](https://github.com/casey/just).

```bash
just sync
just explore
```

`just explore` runs the experiment on the supplied dataset. It writes the results
to a local MLflow store. To read the results:

```bash
just mlflow-ui
```

## Commands

| Command | Description |
|---|---|
| `just sync` | Installs the virtualenv from the lockfile. |
| `just explore` | Runs the experiment from start to end. |
| `just explore --submit` | Also fits on all rows and writes a prediction file. |
| `just mlflow-ui` | Shows the runs at http://localhost:5000. |
| `just test` | Runs the tests. |
| `just lint` | Formats the code, corrects it, and checks the types. |
| `just lint-check` | Reports problems, but does not change the files. |

For the run options, use `just explore --help`.

## Configuration

Each configurable value is in `src/pipeline/settings.py` with a docstring. To
change a value, set an environment variable with the prefix `PIPELINE_`, or use a
`.env` file. See `.env.example`.

```bash
# Read a different table, and treat its rows as independent.
PIPELINE_DATA_PATH=data/your_table.csv PIPELINE_GROUP_COL= just explore
```

An empty value means "not set". `PIPELINE_GROUP_COL=` therefore stops the use of
groups.

## Where to start

- `HYPOTHESIS.md` — the question that this experiment answers. Complete it first.
- `docs/layers.md` — the function of each of the eight layers.
- `docs/agents.md` — the parts that a coding agent uses.
- `docs/conventions/` — the rules that the code obeys.

## License

This pipeline has no license yet. The dataset in `data/` has a CC BY 4.0 license
and needs attribution. See `data/ATTRIBUTION.md`.
