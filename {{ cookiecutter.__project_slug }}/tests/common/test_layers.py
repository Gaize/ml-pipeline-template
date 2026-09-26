import numpy as np
from kissml.settings import settings as kissml_settings

from pipeline.common.layers import layer_cache, layer_step


def test_ndarray_hasher_is_registered():
    assert np.ndarray in kissml_settings.hash_by_type


def test_large_arrays_differing_in_the_middle_hash_differently():
    hasher = kissml_settings.hash_by_type[np.ndarray]
    a = np.zeros(5000)
    b = a.copy()
    b[2500] = 1.0
    assert hasher(a) != hasher(b)


def test_each_layer_gets_its_own_namespace():
    assert layer_cache("01_raw").namespace != layer_cache("02_intermediate").namespace


def test_layer_step_returns_a_decorator():
    decorator = layer_step("01_raw")

    @decorator
    def f(x: int) -> int:
        return x + 1

    assert f(1) == 2
    assert getattr(f, "__kissml_kind__", None) == "step"
