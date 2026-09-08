# Pipeline design

This document tells you what shape new code must have.

The function of each layer is in `docs/layers.md`. The rules for the cache and
for settings are in `python-coding.md`. The rules for logging are in
`observability.md`.

## Start from the flow of the data

A pipeline is a short sequence of stages. Write that sequence as one sentence
before you write code. For example: read the table, clean it, calculate the
features, search the parameters, score the rows, and report.

That sentence is the specification for `run()`. Each module and function that you
add must make the sentence easier to read.

## Four levels

1. **Pipeline** — a command-line program. Its body is the sequence of stages, one
   line for each stage. It has no other branches.
2. **Subpipeline** — `@subpipeline`. It joins steps together and uses no cache.
   Two programs that share a stage must call the same subpipeline.
3. **Step** — `@step`. One stage with a cache. It reads data or calculates a
   result for the full dataset.
4. **Calculation** — a function with no decorator.

Aftereffects operate on a `@step` or a `@subpipeline` only. On other functions
they do nothing.

## Call the library from the step

A step calls scikit-learn, numpy, or scipy directly. Do not write an adapter
around a library. The step is already the connection to the library.

Keep your own calculations in the step. Move a calculation into its own function
only if a second caller needs it, or if it is complex and needs its own test.

## Results are columns, not objects

A value that you calculate for each row becomes a column on the frame. The next
step reads the column, and the aftereffects can also read it. Do not make a list
of objects for results that a table can hold.

Use a class for configuration, for a contract, or for state. Do not use a class
for tabular results.

## A step that removes rows must report the removals

`intermediate_to_primary` returns the rows that remain and a `FilterChain`. Give
the record of the removals as data, and not as a log message. An aftereffect can
then report it at each run.

## The model gives a score. A different layer makes the decision

L06 gives `y_score`. L08 applies the threshold. An estimator with no threshold is
easier to use again, and you can change the threshold without a new fit.

## Each configurable value is a settings field and a step argument

Put each configurable value in `settings.py` with a docstring. Give it to the
top-level step as an argument with a default. Do not read `settings.foo` in a
step body: this is a cache defect. See `python-coding.md`.

Use `@computed_field` for values that must agree with each other. Put related
values in a nested block.

## A constant is calculated or it is a stated assumption

Calculate a constant from the data or from first principles, and it explains
itself. If you must select a number, put it in `settings.py`. Write in the
docstring that it is a selection.

## Put a cache on each read and each calculation

A data read is a step with a cache, like all other steps. If the result of a step
depends on code that its arguments do not describe, make a hash of that code and
give the hash to the step. `architecture_fingerprint()` does this.

## Before you write code

1. Write the flow of the data as one sentence. `run()` must read like it.
2. Look for a step or a function that already does the work.
3. Select the level for each part: pipeline, subpipeline, step, or calculation.
4. Make each configurable value a settings field and a step argument.
5. Make per-row results into columns.

## The test

Read `run()` from the first line to the last. If a module, a wrapper, or a class
does not make the sentence easier to read, remove it.
