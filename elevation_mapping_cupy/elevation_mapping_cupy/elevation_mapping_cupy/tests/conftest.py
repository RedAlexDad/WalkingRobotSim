from pathlib import Path

import numpy as np
import pytest

from ..backend import GPU_AVAILABLE, xp
from ..elevation_mapping import ElevationMap
from ..parameter import Parameter

_TEST_DIR = Path(__file__).parent
_CONFIG_DIR = _TEST_DIR.parent.parent / "config" / "core"


def pytest_collection_modifyitems(items):
    for item in items:
        if "gpu" in item.keywords:
            if not GPU_AVAILABLE:
                item.add_marker(pytest.mark.skip(reason="GPU / CuPy not available"))


@pytest.fixture(scope="function")
def param_default():
    p = Parameter(
        use_chainer=False,
        weight_file=str(_CONFIG_DIR / "weights.dat"),
        plugin_config_file=str(_CONFIG_DIR / "plugin_config.yaml"),
    )
    p.update()
    return p


@pytest.fixture(scope="function")
def param_small():
    p = Parameter(
        use_chainer=False,
        weight_file=str(_CONFIG_DIR / "weights.dat"),
        plugin_config_file=str(_CONFIG_DIR / "plugin_config.yaml"),
    )
    p.resolution = 0.2
    p.map_length = 4.0
    p.update()
    return p


@pytest.fixture(scope="function")
def elmap_default(param_default):
    return ElevationMap(param_default)


@pytest.fixture(scope="function")
def elmap_small(param_small):
    return ElevationMap(param_small)


@pytest.fixture(scope="function")
def sample_pointcloud():
    pts = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 0.5, 0.0],
            [1.0, -0.5, 0.0],
            [2.0, 0.0, 0.0],
            [2.0, 0.5, 0.0],
            [2.0, -0.5, 0.0],
        ],
        dtype=np.float32,
    )
    R = np.eye(3, dtype=np.float32)
    t = np.zeros(3, dtype=np.float32)
    return pts, R, t


@pytest.fixture(scope="function")
def sample_elevation_map():
    n = 10
    em = xp.zeros((7, n, n), dtype=xp.float32)
    em[0] = xp.random.randn(n, n).astype(xp.float32)
    em[1] = xp.ones((n, n), dtype=xp.float32) * 0.01
    em[2] = xp.ones((n, n), dtype=xp.float32)
    em[2, 0, :] = 0.0
    em[3] = xp.ones((n, n), dtype=xp.float32) * 0.8
    em[4] = xp.zeros((n, n), dtype=xp.float32)
    em[5] = xp.ones((n, n), dtype=xp.float32) * 0.5
    em[6] = xp.ones((n, n), dtype=xp.float32)
    layer_names = [
        "elevation",
        "variance",
        "is_valid",
        "traversability",
        "time",
        "upper_bound",
        "is_upper_bound",
    ]
    return em, layer_names


@pytest.fixture(scope="function")
def sample_rotation():
    R = xp.eye(3, dtype=xp.float32)
    return R
