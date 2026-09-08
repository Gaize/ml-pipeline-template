"""L04 Feature: one feature row per unit of analysis, carrying no labels.

Add derived features here. A value computed per row becomes a column on the
frame that flows onward, which is how later layers and the effects both see it.
"""

from typing import Annotated

import pandas as pd

from pipeline.common import features as features_module
from pipeline.common.caching import source_fingerprint
from pipeline.common.effects import DataFrameTableLogger, FeatureCorrelationEffect
from pipeline.common.features import compute_features
from pipeline.common.layers import layer_step
from pipeline.settings import settings

L_PRE = "04_feature"
step_decorator = layer_step(L_PRE)


@step_decorator
def primary_to_feature(
    primary: pd.DataFrame,
    reserved_cols: tuple[str, ...] = settings.reserved_cols,
    features_version: str = source_fingerprint(features_module),
) -> Annotated[pd.DataFrame, DataFrameTableLogger(L_PRE), FeatureCorrelationEffect(L_PRE)]:
    """Return the feature columns for each row.

    `features_version` hashes the feature code so editing it invalidates the
    cache, which the other arguments cannot describe.
    """
    del features_version
    return compute_features(primary, reserved_cols)
