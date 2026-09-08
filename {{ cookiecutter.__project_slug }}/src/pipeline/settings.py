"""Every tunable in the pipeline, in one documented place.

Steps take these as arguments defaulted from `settings`, never by reading the
module from inside a body: KissML hashes arguments, so a value read from a body
never moves the cache key.
"""

from pathlib import Path

from pydantic import BaseModel, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Training(BaseModel):
    """Cross-validation and hyperparameter search configuration."""

    n_splits: int = 5
    """Number of cross-validation folds. With a group column, the rarest class must
    have at least this many groups or a fold ends up empty."""

    n_iterations: int = 10
    """Number of independent grid searches, each with its own fold assignment. The
    spread across iterations is the estimate of how much the score depends on the split."""

    base_random_state: int = 42
    """Seed for iteration 0; iteration i uses base_random_state + i."""

    scoring: str = "roc_auc"
    """Scikit-learn scoring name used to rank candidates during the search."""


class Reporting(BaseModel):
    """Evaluation and figure configuration for L08."""

    fbeta: float = 1.0
    """Beta for the F-beta operating threshold. Below 1 weights precision (a false
    positive costs more than a false negative); above 1 weights recall."""

    n_bootstrap: int = 1000
    """Resamples used for the confidence interval around each headline metric."""

    n_permutations: int = 500
    """Label shuffles in the significance test. Scores are held fixed and only the
    labels are permuted, so nothing refits."""

    learning_curve_sizes: tuple[float, ...] = (0.2, 0.4, 0.6, 0.8, 1.0)
    """Training-set fractions at which the learning curve is evaluated."""

    shap_enabled: bool = True
    """Whether L08 computes SHAP values. Disable when the estimator is slow to explain."""


class Settings(BaseSettings):
    """Configuration for the pipeline, overridable by environment or a `.env` file."""

    model_config = SettingsConfigDict(
        env_prefix="PIPELINE_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # --- Data ---

    data_path: Path = Path("data/parkinsons.csv")
    """Source table for L01. Any CSV or Parquet file pandas can read."""

    target_col: str = "status"
    """Column holding the binary label. Values must be castable to 0 and 1."""

    id_col: str = "name"
    """Column identifying a row in the source table. Never used as a feature."""

    group_col: str | None = "subject"
    """Column identifying the unit that rows repeat over, or None if they do not.

    If several rows describe the same person, session, or device, that column goes
    here: folds that split one unit across train and test score the model on
    something it has already seen. Set None only when rows are genuinely
    independent. L02 derives the bundled dataset's value from the recording name."""

    drop_cols: tuple[str, ...] = ()
    """Columns excluded from the feature matrix beyond the target, id, and group."""

    selected_feature_columns: tuple[str, ...] | None = None
    """Feature shortlist, or None to use every numeric column L04 produces. Changing
    this invalidates the training cache without recomputing features."""

    # --- Cleaning (L03) ---

    max_missing_fraction: float = 0.5
    """Feature columns missing more than this fraction of values are dropped."""

    drop_rows_with_missing_target: bool = True
    """Whether rows with no label are dropped rather than imputed."""

    # --- Model (L06) ---

    class_weight_balanced: bool = True
    """Whether the estimator reweights classes by inverse frequency. Leave on for an
    imbalanced target so the minority class is not ignored."""

    training: Training = Training()
    """Cross-validation and search configuration."""

    reporting: Reporting = Reporting()
    """Evaluation configuration."""

    # --- Tracking ---

    mlflow_tracking_uri: str = "sqlite:///mlflow.db"
    """MLflow backend store. The default is a file beside the pipeline, so runs work
    offline; point it at a server to share results."""

    mlflow_experiment: str = "{{ cookiecutter.project_name }}"
    """MLflow experiment name that runs are logged under."""

    cache_directory: Path = Path.home() / ".kissml"
    """Root of the KissML step cache."""

    cache_namespace: str = "{{ cookiecutter.__project_slug }}"
    """Cache subdirectory for this pipeline, so its entries can be evicted alone."""

    # --- Submission ---

    submission_dir: Path = Path("submissions")
    """Directory that `--submit` writes prediction files into."""

    test_data_path: Path | None = None
    """Held-out table to predict for a submission, or None when there is none."""

    @field_validator("group_col", "test_data_path", mode="before")
    @classmethod
    def _blank_is_none(cls, value: object) -> object:
        """Read an empty environment variable as unset rather than as an empty name.

        `PIPELINE_GROUP_COL=` is how grouping is turned off from the shell, and
        without this it would name a column called "".
        """
        return None if value == "" else value

    @computed_field
    @property
    def reserved_cols(self) -> tuple[str, ...]:
        """Columns that are never features, derived from the id, target, and group."""
        cols = [self.id_col, self.target_col, *self.drop_cols]
        if self.group_col is not None:
            cols.append(self.group_col)
        return tuple(dict.fromkeys(cols))


settings = Settings()
