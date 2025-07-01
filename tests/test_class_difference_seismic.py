from pathlib import Path

import numpy as np
import pytest
import xtgeo

from fmu.sim2seis.utilities.sim2seis_class_definitions import (
    DifferenceSeismic,
    SingleSeismic,
)


@pytest.fixture
def sample_difference_seismic(sample_single_seismic):
    # Create a second SingleSeismic object with different cube values
    cube = xtgeo.Cube(ncol=10, nrow=10, nlay=10, xinc=1.0, yinc=1.0, zinc=1.0)
    cube.values = np.random.rand(10, 10, 10)
    monitor_seismic = SingleSeismic(
        from_dir=Path("/path/to/dir"),
        cube_name=sample_single_seismic.cube_name,
        cube=cube,
        date="20200202"
    )
    return DifferenceSeismic(
        base=sample_single_seismic,
        monitor=monitor_seismic
    )

def test_difference_seismic_init(sample_difference_seismic, sample_single_seismic):
    assert isinstance(sample_difference_seismic, DifferenceSeismic)
    assert sample_difference_seismic.base == sample_single_seismic
    assert sample_difference_seismic.monitor.cube_name == sample_single_seismic.cube_name  # noqa: E501

def test_difference_seismic_dates(sample_difference_seismic):
    assert sample_difference_seismic.date == "20200202_20200101"
    assert sample_difference_seismic.monitor_date == "20200202"
    assert sample_difference_seismic.base_date == "20200101"

def test_difference_seismic_cube(sample_difference_seismic):
    diff_cube = sample_difference_seismic.cube
    expected_diff_values = (
            sample_difference_seismic.monitor.cube.values -
            sample_difference_seismic.base.cube.values
    )
    assert np.array_equal(diff_cube.values, expected_diff_values)
