import numpy as np
import pandas as pd
import pytest

from pipeline.common.evaluation import make_cv, permutation_p_value, run_permutation_test
from tests.conftest import make_raw


def test_grouped_cv_keeps_a_group_within_one_fold():
    df = make_raw()
    groups = df["name"].str.rsplit("_", n=1).str[0]
    cv = make_cv(n_splits=4, random_state=0, grouped=True)

    for train_idx, test_idx in cv.split(df, df["status"], groups=groups):
        assert not set(groups.iloc[train_idx]) & set(groups.iloc[test_idx])


def test_ungrouped_cv_splits_a_group_across_folds():
    df = make_raw()
    groups = df["name"].str.rsplit("_", n=1).str[0]
    cv = make_cv(n_splits=4, random_state=0, grouped=False)

    train_idx, test_idx = next(iter(cv.split(df, df["status"])))
    assert set(groups.iloc[train_idx]) & set(groups.iloc[test_idx])


def test_p_value_never_reaches_zero():
    assert permutation_p_value(1.0, [0.5] * 100) == pytest.approx(1 / 101)


def test_p_value_is_one_when_every_permutation_matches():
    assert permutation_p_value(0.5, [0.5] * 9) == pytest.approx(1.0)


def test_permutation_test_finds_a_real_signal():
    rng = np.random.default_rng(0)
    y_true = pd.Series([0] * 50 + [1] * 50)
    y_score = pd.Series(np.concatenate([rng.normal(0, 1, 50), rng.normal(3, 1, 50)]))

    observed, permuted, p_value = run_permutation_test(
        y_true, y_score, metric="roc_auc", n_permutations=200, random_state=0
    )
    assert observed > 0.9
    assert permuted.mean() == pytest.approx(0.5, abs=0.05)
    assert p_value < 0.01
