"""Threshold selection, confidence intervals, learning curves, and figures."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import learning_curve

from pipeline.common.evaluation import SCORERS, make_cv
from pipeline.common.visualization import default_layout


def fbeta_optimal_threshold(
    y_true: pd.Series, y_score: pd.Series, beta: float
) -> tuple[float, float]:
    """Return the threshold maximizing F-beta, and the score it achieves.

    Beta below 1 weights precision; above 1 weights recall.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    # precision_recall_curve returns one more point than thresholds.
    precision, recall = precision[:-1], recall[:-1]
    beta_sq = beta**2
    denominator = beta_sq * precision + recall
    with np.errstate(divide="ignore", invalid="ignore"):
        scores = np.where(denominator > 0, (1 + beta_sq) * precision * recall / denominator, 0.0)
    best = int(np.argmax(scores))
    return float(thresholds[best]), float(scores[best])


def youdens_j_threshold(y_true: pd.Series, y_score: pd.Series) -> tuple[float, float]:
    """Return the threshold maximizing Youden's J, and the J it achieves.

    J is `sensitivity + specificity - 1`, which weights both classes equally
    regardless of how imbalanced the labels are.
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    j = tpr - fpr
    best = int(np.argmax(j))
    return float(thresholds[best]), float(j[best])


def classification_metrics(
    y_true: pd.Series, y_score: pd.Series, threshold: float, beta: float
) -> dict[str, float]:
    """Return threshold-free and thresholded metrics for one set of scores."""
    y_pred = (np.asarray(y_score) >= threshold).astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "average_precision": float(average_precision_score(y_true, y_score)),
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        f"f{beta:g}": float(fbeta_score(y_true, y_pred, beta=beta, zero_division=0)),
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


def shap_importance(estimator: Any, X: pd.DataFrame, max_rows: int = 200) -> pd.DataFrame | None:
    """Return mean absolute SHAP value per feature, or None if unavailable.

    Returns None rather than raising when the estimator has no supported
    explainer, so a reporting run is never lost to an optional figure.
    """
    import shap

    sample = X.head(max_rows)
    try:
        explainer = shap.Explainer(estimator.predict_proba, sample)
        explanation = explainer(sample)
        values = np.asarray(explanation.values)  # ty: ignore[unresolved-attribute]
    except Exception:  # noqa: BLE001 - any explainer failure degrades to no figure
        return None

    # predict_proba explains both classes; the positive class is the last column.
    per_feature = np.abs(values[..., -1]) if values.ndim == 3 else np.abs(values)
    importance = pd.DataFrame(
        {"feature": list(sample.columns), "mean_abs_shap": per_feature.mean(axis=0)}
    )
    return importance.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def shap_importance_figure(importance: pd.DataFrame) -> go.Figure:
    """Return feature importance as a bar chart, most influential at the top."""
    top = importance.head(30).iloc[::-1]
    fig = go.Figure(go.Bar(x=top["mean_abs_shap"], y=top["feature"], orientation="h"))
    fig.update_xaxes(title="Mean |SHAP value|")
    fig.update_layout(height=max(320, 22 * len(top)))
    return default_layout(fig, "Feature importance")
