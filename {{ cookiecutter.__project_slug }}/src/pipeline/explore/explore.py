"""The experiment: load the data, tune, score out of fold, and report.

The body of `run` is the dataflow. Read it top to bottom and you have the
experiment; anything that does not make that sequence easier to see does not
belong here.
"""

import logging

import click
import mlflow

from pipeline.common.l05_model_input import build_model_input, to_model_input
from pipeline.common.l06_models import search_hyperparameters, train_model
from pipeline.common.l07_model_output import score_out_of_fold
from pipeline.common.l08_reporting import build_reporting
from pipeline.common.observability import (
    configure_logging,
    log_level_option,
    mlflow_run_url,
    start_run,
)
from pipeline.common.submission import write_submission
from pipeline.settings import settings

logger = logging.getLogger(__name__)


@click.command()
@log_level_option()
@click.option("--run-name", default=None, help="Name for the MLflow run.")
@click.option(
    "--permutation-test/--no-permutation-test",
    default=True,
    help="Test the score against shuffled labels.",
)
@click.option(
    "--override-threshold",
    type=float,
    default=None,
    help="Use this operating threshold instead of settings.reporting.threshold.",
)
@click.option(
    "--submit",
    is_flag=True,
    help="Also fit on every row and write a prediction file for settings.test_data_path.",
)
@click.option("--progress/--no-progress", default=True, help="Show progress bars.")
def run(
    log_level: str,
    run_name: str | None,
    permutation_test: bool,
    override_threshold: float | None,
    submit: bool,
    progress: bool,
) -> None:
    """Run the experiment end to end and log it to MLflow."""
    configure_logging(log_level)

    with start_run(settings.mlflow_tracking_uri, settings.mlflow_experiment, run_name) as active:
        mlflow.log_params(
            {
                "data_path": str(settings.data_path),
                "target_col": settings.target_col,
                "group_col": settings.group_col,
                "n_splits": settings.training.n_splits,
                "n_iterations": settings.training.n_iterations,
                "scoring": settings.training.scoring,
            }
        )

        model_input = build_model_input()
        search_results = search_hyperparameters(model_input, show_progress=progress)
        estimator = train_model(model_input, search_results)
        out_of_fold = score_out_of_fold(model_input, search_results, show_progress=progress)
        report = build_reporting(
            out_of_fold,
            model_input,
            estimator,
            permutation_test=permutation_test,
            override_threshold=override_threshold,
        )

        if submit:
            if settings.test_data_path is None:
                raise click.ClickException(
                    "--submit needs a held-out table; set PIPELINE_TEST_DATA_PATH."
                )
            write_submission(
                estimator=estimator,
                feature_columns=list(to_model_input(model_input).X.columns),
                test_data_path=settings.test_data_path,
                submission_dir=settings.submission_dir,
                threshold=report.threshold,
            )

        logger.info("ROC AUC (out of fold): %.4f", report.metrics["roc_auc"])
        logger.info(
            "%s",
            mlflow_run_url(
                settings.mlflow_tracking_uri,
                active.info.experiment_id,
                active.info.run_id,
            ),
        )


if __name__ == "__main__":
    run()
