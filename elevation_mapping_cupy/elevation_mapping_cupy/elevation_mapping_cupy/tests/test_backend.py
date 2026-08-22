import importlib
import builtins

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
    import sys

    orig_find_spec = importlib.util.find_spec
    cupy_keys = [k for k in sys.modules if k == "cupy" or k.startswith("cupy")]

    def fake_find_spec(name, *args, **kwargs):
        if name == "cupy":
            return None
        return orig_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    # Убираем cupy* из sys.modules, чтобы find_spec(None) дал сбой
    for k in cupy_keys:
        sys.modules.pop(k, None)
    backend._detect_cuda()
    assert backend.GPU_AVAILABLE is False
    assert backend.cp is None
    assert backend.xp is np
    # Восстановить: снять monkeypatch, переимпортировать cupy заново
    monkeypatch.undo()
    for k in cupy_keys:
        sys.modules.pop(k, None)
    backend._detect_cuda()
    assert backend.GPU_AVAILABLE is True


def test_detect_cuda_cupy_import_error(monkeypatch):
    real_spec = importlib.util.find_spec("cupy")
    if real_spec is not None:
        # Python 3.14: monkeypatch builtins.__import__ вызывает рекурсию,
        # т.к. внутренние импорты тоже идут через заменённую функцию.
        # Сохраняем оригинальный __import__ и перехватываем только "cupy".
        import sys

        orig_import = builtins.__import__
        cupy_keys = [k for k in sys.modules if k == "cupy" or k.startswith("cupy")]
        for k in cupy_keys:
            sys.modules.pop(k, None)

        def failing_import(name, *args, **kwargs):
            if name == "cupy":
                raise ImportError("Simulated import error")
            return orig_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", failing_import)
        backend._detect_cuda()
        assert backend.GPU_AVAILABLE is False
        # Восстановить: снять monkeypatch, переимпортировать cupy заново
        monkeypatch.undo()
        for k in cupy_keys:
            sys.modules.pop(k, None)
        backend._detect_cuda()
        assert backend.GPU_AVAILABLE is True
