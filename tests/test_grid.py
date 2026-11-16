"""Tests for the grid cell mapping. Skipped where the ML libraries are not installed (e.g. CI)."""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("rasterio")
pytest.importorskip("geopandas")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from imagery.grid import cell_index  # noqa: E402

X0, Y0, SIZE, NCOL, NROW = 170000.0, 3177000.0, 1000.0, 335, 305


def test_cell_centre_maps_to_its_own_cell():
    row, col, ok = cell_index([X0 + 2500.0], [Y0 + 7500.0], X0, Y0, SIZE, NCOL, NROW)
    assert (row[0], col[0], bool(ok[0])) == (7, 2, True)


def test_cell_edges_belong_to_the_cell_on_the_upper_side():
    # A point exactly on a boundary goes to the cell that starts there.
    row, col, ok = cell_index([X0 + 1000.0, X0 + 999.999], [Y0, Y0], X0, Y0, SIZE, NCOL, NROW)
    assert list(col) == [1, 0] and list(row) == [0, 0] and ok.all()


def test_points_outside_the_grid_are_flagged():
    xs = [X0 - 1.0, X0 + NCOL * SIZE, X0 + 10.0, X0 + 10.0]
    ys = [Y0 + 10.0, Y0 + 10.0, Y0 - 1.0, Y0 + NROW * SIZE]
    _, _, ok = cell_index(xs, ys, X0, Y0, SIZE, NCOL, NROW)
    assert not ok.any()


def test_last_cell_is_inside():
    row, col, ok = cell_index([X0 + NCOL * SIZE - 0.5], [Y0 + NROW * SIZE - 0.5], X0, Y0, SIZE, NCOL, NROW)
    assert (row[0], col[0], bool(ok[0])) == (NROW - 1, NCOL - 1, True)
