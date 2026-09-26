"""KissML aftereffects that log to MLflow.

An aftereffect runs whenever a step's value is materialized, including from
cache, so a fully-cached rerun still produces a complete MLflow run. The
metadata is only live on a `@step` or `@subpipeline`; on a plain function it is
inert and never runs.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import mlflow
import pandas as pd
import plotly.express as px
from kissml import AfterEffect
from kissml.types import Tags

from pipeline.common.filters import FilterChain
from pipeline.common.visualization import default_layout, log_figure_html


def log_frame_csv(frame: pd.DataFrame, artifact_path: str, name: str) -> None:
    """Write a frame to MLflow as a CSV artifact under `artifact_path`."""
    with TemporaryDirectory() as tmp:
        out = Path(tmp) / f"{name}.csv"
        frame.to_csv(out, index=False)
        mlflow.log_artifact(str(out), artifact_path=artifact_path)


class DataFrameTableLogger(AfterEffect):
    """Logs a frame to MLflow as a CSV artifact and records its shape."""

    def __init__(self, prefix: str, name: str | None = None, max_rows: int = 5000) -> None:
        self.prefix = prefix
        self.name = name
        self.max_rows = max_rows

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        name = self.name or func_name
        mlflow.log_metric(f"{name}_rows", len(result))
        mlflow.log_metric(f"{name}_cols", result.shape[1])
        log_frame_csv(result.head(self.max_rows), self.prefix, name)


class DataFrameStatsLogger(AfterEffect):
    """Logs per-column summary statistics for a frame."""

    def __init__(self, prefix: str, name: str | None = None) -> None:
        self.prefix = prefix
        self.name = name

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        name = self.name or func_name
        stats = result.describe(include="all").transpose()
        stats.insert(0, "column", stats.index)
        stats["missing"] = result.isna().sum().reindex(stats.index).to_numpy()
        log_frame_csv(stats, self.prefix, f"{name}_stats")


class ClassBalanceLogger(AfterEffect):
    """Logs the label distribution of a frame."""

    def __init__(self, prefix: str, target_col: str) -> None:
        self.prefix = prefix
        self.target_col = target_col

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        if self.target_col not in result.columns:
            return
        counts = result[self.target_col].value_counts().sort_index()
        for label, count in counts.items():
            mlflow.log_metric(f"class_{label}_count", int(count))
        if len(counts) > 1:
            mlflow.log_metric("class_balance", float(counts.min() / counts.max()))


class FilterReportEffect(AfterEffect):
    """Logs per-rule survival for a step that returns `(frame, FilterChain)`.

    This shows where the data went, before a person must ask.
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(
        self,
        result: tuple[pd.DataFrame, FilterChain],
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        _, chain = result
        report = chain.to_frame()
        if report.empty:
            return
        log_frame_csv(report, self.prefix, f"{func_name}_filters")
        for record in report.to_dict("records"):
            mlflow.log_metric(f"survival_{record['filter']}", float(record["survival"]))


class FeatureHistogramEffect(AfterEffect):
    """Logs an overlaid histogram of each feature, split by label."""

    def __init__(self, prefix: str, target_col: str, max_features: int = 24) -> None:
        self.prefix = prefix
        self.target_col = target_col
        self.max_features = max_features

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        if self.target_col not in result.columns:
            return
        numeric = result.select_dtypes("number").columns
        features = [c for c in numeric if c != self.target_col][: self.max_features]
        if not features:
            return
        long = result.melt(
            id_vars=[self.target_col], value_vars=features, var_name="feature", value_name="value"
        )
        fig = px.histogram(
            long,
            x="value",
            color=self.target_col,
            facet_col="feature",
            facet_col_wrap=4,
            histnorm="probability density",
            opacity=0.65,
            barmode="overlay",
        )
        fig.update_xaxes(matches=None, showticklabels=True)
        fig.update_yaxes(matches=None)
        fig.update_layout(height=240 * (1 + (len(features) - 1) // 4))
        default_layout(fig, "Feature distributions by label")
        log_figure_html(fig, self.prefix, "feature_histograms")


class FeatureCorrelationEffect(AfterEffect):
    """Logs the feature correlation matrix as a heatmap."""

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def __call__(
        self,
        result: pd.DataFrame,
        was_cached: bool,
        func_name: str,
        execution_time: float,
        tags: Tags,
    ) -> None:
        numeric = result.select_dtypes("number")
        if numeric.shape[1] < 2:
            return
        corr = numeric.corr()
        fig = px.imshow(corr, zmin=-1, zmax=1, color_continuous_scale="RdBu_r", aspect="auto")
        default_layout(fig, "Feature correlation")
        log_figure_html(fig, self.prefix, "feature_correlation")
