"""L08 Reporting: turn out-of-fold scores into metrics and figures.

The threshold is applied here and not in L06. The model stays a scorer, and you
can change the operating point without a new fit.
"""

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
    learning_curve_figure,
    learning_curve_points,
    permutation_figure,
    precision_recall_figure,
    roc_figure,
    score_distribution_figure,
)
from pipeline.common.visualization import log_figure_html
from pipeline.settings import settings

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

    threshold = settings.reporting.threshold if override_threshold is None else override_threshold
    metrics = classification_metrics(y_true, y_score, threshold)

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

    return Report(
        metrics=metrics,
        figures=figures,
        threshold=threshold,
        learning_curve=curve,
    )
