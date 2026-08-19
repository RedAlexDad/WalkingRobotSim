import importlib

import numpy as np
import pytest

from .. import backend


def test_gpu_available_is_bool():
    assert isinstance(backend.GPU_AVAILABLE, bool)


def test_xp_is_numpy_or_cupy():
    assert backend.xp is np or str(backend.xp.__name__) == "cupy"


def test_asnumpy_returns_ndarray():
    arr = np.array([1.0, 2.0, 3.0])
    result = backend.asnumpy(arr)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, arr)


def test_asnumpy_with_list():
    result = backend.asnumpy([1.0, 2.0, 3.0])
    assert isinstance(result, np.ndarray)


def test_asnumpy_with_scalar():
    result = backend.asnumpy(5.0)
    assert isinstance(result, np.ndarray)


def test_asnumpy_preserves_dtype():
    arr = np.array([1, 2, 3], dtype=np.int32)
    result = backend.asnumpy(arr)
    assert result.dtype == np.int32


def test_get_stream_returns_none_without_gpu():
    if not backend.GPU_AVAILABLE:
        assert backend.get_stream() is None


def test_get_stream_with_gpu():
    if backend.GPU_AVAILABLE:
        stream = backend.get_stream()
        import cupy as cp

        assert stream is cp.cuda.Stream.null


def test_detect_cuda_no_cupy(monkeypatch):
    orig_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None if name == "cupy" else orig_find_spec(name))
    backend._detect_cuda()
    assert backend.GPU_AVAILABLE is False
    assert backend.cp is None
    assert backend.xp is np
    backend._detect_cuda()


def test_detect_cuda_cupy_import_error(monkeypatch):
    real_spec = importlib.util.find_spec("cupy")
    if real_spec is not None:

        def failing_import(name, *args, **kwargs):
            if name == "cupy":
                raise ImportError("Simulated import error")
            return __import__(name, *args, **kwargs)

        import builtins

        monkeypatch.setattr(builtins, "__import__", failing_import)
        backend._detect_cuda()
        assert backend.GPU_AVAILABLE is False
        backend._detect_cuda()
