"""L06 Models: define the estimator, search its hyperparameters, fit it.

This layer emits scores. Thresholds and decisions belong downstream, so the
estimator stays reusable and the policy stays swappable without retraining.
"""

import logging
from typing import Annotated, Any

import mlflow
import pandas as pd
from kissml import AfterEffect
from kissml.types import Tags
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pipeline.common.caching import source_fingerprint
from pipeline.common.effects import DataFrameTableLogger
from pipeline.common.l05_model_input import to_model_input
from pipeline.common.layers import layer_step
from pipeline.common.training import (
    iterated_grid_search,
    representative_params,
    score_spread,
)
from pipeline.settings import settings

logger = logging.getLogger(__name__)

L_PRE = "06_models"
step_decorator = layer_step(L_PRE)

PARAM_GRID: dict[str, list[Any]] = {
    "logreg__C": [0.01, 0.1, 1.0, 10.0],
    "logreg__l1_ratio": [0.0, 0.5, 1.0],
}
"""Hyperparameters searched at every iteration, keyed by estimator step name."""


def make_estimator(class_weight_balanced: bool = settings.class_weight_balanced) -> Pipeline:
    """Return the untrained estimator.

    Imputation and scaling sit inside the pipeline so they refit on each training
    fold, rather than seeing the held-out rows before they are scored. The
    regularization mix is set by `l1_ratio` in the grid: 0 is ridge, 1 is lasso.
    """
    return Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            (
                "logreg",
                LogisticRegression(
                    solver="saga",
                    max_iter=20000,
                    class_weight="balanced" if class_weight_balanced else None,
                ),
            ),
        ]
    )


def architecture_fingerprint() -> str:
    """Return a hash of the estimator definition and its grid.

    Editing either changes what a search means without changing any argument the
    search step receives, so the hash is passed in to move the cache key.
    """
    return source_fingerprint(make_estimator) + str(sorted(PARAM_GRID.items()))


class LogSearchResultsEffect(AfterEffect):
    """Logs per-iteration search scores and the representative hyperparameters."""

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        for name, value in score_spread(result).items():
            mlflow.log_metric(name, value)
        for name, value in representative_params(result).items():
            mlflow.log_param(f"best_{name}", value)


@step_decorator
def search_hyperparameters(
    model_input: pd.DataFrame,
    target_col: str = settings.target_col,
    group_col: str | None = settings.group_col,
    n_iterations: int = settings.training.n_iterations,
    n_splits: int = settings.training.n_splits,
    scoring: str = settings.training.scoring,
    base_random_state: int = settings.training.base_random_state,
    class_weight_balanced: bool = settings.class_weight_balanced,
    architecture: str = architecture_fingerprint(),
    show_progress: bool = False,
) -> Annotated[
    pd.DataFrame,
    DataFrameTableLogger(L_PRE, "search_results"),
    LogSearchResultsEffect(),
]:
    """Return one row per independent grid search over the model input."""
    del architecture
    data = to_model_input(model_input, target_col=target_col, group_col=group_col)
    return iterated_grid_search(
        estimator=make_estimator(class_weight_balanced),
        param_grid=PARAM_GRID,
        X=data.X,
        y=data.y,
        groups=data.groups,
        n_iterations=n_iterations,
        n_splits=n_splits,
        scoring=scoring,
        base_random_state=base_random_state,
        show_progress=show_progress,
    )


@step_decorator
def train_model(
    model_input: pd.DataFrame,
    search_results: pd.DataFrame,
    target_col: str = settings.target_col,
    group_col: str | None = settings.group_col,
    class_weight_balanced: bool = settings.class_weight_balanced,
    architecture: str = architecture_fingerprint(),
) -> Pipeline:
    """Fit the estimator on every row using the representative hyperparameters."""
    del architecture
    data = to_model_input(model_input, target_col=target_col, group_col=group_col)
    estimator = make_estimator(class_weight_balanced)
    estimator.set_params(**representative_params(search_results))
    estimator.fit(data.X, data.y)
    return estimator
