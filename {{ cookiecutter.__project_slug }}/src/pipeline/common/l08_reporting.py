"""L08 Reporting: turn out-of-fold scores into metrics, a threshold, and figures.

The threshold is chosen here rather than in L06, so the model stays a scorer and
the operating point can change without refitting anything.
"""

import logging
from typing import Annotated, NamedTuple

import mlflow
import pandas as pd
import plotly.graph_objects as go
from kissml import AfterEffect, subpipeline
from kissml.types import Tags
from sklearn.pipeline import Pipeline

from pipeline.common.evaluation import run_permutation_test
from pipeline.common.l05_model_input import to_model_input
from pipeline.common.reporting import (
    LearningCurvePoint,
    bootstrap_confidence_interval,
    classification_metrics,
    confusion_figure,
    fbeta_optimal_threshold,
    learning_curve_figure,
    learning_curve_points,
    permutation_figure,
    precision_recall_figure,
    roc_figure,
    score_distribution_figure,
    shap_importance,
    shap_importance_figure,
    youdens_j_threshold,
)
from pipeline.common.visualization import log_figure_html
from pipeline.settings import settings

logger = logging.getLogger(__name__)

L_PRE = "08_reporting"


class Report(NamedTuple):
    """The metrics, figures, threshold, and learning curve of one evaluation."""

    metrics: dict[str, float]
    figures: dict[str, go.Figure]
    threshold: float
    learning_curve: list[LearningCurvePoint]


class LogReportEffect(AfterEffect):
    """Logs every metric and figure in a report to MLflow."""

    def __call__(
        self,
        result: Report,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        for name, value in result.metrics.items():
            mlflow.log_metric(name, float(value))
        for name, figure in result.figures.items():
            log_figure_html(figure, L_PRE, name)


@subpipeline(error_on_effect_failure=True)
def build_reporting(
    out_of_fold: pd.DataFrame,
    model_input: pd.DataFrame,
    estimator: Pipeline,
    permutation_test: bool = True,
    override_threshold: float | None = None,
) -> Annotated[Report, LogReportEffect()]:
    """Evaluate the out-of-fold scores and return the report."""
    y_true, y_score = out_of_fold["y_true"], out_of_fold["y_score"]

    fbeta_threshold, fbeta_value = fbeta_optimal_threshold(
        y_true, y_score, settings.reporting.fbeta
    )
    j_threshold, j_value = youdens_j_threshold(y_true, y_score)
    threshold = override_threshold if override_threshold is not None else fbeta_threshold

    metrics = classification_metrics(y_true, y_score, threshold, settings.reporting.fbeta)
    metrics["threshold_fbeta"] = fbeta_threshold
    metrics["threshold_youden_j"] = j_threshold
    metrics["youden_j"] = j_value
    metrics["fbeta_at_threshold"] = fbeta_value

    for metric in ("roc_auc", "average_precision"):
        _, lower, upper = bootstrap_confidence_interval(
            y_true,
            y_score,
            metric=metric,
            n_bootstrap=settings.reporting.n_bootstrap,
            random_state=settings.training.base_random_state,
        )
        metrics[f"{metric}_ci_lower"] = lower
        metrics[f"{metric}_ci_upper"] = upper

    figures = {
        "roc": roc_figure(y_true, y_score),
        "precision_recall": precision_recall_figure(y_true, y_score),
        "confusion_matrix": confusion_figure(y_true, y_score, threshold),
        "score_distribution": score_distribution_figure(y_true, y_score, threshold),
    }

    data = to_model_input(model_input)
    curve = learning_curve_points(
        estimator=estimator,
        X=data.X,
        y=data.y,
        groups=data.groups,
        fractions=settings.reporting.learning_curve_sizes,
        n_splits=settings.training.n_splits,
        random_state=settings.training.base_random_state,
        scoring=settings.training.scoring,
    )
    figures["learning_curve"] = learning_curve_figure(curve)

    if permutation_test:
        observed, permuted, p_value = run_permutation_test(
            y_true=y_true,
            y_score=y_score,
            metric="roc_auc",
            n_permutations=settings.reporting.n_permutations,
            random_state=settings.training.base_random_state,
        )
        metrics["permutation_p_value"] = p_value
        metrics["permutation_null_mean"] = float(permuted.mean())
        figures["permutation_test"] = permutation_figure(observed, permuted, p_value)

    if settings.reporting.shap_enabled:
        importance = shap_importance(estimator, data.X)
        if importance is None:
            logger.warning("SHAP values unavailable for this estimator; skipping the figure.")
        else:
            figures["shap_importance"] = shap_importance_figure(importance)

    return Report(
        metrics=metrics,
        figures=figures,
        threshold=threshold,
        learning_curve=curve,
    )
