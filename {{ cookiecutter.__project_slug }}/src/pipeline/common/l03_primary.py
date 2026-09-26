"""L03 Primary: drop what cannot be modelled, and record what was dropped."""

from typing import Annotated

import pandas as pd

from pipeline.common.effects import FilterReportEffect
from pipeline.common.filters import FilterChain
from pipeline.common.layers import layer_step
from pipeline.settings import settings

L_PRE = "03_primary"
step_decorator = layer_step(L_PRE)


@step_decorator
def intermediate_to_primary(
    intermediate: pd.DataFrame,
    target_col: str = settings.target_col,
    reserved_cols: tuple[str, ...] = settings.reserved_cols,
    max_missing_fraction: float = settings.max_missing_fraction,
    drop_rows_with_missing_target: bool = settings.drop_rows_with_missing_target,
) -> Annotated[tuple[pd.DataFrame, FilterChain], FilterReportEffect(L_PRE)]:
    """Return the modellable rows and a record of what each rule removed."""
    chain = FilterChain()
    df = intermediate

    if drop_rows_with_missing_target:
        df = chain.apply(df, "missing_target", df[target_col].notna())

    candidates = [c for c in df.columns if c not in reserved_cols]
    sparse = [c for c in candidates if df[c].isna().mean() > max_missing_fraction]
    if sparse:
        df = df.drop(columns=sparse)
    chain.record("sparse_columns", len(candidates), len(candidates) - len(sparse))

    feature_cols = [c for c in df.columns if c not in reserved_cols]
    df = chain.apply(df, "incomplete_rows", df[feature_cols].notna().all(axis=1))

    return df.reset_index(drop=True), chain
