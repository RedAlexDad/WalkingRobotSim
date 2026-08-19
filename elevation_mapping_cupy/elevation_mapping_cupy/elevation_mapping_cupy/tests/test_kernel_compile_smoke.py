from __future__ import annotations

from pathlib import Path

import numpy as np

from ..backend import GPU_AVAILABLE, xp
from ..elevation_mapping import ElevationMap
from ..parameter import Parameter


def test_backend_available():
    assert xp is not None
    assert xp == np or GPU_AVAILABLE


def test_kernels_compile_and_one_update_step_runs():
    root = Path(__file__).resolve().parents[2]
    p = Parameter(
        use_chainer=False,
        weight_file=str(root / "config" / "core" / "weights.dat"),
        plugin_config_file=str(root / "config" / "core" / "plugin_config.yaml"),
    )

    p.resolution = 0.2
    p.map_length = 4.0
    p.update()

    emap = ElevationMap(p)

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

    emap.input_pointcloud(pts, ["x", "y", "z"], R, t, 0.0, 0.0)
    emap.update_variance()
    emap.update_time()
