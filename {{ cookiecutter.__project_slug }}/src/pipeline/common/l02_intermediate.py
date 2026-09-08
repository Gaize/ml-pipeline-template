"""L02 Intermediate: type the raw table and derive the columns later layers need.

The group column is derived here, so every layer below sees the same frame
whether or not grouping is switched on.
"""

from typing import Annotated

import pandas as pd

from pipeline.common.effects import ClassBalanceLogger, DataFrameTableLogger
from pipeline.common.layers import layer_step
from pipeline.settings import settings

L_PRE = "02_intermediate"
step_decorator = layer_step(L_PRE)


def derive_subject(names: pd.Series) -> pd.Series:
    """Return the subject key of each recording name.

    The bundled Parkinson's recordings are named `phon_R01_S01_1`, where the
    trailing index distinguishes repeated recordings of one speaker. Dropping it
    leaves the speaker, which is the unit that must not span a fold boundary.
    """
    return names.astype(str).str.rsplit("_", n=1).str[0]


@step_decorator
def raw_to_intermediate(
    raw: pd.DataFrame,
    target_col: str = settings.target_col,
    id_col: str = settings.id_col,
    group_col: str | None = settings.group_col,
) -> Annotated[
    pd.DataFrame,
    DataFrameTableLogger(L_PRE),
    ClassBalanceLogger(L_PRE, settings.target_col),
]:
    """Cast the label to integers and add the group column when one is configured."""
    df = raw.copy()
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce").astype("Int64")

    if group_col is not None and group_col not in df.columns:
        if id_col not in df.columns:
            raise KeyError(
                f"Cannot derive group column {group_col!r}: no {id_col!r} column to derive it from."
            )
        df[group_col] = derive_subject(df[id_col])

    return df
