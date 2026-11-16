"""Tests for the distance-per-cell calculation. Skipped where the ML libraries are not installed."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("rasterio")
pytest.importorskip("osmium")
pytest.importorskip("scipy")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ml.features_static import SUB, mean_distance_per_cell  # noqa: E402


def test_cell_containing_the_feature_is_nearest_and_order_is_south_first():
    # 2 x 2 grid cells; one feature in the north-west cell (raster row 0 is the north edge).
    mask = np.zeros((2 * SUB, 2 * SUB), dtype=bool)
    mask[0, 0] = True
    d = mean_distance_per_cell(mask, 100.0)
    # cell_id order: row 0 = south. So ids are [SW, SE, NW, NE].
    sw, se, nw, ne = d
    assert nw == d.min()
    assert ne > nw and sw > nw and se > max(ne, sw)


def test_feature_everywhere_gives_zero_distance():
    d = mean_distance_per_cell(np.ones((SUB, SUB), dtype=bool), 100.0)
    assert np.allclose(d, 0.0)


def test_distance_is_in_metres():
    # One feature column on the west edge of a single cell: mean distance over columns 0..9 = 450 m.
    mask = np.zeros((SUB, SUB), dtype=bool)
    mask[:, 0] = True
    assert mean_distance_per_cell(mask, 100.0)[0] == pytest.approx(450.0)


def test_no_features_is_an_error():
    with pytest.raises(ValueError):
        mean_distance_per_cell(np.zeros((SUB, SUB), dtype=bool), 100.0)
