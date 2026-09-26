"""Plotly figure helpers with a shared layout."""

from pathlib import Path
from tempfile import TemporaryDirectory

import mlflow
import plotly.graph_objects as go


def default_layout(fig: go.Figure, title: str) -> go.Figure:
    """Apply the shared title, template, and margins to a figure."""
    fig.update_layout(
        title=title,
        template="plotly_white",
        margin={"l": 60, "r": 30, "t": 60, "b": 60},
        height=460,
    )
    return fig


def log_figure_html(fig: go.Figure, artifact_path: str, name: str) -> None:
    """Write a figure to MLflow as a self-contained HTML artifact."""
    with TemporaryDirectory() as tmp:
        out = Path(tmp) / f"{name}.html"
        fig.write_html(out, include_plotlyjs="cdn")
        mlflow.log_artifact(str(out), artifact_path=artifact_path)
