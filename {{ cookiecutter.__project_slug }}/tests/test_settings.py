from pipeline.settings import Settings


def test_blank_group_col_env_var_disables_grouping(monkeypatch):
    """`PIPELINE_GROUP_COL=` is the documented way to turn grouping off."""
    monkeypatch.setenv("PIPELINE_GROUP_COL", "")
    assert Settings().group_col is None


def test_group_col_env_var_names_a_column(monkeypatch):
    monkeypatch.setenv("PIPELINE_GROUP_COL", "patient_id")
    assert Settings().group_col == "patient_id"


def test_reserved_cols_include_the_group_when_it_is_set():
    settings = Settings(group_col="subject")
    assert set(settings.reserved_cols) == {"name", "status", "subject"}


def test_reserved_cols_omit_the_group_when_it_is_unset():
    settings = Settings(group_col=None)
    assert set(settings.reserved_cols) == {"name", "status"}
