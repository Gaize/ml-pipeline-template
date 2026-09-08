"""Cache and step decorators shared by the layer modules.

Each layer builds its decorator from its own prefix, so one layer's cached
entries live together on disk and can be evicted without touching the others.
"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np
from kissml import CacheConfig, step
from kissml.settings import settings as kissml_settings

from pipeline.settings import settings


def _hash_ndarray(value: np.ndarray) -> str:
    """Return a content hash of an array.

    KissML's fallback hasher is `str(value)`, which numpy elides past 1000
    elements, so two large arrays differing only in the middle would collide.
    """
    return f"{value.shape}-{value.dtype}-{hash(value.tobytes())}"


kissml_settings.hash_by_type[np.ndarray] = _hash_ndarray
kissml_settings.cache_directory = settings.cache_directory


def layer_cache(namespace: str) -> CacheConfig:
    """Return the cache configuration for one layer."""
    return CacheConfig(version=1, namespace=f"{settings.cache_namespace}/{namespace}")


def layer_step(namespace: str) -> Callable[..., Any]:
    """Return a `@step` decorator that caches into one layer's namespace."""
    return step(cache=layer_cache(namespace), log_level=logging.INFO)
