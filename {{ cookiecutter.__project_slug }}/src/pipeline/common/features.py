"""Feature computation, kept free of pipeline imports so it stays testable alone."""

import pandas as pd


def compute_features(df: pd.DataFrame, reserved_cols: tuple[str, ...]) -> pd.DataFrame:
    """Return the numeric feature columns of `df`, excluding the reserved ones.

    This is the seam to extend: derive new columns from `df` and return them
    alongside the passthrough features.
    """
    numeric = df.select_dtypes("number")
    feature_cols = [c for c in numeric.columns if c not in reserved_cols]
    return df[feature_cols].copy()
