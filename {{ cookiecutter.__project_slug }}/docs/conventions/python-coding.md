# Python coding conventions

## Return the natural value

Return the value itself. Do not put one value in a dictionary. Use a dictionary
only if two or more callers read different fields.

```python
# Incorrect
def to_model_input(frame) -> dict:
    return {"X": X, "y": y, "groups": groups}

# Correct. A named tuple gives the caller the names.
def to_model_input(frame) -> ModelInput:
    return ModelInput(X=X, y=y, groups=groups)
```

Do not return an input value. If the caller supplied the parameters, the caller
already has them.

## Give each function a full set of type hints

Each function has types for all arguments and for the result. There is no
exception for an obvious type. The lint hook runs `ty`, which finds these.

## Default values belong on the top-level step

KissML makes the cache key from the arguments of the step. Each configurable
value is therefore an argument of the top-level step, with a default from
`settings`. A step below the top level receives all values from its caller, and
it has no defaults.

```python
# Correct. The default is an argument, so a change to it clears the cache.
@step_decorator
def load_raw(data_path: Path = settings.data_path) -> pd.DataFrame: ...

# Incorrect. A settings value that the body reads does not change the cache key.
@step_decorator
def load_raw() -> pd.DataFrame:
    return pd.read_csv(settings.data_path)
```

A change to a setting changes the argument hash of the top-level step. This
clears the cache for all steps below it. A default on a lower step stops this.

## Configuration is in settings.py

Each configurable value is in `settings.py` with a docstring. The docstring says
what the value controls and what a change does. Do not put a special number in a
function signature. Do not put a constant in a layer file.

## Get a constant from its source

A setting that describes the data, the instrument, or the task must have a
source. Name that source in the docstring.

A value from another project is not a source. You get its history, but you do not
get its accuracy. If you cannot find a source, write in the docstring that the
value is a selection.

If the same constant is in two places, one of them is incorrect. Write a test
that shows the two values agree.

## Do not send optional inputs through all layers

If an optional input changes the behaviour of L02 only, use it in L02. Do not put
it in the signature of a layer below L02. Each layer below must look the same as
it looks when the option is off.

## Imports are at the top of the file

Put all imports at the top of the module. There is one exception: an optional
dependency. Import an optional dependency in the function that needs it, and give
a clear error if it is absent.

Do not use a local import to correct a circular import. A circular import shows a
problem in the structure. Correct the structure.

## Do not leave a TODO without a related issue

Do the work, or write the issue that will do it. A TODO with no issue usually
means "I saw this and I did not do it". Make that decision visible.

## Change a signature with care

- For each new argument, name the caller that uses it. If no caller uses it, do
  not add it.
- For each argument that you remove, make sure that no caller needs it.

A function signature is a contract.
