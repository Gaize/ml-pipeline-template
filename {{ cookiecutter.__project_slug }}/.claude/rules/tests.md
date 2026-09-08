---
paths:
  - "tests/**/*.py"
---

Tests use the synthetic builders in `tests/conftest.py` rather than the bundled
dataset, so they stay fast and survive a student pointing L01 somewhere else.

The `isolated_cache` and `local_mlflow` fixtures are autouse. Without them a test
writes fixture data into the real KissML cache and the real `mlflow.db`, and later
runs read it back. `local_mlflow` also holds one MLflow run open for the test,
because an effect that logs with no active run makes MLflow start one implicitly
and leave it open.

Name a test for the behaviour it pins, not the function it calls:
`test_grouped_cv_keeps_a_group_within_one_fold`, not `test_make_cv`.
