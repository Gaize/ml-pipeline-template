# Python coding conventions

## Return the natural value

**Return the single natural value. Do not wrap it in a dict unless two or more
callers need different fields.**

```python
# Bad
def to_model_input(frame) -> dict:
    return {"X": X, "y": y, "groups": groups}

# Good — a named tuple the caller can unpack
def to_model_input(frame) -> ModelInput:
    return ModelInput(X=X, y=y, groups=groups)
```

**Do not echo inputs back in the return value.** If the caller passed the
hyperparameters in, the caller already has them.

## Type hints everywhere

**Every function has fully-typed arguments and return.** No exceptions for
"obvious" types. `ty` enforces this in the lint hook.

## Defaults belong on the top-level step

**KissML caches a step's return value by hashing its arguments.** Every
configurable value is a parameter of the **top-level step**, defaulted from
`settings`. Sub-steps take everything explicitly and carry no defaults.

```python
# Correct — the default is on the top-level step
@step_decorator
def load_raw(data_path: Path = settings.data_path) -> pd.DataFrame: ...

# Wrong — a settings read inside the body never moves the cache key
@step_decorator
def load_raw() -> pd.DataFrame:
    return pd.read_csv(settings.data_path)
```

When a setting changes, the top-level step's argument hash changes, which
invalidates the whole chain below it. Defaults on sub-steps silently break this.

## Configuration lives in settings.py

**Every tunable lives in `settings.py` with a docstring** explaining what it
controls and what turning it on implies. Never a magic literal in a signature,
never a module-level constant in a layer file.

## A constant that describes the world is sourced, not inherited

A setting that asserts something about the data, the instrument, or the task must
be traceable to the artifact that defines it, and the docstring names that
artifact.

**Copying a value from another project is not a source.** You inherit its
provenance, not its correctness. If you cannot source it, say in the docstring
that it is a choice — a constant you cannot source is a finding you have not made
yet.

**If the same constant appears twice, one of them is wrong.** Assert they agree,
in a test.

## Don't thread optional inputs through every layer

If an optional input only changes behaviour at L02, resolve it at L02 and do not
carry it through every downstream signature. Every layer below the one that cares
should look identical to the case where the flag is off.

## Imports go at the top

**All imports belong at the top of the module.** The only exception is a genuinely
optional dependency, imported lazily with a clear error if it is missing. Do not
use local imports to break circular imports — that is a design smell; fix the
structure.

## No TODO comments without a tracked follow-up

Either do the work, or name the issue that will. A bare `TODO` almost always means
"I noticed this and chose not to do it" — make that decision explicit.

## Diff hygiene for signature changes

- **For every added argument, name the call site that uses it.** If nothing calls
  it, do not add it.
- **For every removed argument, confirm no caller depends on it.**

Function signatures are contracts. Change them deliberately.
