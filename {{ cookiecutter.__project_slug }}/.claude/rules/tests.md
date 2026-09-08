---
paths:
  - "tests/**/*.py"
---

Tests use the synthetic data in `tests/conftest.py`, and not the supplied
dataset. The tests are therefore fast, and they continue to operate if a user
selects different data.

The fixtures `isolated_cache` and `local_mlflow` have `autouse=True`. Without
them, a test writes data into the real KissML cache and the real `mlflow.db`, and
a later run reads that data. `local_mlflow` also keeps one MLflow run open for
the test. An effect that writes with no open run makes MLflow open one and keep
it open.

Give a test the name of the behaviour that it protects, and not the name of the
function that it calls. Use `test_grouped_cv_keeps_a_group_within_one_fold`, not
`test_make_cv`.
