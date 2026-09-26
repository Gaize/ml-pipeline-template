import pandas as pd
import pytest

from pipeline.common.l01_raw import load_raw
from pipeline.common.l02_intermediate import derive_subject, raw_to_intermediate
from pipeline.common.l03_primary import intermediate_to_primary
from pipeline.common.l04_feature import primary_to_feature
from pipeline.common.l05_model_input import join_features_and_labels, to_model_input


def test_load_raw_rejects_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_raw(tmp_path / "absent.csv")


def test_load_raw_reads_a_csv_unchanged(tmp_path, raw):
    path = tmp_path / "raw.csv"
    raw.to_csv(path, index=False)
    assert load_raw(path).shape == raw.shape


def test_derive_subject_drops_the_recording_index():
    names = pd.Series(["phon_R01_S01_1", "phon_R01_S01_6", "phon_R01_S02_1"])
    assert list(derive_subject(names)) == ["phon_R01_S01", "phon_R01_S01", "phon_R01_S02"]


def test_intermediate_adds_the_group_column(raw):
    out = raw_to_intermediate(raw, group_col="subject")
    assert out["subject"].nunique() == 12
    assert out["status"].dtype == "Int64"


def test_intermediate_skips_the_group_column_when_disabled(raw):
    assert "subject" not in raw_to_intermediate(raw, group_col=None).columns


def test_primary_drops_rows_with_no_label(raw):
    raw.loc[0, "status"] = None
    out, chain = intermediate_to_primary(raw_to_intermediate(raw))
    assert len(out) == len(raw) - 1
    assert chain.steps[0].name == "missing_target"


def test_primary_drops_a_mostly_empty_column(raw):
    raw["feat_sparse"] = None
    out, chain = intermediate_to_primary(raw_to_intermediate(raw))
    assert "feat_sparse" not in out.columns
    assert any(s.name == "sparse_columns" and s.dropped == 1 for s in chain.steps)


def test_features_exclude_the_label_and_group(raw):
    primary, _ = intermediate_to_primary(raw_to_intermediate(raw))
    features = primary_to_feature(primary)
    assert "status" not in features.columns
    assert "subject" not in features.columns
    assert "feat_a" in features.columns


def test_model_input_carries_features_label_and_group(raw):
    primary, _ = intermediate_to_primary(raw_to_intermediate(raw))
    features = primary_to_feature(primary)
    frame = join_features_and_labels(features, primary)

    data = to_model_input(frame)
    assert "status" not in data.X.columns
    assert "subject" not in data.X.columns
    assert len(data.y) == len(primary)
    assert data.groups is not None


def test_a_feature_shortlist_naming_an_unknown_column_fails(raw):
    primary, _ = intermediate_to_primary(raw_to_intermediate(raw))
    features = primary_to_feature(primary)
    with pytest.raises(KeyError):
        join_features_and_labels(features, primary, selected_feature_columns=("nope",))
