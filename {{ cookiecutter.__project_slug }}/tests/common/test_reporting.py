import numpy as np
import pandas as pd
import pytest

from pipeline.common.reporting import (
    bootstrap_confidence_interval,
    classification_metrics,
    fbeta_optimal_threshold,
    youdens_j_threshold,
)


@pytest.fixture
def separable() -> tuple[pd.Series, pd.Series]:
    y_true = pd.Series([0] * 50 + [1] * 50)
    y_score = pd.Series(np.concatenate([np.linspace(0.0, 0.4, 50), np.linspace(0.6, 1.0, 50)]))
    return y_true, y_score


def test_fbeta_threshold_separates_the_classes(separable):
    threshold, score = fbeta_optimal_threshold(*separable, beta=1.0)
    assert 0.4 < threshold <= 0.6
    assert score == pytest.approx(1.0)


def test_a_low_beta_does_not_lower_the_threshold(separable):
    precision_weighted, _ = fbeta_optimal_threshold(*separable, beta=0.5)
    recall_weighted, _ = fbeta_optimal_threshold(*separable, beta=2.0)
    assert precision_weighted >= recall_weighted


def test_youden_j_is_one_for_perfect_separation(separable):
    _, j = youdens_j_threshold(*separable)
    assert j == pytest.approx(1.0)


def test_metrics_report_a_perfect_split(separable):
    metrics = classification_metrics(*separable, threshold=0.5, beta=1.0)
    assert metrics["roc_auc"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(1.0)
    assert metrics["recall"] == pytest.approx(1.0)


def test_confidence_interval_brackets_the_point_estimate(separable):
    point, lower, upper = bootstrap_confidence_interval(
        *separable, metric="roc_auc", n_bootstrap=200, random_state=0
    )
    assert lower <= point <= upper


def test_confidence_interval_is_wider_for_a_weak_signal():
    rng = np.random.default_rng(0)
    y_true = pd.Series([0] * 40 + [1] * 40)
    weak = pd.Series(rng.normal(0, 1, 80) + y_true * 0.3)

    _, low, high = bootstrap_confidence_interval(
        y_true, weak, metric="roc_auc", n_bootstrap=300, random_state=0
    )
    assert high - low > 0.1
