"""Repeated grid search and the selection of a representative iteration."""

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, clone
from sklearn.model_selection import GridSearchCV
from tqdm import tqdm

from pipeline.common.evaluation import make_cv


def run_grid_search(
    estimator: BaseEstimator,
    param_grid: dict[str, list[Any]],
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series | None,
    n_splits: int,
    scoring: str,
    random_state: int,
) -> GridSearchCV:
    """Fit one grid search over `param_grid` with folds seeded by `random_state`."""
    cv = make_cv(n_splits=n_splits, random_state=random_state, grouped=groups is not None)
    search = GridSearchCV(
        estimator=clone(estimator),
        param_grid=param_grid,
        scoring=scoring,
        cv=cv,
        n_jobs=-1,
        refit=True,
    )
    search.fit(X, y, groups=groups)
    return search


def iterated_grid_search(
    estimator: BaseEstimator,
    param_grid: dict[str, list[Any]],
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series | None,
    n_iterations: int,
    n_splits: int,
    scoring: str,
    base_random_state: int,
    show_progress: bool = False,
) -> pd.DataFrame:
    """Return one row per independent grid search, each with its own fold assignment.

    A single grid search reports the score of one particular way of cutting the
    data. Repeating it under different seeds shows how much of that score is the
    model and how much is the split.
    """
    iterator = range(n_iterations)
    if show_progress:
        iterator = tqdm(iterator, total=n_iterations, desc="grid search")

    rows = []
    for i in iterator:
        random_state = base_random_state + i
        search = run_grid_search(
            estimator=estimator,
            param_grid=param_grid,
            X=X,
            y=y,
            groups=groups,
            n_splits=n_splits,
            scoring=scoring,
            random_state=random_state,
        )
        rows.append(
            {
                "iteration": i,
                "random_state": random_state,
                "best_score": float(search.best_score_),
                "best_params": search.best_params_,
            }
        )
    return select_representative(pd.DataFrame(rows))


def select_representative(results: pd.DataFrame) -> pd.DataFrame:
    """Mark the iteration whose score is closest to the mean across iterations.

    The typical iteration is a better estimate of the result of the next split
    than the best iteration is.
    """
    out = results.copy()
    out["distance_from_mean"] = (out["best_score"] - out["best_score"].mean()).abs()
    out["is_representative"] = False
    out.loc[out["distance_from_mean"].idxmin(), "is_representative"] = True
    return out


def representative_params(results: pd.DataFrame) -> dict[str, Any]:
    """Return the hyperparameters of the representative iteration."""
    row = results.loc[results["is_representative"]].iloc[0]
    return dict(row["best_params"])


def score_spread(results: pd.DataFrame) -> dict[str, float]:
    """Return the mean, standard deviation, and range of scores across iterations."""
    scores = results["best_score"].to_numpy(dtype=float)
    return {
        "cv_score_mean": float(np.mean(scores)),
        "cv_score_std": float(np.std(scores)),
        "cv_score_min": float(np.min(scores)),
        "cv_score_max": float(np.max(scores)),
    }
