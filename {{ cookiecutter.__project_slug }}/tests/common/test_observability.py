from pipeline.common.observability import mlflow_run_url


def test_http_uri_produces_a_browsable_link():
    url = mlflow_run_url("http://localhost:5000", "1", "abc")
    assert url == "http://localhost:5000/#/experiments/1/runs/abc"


def test_sqlite_uri_produces_a_hint_instead_of_a_link():
    assert "just mlflow-ui" in mlflow_run_url("sqlite:///mlflow.db", "1", "abc")
