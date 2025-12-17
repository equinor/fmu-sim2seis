from unittest.mock import Mock

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
    assert sample_seismic_attribute.calc_types == ["mean"]


def test_seismic_attribute_value(sample_seismic_attribute):
    values = sample_seismic_attribute.value
    assert isinstance(values, list)
    assert len(values) == 1
    assert isinstance(values[0], xtgeo.RegularSurface)


def test_seismic_attribute_with_window_length_calculates_bottom_surface():
    """Test that bottom_surface is calculated when window_length is provided."""
    surface = Mock(spec=xtgeo.RegularSurface)
    intermediate = Mock(spec=xtgeo.RegularSurface)
    final = Mock(spec=xtgeo.RegularSurface)

    surface.__add__ = Mock(return_value=intermediate)
    intermediate.__add__ = Mock(return_value=final)

    cube = Mock()

    attr = SeismicAttribute(
        surface=surface,
        calc_types=["rms"],
        from_cube=cube,
        window_length=25.0,
        top_surface_shift=5.0,
    )

    # Verify: surface + top_shift + window_length
    surface.__add__.assert_called_once_with(5.0)
    intermediate.__add__.assert_called_once_with(25.0)
    assert attr.bottom_surface is final
    assert attr.bottom_surface_shift == 0.0  # Should be zeroed


def test_seismic_attribute_with_provided_bottom_surface():
    """Test that provided bottom_surface is used and not recalculated."""
    top_surface = Mock(spec=xtgeo.RegularSurface)
    bottom_surface = Mock(spec=xtgeo.RegularSurface)
    cube = Mock()

    attr = SeismicAttribute(
        surface=top_surface,
        calc_types=["mean"],
        from_cube=cube,
        bottom_surface=bottom_surface,
        bottom_surface_shift=10.0,
    )

    # bottom_surface should not be modified
    assert attr.bottom_surface is bottom_surface
    assert attr.bottom_surface_shift == 10.0  # Should NOT be zeroed
    assert attr.window_length is None


def test_seismic_attribute_value_applies_scale_factor():
    """Test that value property applies scale_factor correctly."""
    surface = Mock(spec=xtgeo.RegularSurface)
    bottom_surface = Mock(spec=xtgeo.RegularSurface)

    surface.__add__ = Mock(return_value=surface)
    bottom_surface.__add__ = Mock(return_value=bottom_surface)

    mock_result_surface = Mock(spec=xtgeo.RegularSurface)

    cube_obj = Mock()
    cube_obj.compute_attributes_in_window = Mock(
        return_value={"rms": mock_result_surface}
    )

    cube = Mock()
    cube.cube = cube_obj

    attr = SeismicAttribute(
        surface=surface,
        calc_types=["rms"],
        from_cube=cube,
        bottom_surface=bottom_surface,
        scale_factor=2.5,
        top_surface_shift=3.0,
        bottom_surface_shift=7.0,
    )

    # Mock the multiplication
    mock_result_surface.__mul__ = Mock(return_value="scaled_result")

    values = attr.value

    # Verify compute_attributes_in_window was called with shifted surfaces
    cube_obj.compute_attributes_in_window.assert_called_once_with(surface, bottom_surface)

    # Verify scale_factor was applied
    mock_result_surface.__mul__.assert_called_once_with(2.5)
    assert values == ["scaled_result"]


def test_seismic_attribute_multiple_calc_types():
    """Test with multiple calculation types."""
    surface = Mock(spec=xtgeo.RegularSurface)
    bottom_surface = Mock(spec=xtgeo.RegularSurface)

    surface.__add__ = Mock(return_value=surface)
    bottom_surface.__add__ = Mock(return_value=bottom_surface)

    rms_result = Mock(spec=xtgeo.RegularSurface)
    mean_result = Mock(spec=xtgeo.RegularSurface)
    rms_result.__mul__ = Mock(return_value="rms_scaled")
    mean_result.__mul__ = Mock(return_value="mean_scaled")

    cube_obj = Mock()
    cube_obj.compute_attributes_in_window = Mock(
        return_value={"rms": rms_result, "mean": mean_result}
    )

    cube = Mock()
    cube.cube = cube_obj

    attr = SeismicAttribute(
        surface=surface,
        calc_types=["rms", "mean"],
        from_cube=cube,
        bottom_surface=bottom_surface,
    )

    values = attr.value

    assert len(values) == 2
    assert values == ["rms_scaled", "mean_scaled"]


def test_seismic_attribute_fails_without_bottom_surface_or_window():
    """Test that initialization fails without bottom_surface or window_length."""
    surface = Mock(spec=xtgeo.RegularSurface)
    cube = Mock()

    with pytest.raises(
        ValueError, match="Must specify either 'bottom_surface' or 'window_length'!"
    ):
        SeismicAttribute(
            surface=surface,
            calc_types=["rms"],
            from_cube=cube,
            # Missing both bottom_surface and window_length
        )


def test_seismic_attribute_window_length_zero_shift():
    """Test window_length calculation with zero top_surface_shift."""
    surface = Mock(spec=xtgeo.RegularSurface)
    intermediate = Mock(spec=xtgeo.RegularSurface)
    final = Mock(spec=xtgeo.RegularSurface)

    surface.__add__ = Mock(return_value=intermediate)
    intermediate.__add__ = Mock(return_value=final)

    cube = Mock()

    SeismicAttribute(
        surface=surface,
        calc_types=["mean"],
        from_cube=cube,
        window_length=10.0,
        # top_surface_shift defaults to 0.0
    )

    # Should add 0.0 then 10.0
    surface.__add__.assert_called_once_with(0.0)
    intermediate.__add__.assert_called_once_with(10.0)
