from pathlib import Path
from shutil import copy2, copytree

import numpy as np
import pytest
import xtgeo

from fmu.sim2seis.utilities.sim2seis_class_definitions import (
    DifferenceSeismic,
    SeismicName,
    SingleSeismic,
)


@pytest.fixture(scope="session")
def testdata() -> Path:
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session", autouse=True, name="data_dir")
def setup_sim2seis_test_data(testdata, tmp_path_factory):
    config_dir = tmp_path_factory.mktemp("data")
    # Copy data directory tree
    copytree(testdata, config_dir, dirs_exist_ok=True)

    # List all directories that must be created, relative to config_dir
    dirs_to_make = [
        "./sim2seis/model",
        "./share/observations/tables",
        "./share/results/cubes",
        "./share/results/pickle_files",
        "./share/results/tables",
        "./sim2seis/output/pem",
    ]
    for make_dir in dirs_to_make:
        config_dir.joinpath(make_dir).mkdir(parents=True, exist_ok=True)

    special_files = [
        "./share/observations/cubes/test_data/seismic--amplitude_time--20180701_20180101.segy",
        "./share/observations/cubes/test_data/seismic--amplitude_time--20190701_20180101.segy",
        "./share/observations/cubes/test_data/seismic--amplitude_time--20200701_20180101.segy",
        "./share/observations/cubes/test_data/seismic--relai_time--20180701_20180101.segy",
        "./share/observations/cubes/test_data/seismic--relai_time--20190701_20180101.segy",
        "./share/observations/cubes/test_data/seismic--relai_time--20200701_20180101.segy",
    ]
    for filename in special_files:
        copy2(
            Path(testdata) / filename, config_dir / filename.replace("test_data/", "")
        )
    return config_dir


@pytest.fixture
def sample_cube():
    # Create a sample xtgeo.Cube object with required parameters
    cube = xtgeo.Cube(ncol=10, nrow=10, nlay=10, xinc=1.0, yinc=1.0, zinc=1.0)
    cube.values = np.random.rand(10, 10, 10)
    return cube


@pytest.fixture
def sample_seismic_name():
    return SeismicName(
        process="seismic",
        attribute="relai",
        domain="depth",
        date="20200101",
        stack="full",
        ext="segy",
    )


@pytest.fixture
def sample_single_seismic(sample_cube, sample_seismic_name):
    return SingleSeismic(
        from_dir=Path("/path/to/dir"),
        cube_name=sample_seismic_name,
        cube=sample_cube,
        date="20200101",
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
        date="20200202",
    )
    return DifferenceSeismic(base=sample_single_seismic, monitor=monitor_seismic)
