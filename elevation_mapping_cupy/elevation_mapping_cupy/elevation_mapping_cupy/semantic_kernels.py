import numpy as np


class SemanticKernels:
    def __init__(self, width: int = 202, height: int = 202, resolution: float = 0.05):
        self.width = width
        self.height = height
        self.resolution = resolution

    def update(self, elevation: np.ndarray) -> np.ndarray:
        return elevation
