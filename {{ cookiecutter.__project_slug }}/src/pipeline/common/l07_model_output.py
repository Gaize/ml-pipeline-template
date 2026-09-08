"""L07 Model output: run the model and produce an honest score for every row.

Each row is scored by a model that never saw it during fitting, so the scores
L08 evaluates are not the scores of a model grading its own training data.
"""

from typing import Annotated

import numpy as np
import pandas as pd
from sklearn.base import clone
from tqdm import tqdm

from pipeline.common.effects import DataFrameTableLogger
from pipeline.common.evaluation import make_cv
from pipeline.common.l05_model_input import to_model_input
from pipeline.common.l06_models import make_estimator
from pipeline.common.layers import layer_step
from pipeline.common.training import representative_params
from pipeline.settings import settings

L_PRE = "07_model_output"
step_decorator = layer_step(L_PRE)


@step_decorator
def score_out_of_fold(
    model_input: pd.DataFrame,
    search_results: pd.DataFrame,
    target_col: str = settings.target_col,
    group_col: str | None = settings.group_col,
    n_splits: int = settings.training.n_splits,
    random_state: int = settings.training.base_random_state,
    class_weight_balanced: bool = settings.class_weight_balanced,
    show_progress: bool = False,
) -> Annotated[pd.DataFrame, DataFrameTableLogger(L_PRE, "out_of_fold")]:
    """Return the label, the out-of-fold score, and the fold index for every row."""
    data = to_model_input(model_input, target_col=target_col, group_col=group_col)
    estimator = make_estimator(class_weight_balanced)
    estimator.set_params(**representative_params(search_results))

    cv = make_cv(n_splits=n_splits, random_state=random_state, grouped=data.groups is not None)
    splits = list(cv.split(data.X, data.y, groups=data.groups))

    y_score = np.full(len(data.X), np.nan)
    fold_index = np.full(len(data.X), -1, dtype=int)

    iterator = enumerate(splits)
    if show_progress:
        iterator = tqdm(iterator, total=len(splits), desc="out-of-fold scoring")

    for fold, (train_idx, test_idx) in iterator:
        fitted = clone(estimator)
        fitted.fit(data.X.iloc[train_idx], data.y.iloc[train_idx])
        y_score[test_idx] = fitted.predict_proba(data.X.iloc[test_idx])[:, 1]
        fold_index[test_idx] = fold

    out = pd.DataFrame(
        {
            "y_true": data.y.to_numpy(),
            "y_score": y_score,
            "fold": fold_index,
        }
    )
    if data.groups is not None:
        out[group_col] = data.groups.to_numpy()
    return out.loc[out["fold"] >= 0].reset_index(drop=True)
