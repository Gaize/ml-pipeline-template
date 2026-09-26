"""Cross-validation splitters and the label-permutation significance test."""

from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

SCORERS: dict[str, Callable[..., float]] = {
    "roc_auc": roc_auc_score,
    "average_precision": average_precision_score,
}
"""Threshold-free metrics, keyed by the name a caller passes as `metric`."""


def make_cv(
    n_splits: int,
    random_state: int,
    grouped: bool,
) -> StratifiedKFold | StratifiedGroupKFold:
    """Return a stratified splitter, group-aware when `grouped` is set.

    A group-aware split keeps every row sharing a group value on the same side of
    the fold boundary. Use it when rows are repeated measurements of one entity:
    an independent split lets the model recognise the entity rather than the label,
    which inflates the score without improving anything.
    """
    cls = StratifiedGroupKFold if grouped else StratifiedKFold
    return cls(n_splits=n_splits, shuffle=True, random_state=random_state)


def permutation_p_value(
    observed: float,
    permuted: Sequence[float] | np.ndarray,
) -> float:
    """Return the one-sided p-value of `observed` against a permutation null.

    The estimate is `(1 + #{permuted >= observed}) / (1 + n)`, whose numerator and
    denominator both count the observed statistic. That keeps the p-value above
    zero, since a finite number of shuffles cannot evidence an arbitrarily small one.
    """
    permuted_arr = np.asarray(permuted, dtype=float)
    at_least_as_extreme = int(np.sum(permuted_arr >= observed))
    return (1 + at_least_as_extreme) / (1 + permuted_arr.size)


def run_permutation_test(
    y_true: pd.Series,
    y_score: pd.Series,
    metric: str,
    n_permutations: int,
    random_state: int,
) -> tuple[float, np.ndarray, float]:
    """Return the observed score, the permuted null scores, and the p-value.

    Only the labels are shuffled; the scores stay fixed, so nothing refits. This
    tests whether the ranking carries label information, not whether a fresh model
    would learn one.
    """
    scorer = SCORERS[metric]
    y_true_arr = np.asarray(y_true, dtype=int)
    y_score_arr = np.asarray(y_score, dtype=float)

    observed = float(scorer(y_true_arr, y_score_arr))
    rng = np.random.default_rng(random_state)
    permuted = np.array(
        [float(scorer(rng.permutation(y_true_arr), y_score_arr)) for _ in range(n_permutations)]
    )
    return observed, permuted, permutation_p_value(observed, permuted)
