import pandas as pd
import pytest

from pipeline.common.l02_intermediate import raw_to_intermediate
from pipeline.common.l03_primary import intermediate_to_primary
from pipeline.common.l04_feature import primary_to_feature
from pipeline.common.l05_model_input import join_features_and_labels
from pipeline.common.l06_models import (
    architecture_fingerprint,
    make_estimator,
    search_hyperparameters,
    train_model,
)
from pipeline.common.l07_model_output import score_out_of_fold
from pipeline.common.l08_reporting import build_reporting


@pytest.fixture
def model_input(raw) -> pd.DataFrame:
    primary, _ = intermediate_to_primary(raw_to_intermediate(raw))
    return join_features_and_labels(primary_to_feature(primary), primary)


@pytest.fixture
def search_results(model_input) -> pd.DataFrame:
    return search_hyperparameters(model_input, n_iterations=2, n_splits=3)


def test_estimator_scales_inside_the_pipeline():
    assert "scale" in dict(make_estimator().named_steps)


def test_architecture_fingerprint_is_stable_across_calls():
    assert architecture_fingerprint() == architecture_fingerprint()


def test_search_returns_one_row_per_iteration(search_results):
    assert len(search_results) == 2
    assert search_results["is_representative"].sum() == 1


def test_representative_iteration_is_not_the_best_by_construction(search_results):
    representative = search_results.loc[search_results["is_representative"], "best_score"].iloc[0]
    assert representative <= search_results["best_score"].max()


def test_train_model_fits_on_every_row(model_input, search_results):
    estimator = train_model(model_input, search_results)
    assert estimator.predict_proba(model_input.drop(columns=["status", "subject"])).shape == (
        len(model_input),
        2,
    )


def test_out_of_fold_scores_every_row_exactly_once(model_input, search_results):
    out = score_out_of_fold(model_input, search_results, n_splits=3)
    assert len(out) == len(model_input)
    assert out["y_score"].notna().all()
    assert set(out["fold"]) == {0, 1, 2}


def test_reporting_produces_metrics_and_figures(model_input, search_results):
    out = score_out_of_fold(model_input, search_results, n_splits=3)
    estimator = train_model(model_input, search_results)
    report = build_reporting(out, model_input, estimator, permutation_test=False)

    assert 0.0 <= report.metrics["roc_auc"] <= 1.0
    assert "roc_auc_ci_lower" in report.metrics
    assert {"roc", "precision_recall", "learning_curve"} <= set(report.figures)


def test_an_override_threshold_is_used_verbatim(model_input, search_results):
    out = score_out_of_fold(model_input, search_results, n_splits=3)
    estimator = train_model(model_input, search_results)
    report = build_reporting(
        out, model_input, estimator, permutation_test=False, override_threshold=0.9
    )
    assert report.threshold == 0.9
