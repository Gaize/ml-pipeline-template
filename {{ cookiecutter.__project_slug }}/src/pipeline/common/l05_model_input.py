"""L05 Model input: join features to labels and groups, ready for the estimator."""

from typing import Annotated, NamedTuple

import pandas as pd
from kissml import subpipeline

from pipeline.common.effects import (
    ClassBalanceLogger,
    DataFrameTableLogger,
    FeatureHistogramEffect,
)
from pipeline.common.l01_raw import load_raw
from pipeline.common.l02_intermediate import raw_to_intermediate
from pipeline.common.l03_primary import intermediate_to_primary
from pipeline.common.l04_feature import primary_to_feature
from pipeline.common.layers import layer_step
from pipeline.settings import settings

L_PRE = "05_model_input"
step_decorator = layer_step(L_PRE)


class ModelInput(NamedTuple):
    """The feature matrix, the labels, and the group keys for one dataset."""

    X: pd.DataFrame
    y: pd.Series
    groups: pd.Series | None


@step_decorator
def join_features_and_labels(
    features: pd.DataFrame,
    primary: pd.DataFrame,
    target_col: str = settings.target_col,
    group_col: str | None = settings.group_col,
    selected_feature_columns: tuple[str, ...] | None = settings.selected_feature_columns,
) -> Annotated[
    pd.DataFrame,
    DataFrameTableLogger(L_PRE),
    ClassBalanceLogger(L_PRE, settings.target_col),
    FeatureHistogramEffect(L_PRE, settings.target_col),
]:
    """Return one frame holding the features, the label, and the group key."""
    columns = list(selected_feature_columns or features.columns)
    missing = [c for c in columns if c not in features.columns]
    if missing:
        raise KeyError(f"selected_feature_columns names columns L04 did not produce: {missing}")

    out = features[columns].copy()
    out[target_col] = primary[target_col].astype(int).to_numpy()
    if group_col is not None:
        out[group_col] = primary[group_col].to_numpy()
    return out


def to_model_input(
    frame: pd.DataFrame,
    target_col: str = settings.target_col,
    group_col: str | None = settings.group_col,
) -> ModelInput:
    """Split a model-input frame into its feature matrix, labels, and groups."""
    drop = [target_col] + ([group_col] if group_col else [])
    X = frame.drop(columns=drop)
    y = frame[target_col]
    groups = frame[group_col] if group_col else None
    return ModelInput(X=X, y=y, groups=groups)


@subpipeline()
def build_model_input() -> pd.DataFrame:
    """Walk L01 through L05 and return the joined model-input frame."""
    raw = load_raw()
    intermediate = raw_to_intermediate(raw)
    primary, _ = intermediate_to_primary(intermediate)
    features = primary_to_feature(primary)
    return join_features_and_labels(features, primary)
