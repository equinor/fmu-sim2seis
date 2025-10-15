import numpy as np
import pytest
import xtgeo

from fmu.sim2seis.utilities.sim2seis_class_definitions import (
    SeismicAttribute,
)


@pytest.fixture
def sample_surface():
    # Create a sample xtgeo.RegularSurface object
    surface = xtgeo.RegularSurface(ncol=10, nrow=10, xinc=1.0, yinc=1.0)
    surface.values = 0.25 * np.random.rand(10, 10)
    return surface


@pytest.fixture
def sample_seismic_attribute(sample_surface, sample_single_seismic):
    return SeismicAttribute(
        surface=sample_surface,
        calc_types=["mean"],
        from_cube=sample_single_seismic,
        domain="depth",
        window_length=2.0,
    )


def test_seismic_attribute_init(
    sample_seismic_attribute, sample_surface, sample_single_seismic
):
    assert isinstance(sample_seismic_attribute, SeismicAttribute)
    assert np.array_equal(
        sample_seismic_attribute.surface.values, sample_surface.values
    )
    assert sample_seismic_attribute.from_cube == sample_single_seismic
    assert sample_seismic_attribute.domain == "depth"
    assert sample_seismic_attribute.calc_types == ["mean"]


def test_seismic_attribute_value(sample_seismic_attribute):
    values = sample_seismic_attribute.value
    assert isinstance(values, list)
    assert len(values) == 1
    assert isinstance(values[0], xtgeo.RegularSurface)
