"""Shared fixtures.

The cache fixture is autouse because a test that writes into the real KissML
cache would poison later real runs with fixture data.
"""

import numpy as np
import pandas as pd
import pytest
from kissml.core import close_all_caches
from kissml.settings import settings as kissml_settings


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the KissML cache at a temporary directory for the duration of a test."""
    close_all_caches()
    monkeypatch.setattr(kissml_settings, "cache_directory", tmp_path / "kissml")
    yield
    close_all_caches()


@pytest.fixture(autouse=True)
def local_mlflow(tmp_path, monkeypatch):
    """Give each test a temporary MLflow store and one active run.

    The run is opened here for the same reason the CLI opens it: layers and their
    aftereffects log into whatever run is active. Without one, the first effect
    to log makes MLflow start a run implicitly and leave it open, and every later
    `start_run` then fails.
    """
    import mlflow

    monkeypatch.chdir(tmp_path)
    mlflow.set_tracking_uri(f"sqlite:///{tmp_path / 'test.db'}")
    while mlflow.active_run():
        mlflow.end_run()
    with mlflow.start_run():
        yield
    while mlflow.active_run():
        mlflow.end_run()


def make_raw(n_subjects: int = 12, per_subject: int = 6, seed: int = 0) -> pd.DataFrame:
    """Return a synthetic source table shaped like the bundled dataset.

    Each subject gets one label and several recordings, so a record-wise split
    would put most of a subject's rows in train.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for subject in range(n_subjects):
        label = int(subject % 3 != 0)
        offset = rng.normal(label * 1.2, 0.3)
        for recording in range(per_subject):
            rows.append(
                {
                    "name": f"phon_R01_S{subject:02d}_{recording + 1}",
                    "feat_a": offset + rng.normal(0, 0.5),
                    "feat_b": rng.normal(0, 1.0),
                    "feat_c": offset * 0.5 + rng.normal(0, 0.8),
                    "status": label,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture
def raw() -> pd.DataFrame:
    """A synthetic source table."""
    return make_raw()
