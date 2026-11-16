"""Tests for slope and aspect. Skipped where the ML libraries are not installed (e.g. CI)."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from imagery.terrain import slope_aspect  # noqa: E402

DX = np.full(5, 30.0)   # 30 m pixels
DY = 30.0


def _plane(rise_per_pixel_east=0.0, rise_per_pixel_north=0.0):
    rows, cols = np.mgrid[0:5, 0:5].astype(float)
    return cols * rise_per_pixel_east - rows * rise_per_pixel_north   # row 0 is the northern edge


def test_flat_ground_has_no_slope_or_aspect():
    slope, north, east = slope_aspect(np.full((5, 5), 100.0), DX, DY)
    assert np.allclose(slope, 0) and np.allclose(north, 0) and np.allclose(east, 0)


def test_45_degree_slope():
    slope, _, _ = slope_aspect(_plane(rise_per_pixel_east=30.0), DX, DY)   # 30 m up per 30 m across
    assert np.allclose(slope, 45.0)


def test_ground_rising_northwards_faces_south():
    _, north, east = slope_aspect(_plane(rise_per_pixel_north=3.0), DX, DY)
    assert np.allclose(north, -1.0) and np.allclose(east, 0.0)


def test_ground_rising_eastwards_faces_west():
    _, north, east = slope_aspect(_plane(rise_per_pixel_east=3.0), DX, DY)
    assert np.allclose(east, -1.0) and np.allclose(north, 0.0)


def test_narrower_pixels_make_the_same_rise_steeper():
    wide, _, _ = slope_aspect(_plane(rise_per_pixel_east=3.0), np.full(5, 30.0), DY)
    narrow, _, _ = slope_aspect(_plane(rise_per_pixel_east=3.0), np.full(5, 15.0), DY)
    assert narrow.mean() > wide.mean()
