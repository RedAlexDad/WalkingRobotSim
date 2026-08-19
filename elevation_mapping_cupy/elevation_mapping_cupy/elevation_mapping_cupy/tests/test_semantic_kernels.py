import numpy as np
import pytest

from ..backend import GPU_AVAILABLE, xp


class TestSemanticKernels:
    def test_importable(self):
        from ..semantic_kernels import SemanticKernels
        assert SemanticKernels is not None

    def test_init_default(self):
        from ..semantic_kernels import SemanticKernels
        sk = SemanticKernels()
        assert hasattr(sk, "update")

    def test_update_returns_layers(self):
        from ..semantic_kernels import SemanticKernels
        sk = SemanticKernels()
        n = 10
        elevation = xp.random.randn(n, n).astype(xp.float32)
        result = sk.update(elevation)
        assert result is not None
