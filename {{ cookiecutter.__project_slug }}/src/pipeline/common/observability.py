"""Logging setup, git provenance, and the MLflow run URL."""

import logging
import subprocess
from collections.abc import Callable
from typing import Any

import click
import mlflow

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    """Configure root logging at `level` and quiet the noisiest dependencies."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("urllib3", "git"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def log_level_option() -> Callable[..., Any]:
    """Return a `--log-level` click option."""
    return click.option(
        "--log-level",
        default="INFO",
        type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
        help="Logging verbosity.",
    )


def clean_git_hash() -> str | None:
    """Return the current commit hash, or None if the tree is dirty or not a repo.

    A dirty tree has no hash that identifies the code that ran, so tagging one
    would assert a reproducibility the run does not have.
    """
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        if status.stdout.strip():
            return None
        rev = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return rev.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def mlflow_run_url(tracking_uri: str, experiment_id: str, run_id: str) -> str:
    """Return the browser URL for a run, or a `mlflow ui` hint for a local store."""
    if tracking_uri.startswith(("http://", "https://")):
        return f"{tracking_uri}/#/experiments/{experiment_id}/runs/{run_id}"
    return f"run {run_id} in experiment {experiment_id} (browse it with `just mlflow-ui`)"


def start_run(tracking_uri: str, experiment: str, run_name: str | None) -> Any:
    """Point MLflow at `tracking_uri` and start a run tagged with the commit hash."""
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment)
    run = mlflow.start_run(run_name=run_name)
    git_hash = clean_git_hash()
    if git_hash:
        mlflow.set_tag("git_hash", git_hash)
    else:
        logger.warning("Working tree is dirty or untracked; this run has no git_hash tag.")
    return run
