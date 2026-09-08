"""Prediction files for an external scorer.

The submitted model is fitted on every training row, which is not the model any
reported score describes: those come from L07, where each row was scored by a
model that had not seen it. Both are correct for their purpose, and the
difference is the reason they live in different places.
"""

import logging
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.pipeline import Pipeline

from pipeline.common.l01_raw import load_raw
from pipeline.common.l02_intermediate import raw_to_intermediate
from pipeline.common.l04_feature import primary_to_feature
from pipeline.settings import settings

logger = logging.getLogger(__name__)


def write_submission(
    estimator: Pipeline,
    feature_columns: list[str],
    test_data_path: Path,
    submission_dir: Path,
    id_col: str = settings.id_col,
    target_col: str = settings.target_col,
    threshold: float | None = None,
) -> Path:
    """Score the held-out table and write a two-column prediction file.

    Writes the probability when `threshold` is None, and the thresholded label
    otherwise. The file is logged to the active MLflow run.
    """
    raw = load_raw(test_data_path)
    intermediate = raw_to_intermediate(raw)
    features = primary_to_feature(intermediate)

    missing = [c for c in feature_columns if c not in features.columns]
    if missing:
        raise KeyError(f"The held-out table is missing feature columns: {missing}")

    scores = estimator.predict_proba(features[feature_columns])[:, 1]
    predictions = (scores >= threshold).astype(int) if threshold is not None else scores

    submission_dir.mkdir(parents=True, exist_ok=True)
    out = submission_dir / f"submission-{datetime.now():%Y%m%d-%H%M%S}.csv"
    pd.DataFrame({id_col: raw[id_col], target_col: predictions}).to_csv(out, index=False)

    mlflow.log_artifact(str(out), artifact_path="09_submission")
    logger.info("Wrote %s (%d rows)", out, len(raw))
    return out
