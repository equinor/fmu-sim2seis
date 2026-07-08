import numpy as np
import pytest
import xtgeo

from fmu.sim2seis.utilities.export_with_dataio import _build_error_surface
from fmu.sim2seis.utilities.sim2seis_class_definitions import ErrorConfig


def _surface(values, ncol=3, nrow=3):
    return xtgeo.RegularSurface(
        ncol=ncol,
        nrow=nrow,
        xori=0.0,
        yori=0.0,
        xinc=1.0,
        yinc=1.0,
        values=np.array(values, dtype=float),
    )


@pytest.fixture
def attribute_map():
    return _surface([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])


def test_relative_scalar(attribute_map):
    err = _build_error_surface(attribute_map, ErrorConfig(type="relative", value=0.1))
    np.testing.assert_allclose(err.values, np.abs(attribute_map.values * 0.1))


def test_absolute_scalar(attribute_map):
    err = _build_error_surface(attribute_map, ErrorConfig(type="absolute", value=0.25))
    np.testing.assert_allclose(err.values, 0.25)


def test_relative_surface(attribute_map, tmp_path):
    error_surface = _surface([[2.0] * 3] * 3)
    path = tmp_path / "err.gri"
    error_surface.to_file(path)
    err = _build_error_surface(
        attribute_map, ErrorConfig(type="relative", error_surface=path)
    )
    np.testing.assert_allclose(err.values, np.abs(attribute_map.values * 2.0))


def test_absolute_surface(attribute_map, tmp_path):
    error_surface = _surface([[0.5, 1.0, 1.5], [2.0, 2.5, 3.0], [3.5, 4.0, 4.5]])
    path = tmp_path / "err.gri"
    error_surface.to_file(path)
    err = _build_error_surface(
        attribute_map, ErrorConfig(type="absolute", error_surface=path)
    )
    np.testing.assert_allclose(err.values, error_surface.values)


def test_geometry_mismatch_raises(attribute_map, tmp_path):
    mismatched = _surface(np.ones((4, 3)), ncol=4, nrow=3)
    path = tmp_path / "err.gri"
    mismatched.to_file(path)
    with pytest.raises(ValueError, match="same geometry"):
        _build_error_surface(
            attribute_map, ErrorConfig(type="absolute", error_surface=path)
        )
