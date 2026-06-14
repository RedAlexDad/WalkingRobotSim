"""
Tests for map shifting functionality.

These tests verify that the map shifts correctly when the robot moves,
ensuring X movement affects X axis and Y movement affects Y axis.

This test suite was created to prevent regression of the axis swap bug
where forward robot movement (X) was incorrectly causing sideways map shift (Y).
"""

from pathlib import Path

import numpy as np
import pytest

from elevation_mapping_cupy import elevation_mapping, parameter

from ..backend import asnumpy, xp

# Get absolute paths to config files
_TEST_DIR = Path(__file__).parent
_CONFIG_DIR = _TEST_DIR.parent.parent / "config" / "core"


@pytest.fixture
def elmap_shift():
    """Create a minimal elevation map for shift testing."""
    p = parameter.Parameter(
        use_chainer=False,
        weight_file=str(_CONFIG_DIR / "weights.dat"),
        plugin_config_file=str(_CONFIG_DIR / "plugin_config.yaml"),
    )
    # Use default resolution (0.1m) and map_length (20m) -> ~200x200 cells
    p.update()
    e = elevation_mapping.ElevationMap(p)
    e.clear()  # Start with clean map
    return e


class TestShiftMapXY:
    """Tests for the shift_map_xy function."""

    def test_shift_x_only_affects_columns(self, elmap_shift):
        center_idx = elmap_shift.cell_n // 2

        # Place a marker at the center
        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0

        # Shift by [5, 0] -> X=5 pixels, Y=0 pixels
        shift_amount = 5
        elmap_shift.shift_map_xy(xp.array([shift_amount, 0], dtype=xp.float32))

        # After X shift, marker should have moved in column direction
        new_col = center_idx + shift_amount

        assert float(elmap_shift.elevation_map[0, center_idx, new_col]) == 1.0, (
            f"Marker should be at (row={center_idx}, col={new_col}) after X shift"
        )

        new_row_wrong = center_idx + shift_amount
        assert float(elmap_shift.elevation_map[0, new_row_wrong, center_idx]) == 0.0, (
            f"Marker should NOT be at (row={new_row_wrong}, col={center_idx}) - X shift should not affect rows"
        )

    def test_shift_y_only_affects_rows(self, elmap_shift):
        center_idx = elmap_shift.cell_n // 2

        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0

        shift_amount = 5
        elmap_shift.shift_map_xy(xp.array([0, shift_amount], dtype=xp.float32))

        new_row = center_idx + shift_amount

        assert float(elmap_shift.elevation_map[0, new_row, center_idx]) == 1.0, (
            f"Marker should be at (row={new_row}, col={center_idx}) after Y shift"
        )

        new_col_wrong = center_idx + shift_amount
        assert float(elmap_shift.elevation_map[0, center_idx, new_col_wrong]) == 0.0, (
            f"Marker should NOT be at (row={center_idx}, col={new_col_wrong}) - Y shift should not affect columns"
        )

    def test_diagonal_shift(self, elmap_shift):
        center_idx = elmap_shift.cell_n // 2

        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0

        shift_x, shift_y = 3, 7
        elmap_shift.shift_map_xy(xp.array([shift_x, shift_y], dtype=xp.float32))

        expected_row = center_idx + shift_y
        expected_col = center_idx + shift_x

        assert float(elmap_shift.elevation_map[0, expected_row, expected_col]) == 1.0, (
            f"Marker should be at (row={expected_row}, col={expected_col}) after diagonal shift"
        )

    def test_negative_shift(self, elmap_shift):
        center_idx = elmap_shift.cell_n // 2

        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0

        shift_x, shift_y = -5, -3
        elmap_shift.shift_map_xy(xp.array([shift_x, shift_y], dtype=xp.float32))

        expected_row = center_idx + shift_y
        expected_col = center_idx + shift_x

        assert float(elmap_shift.elevation_map[0, expected_row, expected_col]) == 1.0, (
            f"Marker should be at (row={expected_row}, col={expected_col}) after negative shift"
        )

    def test_zero_shift_no_change(self, elmap_shift):
        center_idx = elmap_shift.cell_n // 2

        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0
        original_map = elmap_shift.elevation_map.copy()

        elmap_shift.shift_map_xy(xp.array([0, 0], dtype=xp.float32))

        assert xp.allclose(elmap_shift.elevation_map, original_map), "Zero shift should not modify the map"


class TestMoveTo:
    """Tests for the move_to function which uses shift_map_xy internally."""

    def test_move_to_x_positive(self, elmap_shift):
        initial_center = asnumpy(elmap_shift.center.copy())

        center_idx = elmap_shift.cell_n // 2
        elmap_shift.elevation_map[0, center_idx, center_idx] = 1.0

        move_distance = 1.0
        R = np.eye(3, dtype=np.float32)
        elmap_shift.move_to(np.array([move_distance, 0.0, 0.0], dtype=np.float32), R)

        new_center = asnumpy(elmap_shift.center)
        assert new_center[0] > initial_center[0], "Map center X should increase when robot moves +X"
        assert abs(new_center[1] - initial_center[1]) < 1e-6, "Map center Y should not change for X-only movement"

    def test_move_to_y_positive(self, elmap_shift):
        initial_center = asnumpy(elmap_shift.center.copy())

        move_distance = 1.0
        R = np.eye(3, dtype=np.float32)
        elmap_shift.move_to(np.array([0.0, move_distance, 0.0], dtype=np.float32), R)

        new_center = asnumpy(elmap_shift.center)
        assert new_center[1] > initial_center[1], "Map center Y should increase when robot moves +Y"
        assert abs(new_center[0] - initial_center[0]) < 1e-6, "Map center X should not change for Y-only movement"

    def test_move_to_preserves_relative_data(self, elmap_shift):
        resolution = elmap_shift.resolution
        center_idx = elmap_shift.cell_n // 2

        offset_cells = int(1.0 / resolution)
        marker_col = center_idx + offset_cells
        elmap_shift.elevation_map[0, center_idx, marker_col] = 1.0

        R = np.eye(3, dtype=np.float32)
        elmap_shift.move_to(np.array([0.5, 0.0, 0.0], dtype=np.float32), R)

        expected_new_col = marker_col - int(0.5 / resolution)

        assert float(elmap_shift.elevation_map[0, center_idx, expected_new_col]) == 1.0, (
            "Marker should maintain relative world position after robot movement"
        )


class TestPadValue:
    """Tests for padding behavior after shifts."""

    def test_positive_x_shift_pads_left(self, elmap_shift):
        elmap_shift.elevation_map[0, :, :] = 1.0

        shift_amount = 10
        elmap_shift.shift_map_xy(xp.array([shift_amount, 0], dtype=xp.float32))

        assert xp.all(elmap_shift.elevation_map[0, :, :shift_amount] == 0.0), (
            "Left edge should be padded with 0 after positive X shift"
        )

        assert xp.any(elmap_shift.elevation_map[0, :, shift_amount:] != 0.0), (
            "Right side should still have data after positive X shift"
        )

    def test_positive_y_shift_pads_top(self, elmap_shift):
        elmap_shift.elevation_map[0, :, :] = 1.0

        shift_amount = 10
        elmap_shift.shift_map_xy(xp.array([0, shift_amount], dtype=xp.float32))

        assert xp.all(elmap_shift.elevation_map[0, :shift_amount, :] == 0.0), (
            "Top edge should be padded with 0 after positive Y shift"
        )

        assert xp.any(elmap_shift.elevation_map[0, shift_amount:, :] != 0.0), (
            "Bottom side should still have data after positive Y shift"
        )
