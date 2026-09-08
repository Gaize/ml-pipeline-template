# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

## Setup

Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

```bash
just sync
just explore
```

`just explore` runs the whole experiment on the bundled dataset and logs it to a
local MLflow store. To read the results:

```bash
just mlflow-ui
```

## Commands

| Command | What it does |
|---|---|
| `just sync` | Install the virtualenv from the lockfile. |
| `just explore` | Run the experiment end to end. |
| `just explore --submit` | Also fit on every row and write a prediction file. |
| `just mlflow-ui` | Browse runs at http://localhost:5000. |
| `just test` | Run the test suite. |
| `just lint` | Format, fix, sort imports, and type check. |
| `just lint-check` | Report failures without changing files. |

`just explore --help` lists the run options.

## Configuration

Every tunable lives in `src/pipeline/settings.py` with a docstring. Override any
of them with a `PIPELINE_`-prefixed environment variable or a `.env` file; see
`.env.example`.

```bash
# Read a different table, and treat its rows as independent.
PIPELINE_DATA_PATH=data/your_table.csv PIPELINE_GROUP_COL= just explore
```

An empty value means unset, so `PIPELINE_GROUP_COL=` turns grouping off.

## Where to start

- `HYPOTHESIS.md` — what this experiment is testing. Fill it in first.
- `docs/layers.md` — what each of the eight layers is for and where to add code.
- `docs/agents.md` — the agent-facing surface of this repository.
- `docs/conventions/` — the rules the code follows, loaded automatically when
  editing matching files.

## License

Not yet licensed. The bundled dataset in `data/` is CC BY 4.0 and carries its own
attribution — see `data/ATTRIBUTION.md`.
