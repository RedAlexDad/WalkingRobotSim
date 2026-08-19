import elevation_mapping_cupy.gridmap_utils as emn
import numpy as np
import pytest
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, MultiArrayLayout


def _make_manual_gridmap_column(
    rows: int, cols: int
) -> tuple[np.ndarray, Float32MultiArray]:
    """Build a Float32MultiArray with GridMap-style column-major layout."""
    data = np.arange(rows * cols, dtype=np.float32).reshape((rows, cols))
    msg = Float32MultiArray()
    msg.layout = MultiArrayLayout()
    msg.layout.dim.append(
        MultiArrayDimension(label="column_index", size=cols, stride=rows * cols)
    )
    msg.layout.dim.append(
        MultiArrayDimension(label="row_index", size=rows, stride=rows)
    )
    msg.data = data.flatten(order="F").tolist()
    return data, msg


def test_encode_decode_column_major_roundtrip():
    arr = np.arange(12, dtype=np.float32).reshape((3, 4))
    msg = emn.encode_layer_to_multiarray(arr, layout="gridmap_column")
    out = emn.decode_multiarray_to_rows_cols("elevation", msg)
    assert np.array_equal(arr, out)


def test_encode_decode_row_major_roundtrip():
    arr = np.arange(6, dtype=np.float32).reshape((2, 3))
    msg = emn.encode_layer_to_multiarray(arr, layout="row_major")
    out = emn.decode_multiarray_to_rows_cols("elevation", msg)
    assert np.array_equal(arr, out)


def test_decode_manual_gridmap_column_major():
    arr, msg = _make_manual_gridmap_column(rows=3, cols=4)
    out = emn.decode_multiarray_to_rows_cols("elevation", msg)
    assert np.array_equal(arr, out)


def test_encode_unknown_layout_raises():
    arr = np.arange(6, dtype=np.float32).reshape((2, 3))
    with pytest.raises(ValueError, match="Unknown layout"):
        emn.encode_layer_to_multiarray(arr, layout="invalid")


def test_decode_inconsistent_metadata_raises():
    msg = Float32MultiArray()
    msg.layout = MultiArrayLayout()
    msg.layout.dim.append(MultiArrayDimension(label="row_index", size=2, stride=6))
    msg.layout.dim.append(MultiArrayDimension(label="column_index", size=3, stride=3))
    msg.data = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError, match="inconsistent layout"):
        emn.decode_multiarray_to_rows_cols("test", msg)


def test_decode_empty_dims_fallback():
    msg = Float32MultiArray()
    msg.layout = MultiArrayLayout()
    msg.layout.dim.append(MultiArrayDimension(label="", size=0, stride=0))
    msg.data = [1.0, 2.0, 3.0, 4.0]
    out = emn.decode_multiarray_to_rows_cols("test", msg)
    assert out.shape == (4, 1)


def test_decode_no_dims_fallback():
    msg = Float32MultiArray()
    msg.layout = MultiArrayLayout()
    msg.data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    out = emn.decode_multiarray_to_rows_cols("test", msg)
    assert out.shape == (3, 3)
