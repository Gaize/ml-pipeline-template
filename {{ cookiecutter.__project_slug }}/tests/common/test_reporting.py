import numpy as np
import pandas as pd
import pytest

from pipeline.common.reporting import bootstrap_confidence_interval, classification_metrics


@pytest.fixture
def separable() -> tuple[pd.Series, pd.Series]:
    y_true = pd.Series([0] * 50 + [1] * 50)
    y_score = pd.Series(np.concatenate([np.linspace(0.0, 0.4, 50), np.linspace(0.6, 1.0, 50)]))
    return y_true, y_score


def test_metrics_report_a_perfect_split(separable):
    metrics = classification_metrics(*separable, threshold=0.5)
    assert metrics["roc_auc"] == pytest.approx(1.0)
    assert metrics["precision"] == pytest.approx(1.0)
    assert metrics["recall"] == pytest.approx(1.0)


def test_a_high_threshold_trades_recall_for_precision(separable):
    strict = classification_metrics(*separable, threshold=0.95)
    assert strict["recall"] < 1.0
    assert strict["precision"] == pytest.approx(1.0)


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
