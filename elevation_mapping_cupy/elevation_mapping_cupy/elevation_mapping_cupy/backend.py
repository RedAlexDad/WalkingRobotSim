import importlib.util

import numpy as np

GPU_AVAILABLE = False
cp = None
xp = np
scipy_ndimage = None


def _detect_cuda():
    global GPU_AVAILABLE, cp, xp, scipy_ndimage

    cp_spec = importlib.util.find_spec("cupy")
    if cp_spec is None:
        import scipy.ndimage

        scipy_ndimage = scipy.ndimage
        return

    try:
        import cupy as _cp

        _cp.cuda.runtime.getDeviceCount()
        cp = _cp
        xp = _cp
        GPU_AVAILABLE = True
        import cupyx.scipy.ndimage as _cupyx_nd

        scipy_ndimage = _cupyx_nd
    except Exception:
        import scipy.ndimage

        scipy_ndimage = scipy.ndimage


def asnumpy(array, stream=None):
    if GPU_AVAILABLE and hasattr(array, "get"):
        if stream is not None:
            return array.get(stream=stream)
        return array.get()
    return np.asarray(array)


def get_stream():
    if GPU_AVAILABLE:
        return cp.cuda.Stream.null
    return None


_detect_cuda()
