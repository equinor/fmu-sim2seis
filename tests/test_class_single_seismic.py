from pathlib import Path

import numpy as np
import xtgeo

from fmu.sim2seis.utilities.sim2seis_class_definitions import (
    SeismicDate,
    SeismicName,
    SingleSeismic,
)


def test_single_seismic_init(sample_single_seismic, sample_cube, sample_seismic_name):
    assert isinstance(sample_single_seismic, SingleSeismic)
    assert sample_single_seismic.from_dir == Path("/path/to/dir")
    assert sample_single_seismic.cube_name == sample_seismic_name
    assert sample_single_seismic.cube == sample_cube
    assert sample_single_seismic.date == "20200101"

def test_single_seismic_date(sample_single_seismic):
    sample_single_seismic.date = "20200202"
    assert sample_single_seismic.date == "20200202"
    sample_single_seismic.date = SeismicDate("20200303")
    assert sample_single_seismic.date == "20200303"

def test_single_seismic_monitor_date(sample_single_seismic):
    assert sample_single_seismic.monitor_date is None
    sample_single_seismic.date = "20200101_20200202"
    assert sample_single_seismic.monitor_date == "20200202"

def test_single_seismic_base_date(sample_single_seismic):
    assert sample_single_seismic.base_date is None
    # Note: SeismicDate checks which part of a date string represents
    # monitor (the most recent) and base (the oldest) dates. In this
    # case they are swapped.
    sample_single_seismic.date = "20200101_20200202"
    assert sample_single_seismic.base_date == "20200101"

def test_single_seismic_from_dir(sample_single_seismic):
    sample_single_seismic.from_dir = Path("/new/path/to/dir")
    assert sample_single_seismic.from_dir == Path("/new/path/to/dir")

def test_single_seismic_cube_name(sample_single_seismic):
    new_cube_name = SeismicName(
        process="syntseis",
        attribute="amplitude",
        domain="time",
        date="20200202",
        stack="near",
        ext="segy"
    )
    sample_single_seismic.cube_name = new_cube_name
    assert sample_single_seismic.cube_name == new_cube_name

def test_single_seismic_cube(sample_single_seismic):
    new_cube = xtgeo.Cube(ncol=5, nrow=5, nlay=5, xinc=1.0, yinc=1.0, zinc=1.0)
    new_cube.values = np.random.rand(5, 5, 5)
    sample_single_seismic.cube = new_cube
    assert sample_single_seismic.cube == new_cube
