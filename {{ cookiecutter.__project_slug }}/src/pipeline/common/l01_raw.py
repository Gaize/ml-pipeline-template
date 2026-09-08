"""L01 Raw: load the source table unchanged.

Nothing here filters, types, or enriches. Keeping this step narrow keeps its
cache key stable, so editing later layers never reloads the source.
"""

from pathlib import Path
from typing import Annotated

import pandas as pd

from pipeline.common.effects import DataFrameStatsLogger, DataFrameTableLogger
from pipeline.common.layers import layer_step
from pipeline.settings import settings

L_PRE = "01_raw"
step_decorator = layer_step(L_PRE)


@step_decorator
def load_raw(
    data_path: Path = settings.data_path,
) -> Annotated[pd.DataFrame, DataFrameTableLogger(L_PRE), DataFrameStatsLogger(L_PRE)]:
    """Read the source table as it sits on disk.

    Reads Parquet when the suffix says so and CSV otherwise.
    """
    if not data_path.exists():
        raise FileNotFoundError(
            f"No source table at {data_path}. Set PIPELINE_DATA_PATH or settings.data_path."
        )
    if data_path.suffix in {".parquet", ".pq"}:
        return pd.read_parquet(data_path)
    return pd.read_csv(data_path)
