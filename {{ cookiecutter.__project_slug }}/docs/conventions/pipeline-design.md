# Pipeline design

The design contract for pipeline code. It answers *what shape should this take?*

Layer roles are in `docs/layers.md`; cache-key and settings mechanics are in
`python-coding.md`; logging is in `observability.md`.

## Design forward from the dataflow

**A pipeline is a short sequence of named stages. Write that sequence as one
sentence before you write code** — *load the table → clean it → compute features
→ tune → score out of fold → report* — because it is the specification for
`run()`.

Every module and function you add exists to make that sequence easy to read at
the entry point. Decide the stages first, then give each stage a home.

## Four call levels

1. **Pipeline** — a runnable CLI. Its body is the dataflow: one line per stage in
   layer order. Its only branches validate inputs.
2. **Subpipeline** — `@subpipeline`: an uncached composition. Its body calls steps
   and packs results. Two entry points sharing a stage call the same subpipeline;
   inlined copies of a call list are how two paths drift apart.
3. **Step** — `@step`: one cached stage, a load or a whole-dataset computation.
4. **Compute** — undecorated maths. The step is the seam between the pipeline and
   the library.

**Aftereffects attach to `@step` and `@subpipeline` only.** On a plain function
the metadata is inert and never runs.

## Call libraries from the step

A step calls scikit-learn, numpy, or scipy directly. Don't wrap a library in an
adapter to isolate it; the step is already that seam.

Your own computation is inline by default. Give it a function or module only when
it has a second caller, or is non-trivial maths worth testing alone.

## Data grows horizontally; results are columns

**A value computed for each row becomes a column on the frame that flows onward.**
That is how downstream steps read it and how it reaches observability. Don't model
a table of per-row results as a collection of objects — that table is a DataFrame.

Classes are for configuration handed to a step, typed contracts, and fitted state.
Not for tabular results that could be columns.

## A step that drops rows returns what survived and what it dropped

`intermediate_to_primary` returns `(df, FilterChain)`. Return the drop record as
data, not a log line, so an aftereffect can report per-rule survival every run.

## The model produces a score; a separate layer turns scores into decisions

**L06 emits `y_score`.** Thresholds live downstream in L08. A scorer with no policy
baked in stays reusable, and a policy kept separate stays changeable without
retraining.

## Every tunable is a settings field, passed as an argument

**A value that can be tuned is a documented `settings.py` field, passed to the
top-level step as an argument defaulted from settings.** Reading `settings.foo`
inside a step body is a cache bug — see `python-coding.md`.

Couple values that must agree with `@computed_field` so they cannot drift, and
group related knobs into nested blocks.

## A constant is either derived or an explicit assumption

Derive a constant from first principles or from the data, and it carries its own
explanation. When you must choose a number outright, put it in `settings.py` and
say in the docstring that it is a choice.

## Cache every load and computation

**Loading data is a cached step like any other.** When a step's result depends on
code its arguments do not describe, hash that source and pass the hash in, as
`architecture_fingerprint()` does, so editing the code invalidates the cache.

## Before you write

1. State the dataflow in one sentence. That is what `run()` should read like.
2. Search for a step or function that already does the job, and call it.
3. Place each piece: pipeline = dataflow, subpipeline = composition, step = cached
   stage, compute = maths.
4. Tunables become settings fields passed as arguments.
5. Per-row results are columns; classes are for config, contracts, and state.

## The litmus test

Read `run()` top to bottom. If a module, wrapper, or class does not make the
one-sentence dataflow easier to see, it has not earned its place.
