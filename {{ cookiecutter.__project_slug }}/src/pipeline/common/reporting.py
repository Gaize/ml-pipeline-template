"""Classification metrics, confidence intervals, learning curves, and figures."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import learning_curve

from pipeline.common.evaluation import SCORERS, make_cv
from pipeline.common.visualization import default_layout


def classification_metrics(
    y_true: pd.Series, y_score: pd.Series, threshold: float
) -> dict[str, float]:
    """Return the metrics for one set of scores at one threshold."""
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "average_precision": float(average_precision_score(y_true, y_score)),
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def bootstrap_confidence_interval(
    y_true: pd.Series,
    y_score: pd.Series,
    metric: str,
    n_bootstrap: int,
    random_state: int,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Return the point estimate and percentile confidence bounds for a metric.

    Resamples rows with replacement. Resamples that end up single-class are
    skipped, since the metric is undefined for them.
    """
    scorer = SCORERS[metric]
    y_true_arr = np.asarray(y_true, dtype=int)
    y_score_arr = np.asarray(y_score, dtype=float)
    point = float(scorer(y_true_arr, y_score_arr))

    rng = np.random.default_rng(random_state)
    n = y_true_arr.size
    samples = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)
        if np.unique(y_true_arr[idx]).size < 2:
            continue
        samples.append(float(scorer(y_true_arr[idx], y_score_arr[idx])))

    if not samples:
        return point, float("nan"), float("nan")
    lower = float(np.percentile(samples, 100 * alpha / 2))
    upper = float(np.percentile(samples, 100 * (1 - alpha / 2)))
    return point, lower, upper


@dataclass
class LearningCurvePoint:
    """One training-set size and the score reached there."""

    train_fraction: float
    n_train: int
    train_score: float
    test_score: float
    test_score_std: float


def learning_curve_points(
    estimator: BaseEstimator,
    X: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series | None,
    fractions: Sequence[float],
    n_splits: int,
    random_state: int,
    scoring: str = "roc_auc",
) -> list[LearningCurvePoint]:
    """Return cross-validated train and test scores at each training-set fraction.

    A test score still climbing at the largest fraction means more data would help;
    a wide train-test gap that does not close means the model is memorizing.
    """
    cv = make_cv(n_splits=n_splits, random_state=random_state, grouped=groups is not None)
    sizes, train_scores, test_scores = learning_curve(
        clone(estimator),
        X,
        y,
        groups=groups,
        train_sizes=np.asarray(fractions),
        cv=cv,
        scoring=scoring,
        n_jobs=-1,
        shuffle=False,
    )
    return [
        LearningCurvePoint(
            train_fraction=float(frac),
            n_train=int(size),
            train_score=float(np.mean(train)),
            test_score=float(np.mean(test)),
            test_score_std=float(np.std(test)),
        )
        for frac, size, train, test in zip(fractions, sizes, train_scores, test_scores, strict=True)
    ]


def roc_figure(y_true: pd.Series, y_score: pd.Series) -> go.Figure:
    """Return the ROC curve with the chance diagonal drawn."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    auc = roc_auc_score(y_true, y_score)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name=f"AUC = {auc:.3f}"))
    fig.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="chance", line={"dash": "dash"})
    )
    fig.update_xaxes(title="False positive rate")
    fig.update_yaxes(title="True positive rate")
    return default_layout(fig, "ROC curve (out of fold)")


def precision_recall_figure(y_true: pd.Series, y_score: pd.Series) -> go.Figure:
    """Return the precision-recall curve with the positive-rate baseline drawn."""
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    ap = average_precision_score(y_true, y_score)
    baseline = float(np.mean(np.asarray(y_true, dtype=int)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recall, y=precision, mode="lines", name=f"AP = {ap:.3f}"))
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[baseline, baseline],
            mode="lines",
            name=f"baseline = {baseline:.3f}",
            line={"dash": "dash"},
        )
    )
    fig.update_xaxes(title="Recall")
    fig.update_yaxes(title="Precision")
    return default_layout(fig, "Precision-recall curve (out of fold)")


def confusion_figure(y_true: pd.Series, y_score: pd.Series, threshold: float) -> go.Figure:
    """Return the confusion matrix at `threshold` as an annotated heatmap."""
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    matrix = confusion_matrix(y_true, y_pred)
    labels = ["negative", "positive"]
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=[f"predicted {label}" for label in labels],
            y=[f"actual {label}" for label in labels],
            colorscale="Blues",
            showscale=False,
            text=matrix,
            texttemplate="%{text}",
        )
    )
    return default_layout(fig, f"Confusion matrix at threshold {threshold:.3f}")


def learning_curve_figure(points: Sequence[LearningCurvePoint]) -> go.Figure:
    """Return train and cross-validated test scores against training-set size."""
    sizes = [p.n_train for p in points]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=sizes, y=[p.train_score for p in points], mode="lines+markers", name="train")
    )
    fig.add_trace(
        go.Scatter(
            x=sizes,
            y=[p.test_score for p in points],
            mode="lines+markers",
            name="cross-validated",
            error_y={"type": "data", "array": [p.test_score_std for p in points]},
        )
    )
    fig.update_xaxes(title="Training rows")
    fig.update_yaxes(title="Score")
    return default_layout(fig, "Learning curve")


def permutation_figure(observed: float, permuted: np.ndarray, p_value: float) -> go.Figure:
    """Return the permutation null distribution with the observed score marked.

    The null sits at chance because the scores are fixed and only the labels
    move. This asks whether the ranking beats chance, not whether the split leaks.
    """
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=permuted, nbinsx=40, name="shuffled labels"))
    fig.add_vline(
        x=observed,
        line={"color": "crimson", "width": 2},
        annotation_text=f"observed = {observed:.3f} (p = {p_value:.4f})",
    )
    fig.add_vline(x=float(np.mean(permuted)), line={"color": "grey", "dash": "dash"})
    fig.update_xaxes(title="Score")
    fig.update_yaxes(title="Permutations")
    return default_layout(fig, "Label-permutation null distribution")


def score_distribution_figure(y_true: pd.Series, y_score: pd.Series, threshold: float) -> go.Figure:
    """Return overlaid score histograms per class with the threshold marked."""
    fig = go.Figure()
    y_true_arr = np.asarray(y_true, dtype=int)
    y_score_arr = np.asarray(y_score, dtype=float)
    for label, name in ((0, "negative"), (1, "positive")):
        fig.add_trace(
            go.Histogram(x=y_score_arr[y_true_arr == label], name=name, opacity=0.6, nbinsx=40)
        )
    fig.add_vline(x=threshold, line={"color": "black", "dash": "dash"})
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title="Score")
    fig.update_yaxes(title="Rows")
    return default_layout(fig, "Out-of-fold score distribution")
