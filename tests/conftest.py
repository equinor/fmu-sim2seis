from pathlib import Path
from shutil import copy2, copytree

import numpy as np
import pytest
import xtgeo
import yaml
from fmu.settings._drogon import create_drogon_fmu_dir

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
        "./share/preprocessed/cubes",
        "./share/results/cubes",
        "./share/results/pickle_files",
        "./share/results/tables",
        "./sim2seis/output/pem",
        "./sim2seis/input/pem",
    ]
    for make_dir in dirs_to_make:
        config_dir.joinpath(make_dir).mkdir(parents=True, exist_ok=True)

    special_files = [
        "./share/preprocessed/cubes/test_data/seismic--amplitude_full_time--20180701_20180101.segy",
        "./share/preprocessed/cubes/test_data/seismic--amplitude_full_time--20190701_20180101.segy",
        "./share/preprocessed/cubes/test_data/seismic--amplitude_full_time--20200701_20180101.segy",
        "./share/preprocessed/cubes/test_data/seismic--relai_full_time--20180701_20180101.segy",
        "./share/preprocessed/cubes/test_data/seismic--relai_full_time--20190701_20180101.segy",
        "./share/preprocessed/cubes/test_data/seismic--relai_full_time--20200701_20180101.segy",
    ]
    for filename in special_files:
        copy2(
            Path(testdata) / filename, config_dir / filename.replace("test_data/", "")
        )
    # The shipped sim2seis_config.yml is a clean template, where test_run stays at
    # its default (False) for real runs. Enable it in the copied test tree so
    # OBSERVED_DATA uses the copied observed cubes instead of symlinking the real
    # /scratch seismic data, which is absent in the fixture.
    config_file = config_dir / "sim2seis" / "model" / "sim2seis_config.yml"
    with open(config_file) as fin:
        config_data = yaml.safe_load(fin)
    config_data["test_run"] = True
    with open(config_file, "w") as fout:
        yaml.safe_dump(config_data, fout)
    # Create required .fmu directory
    create_drogon_fmu_dir(base_path=config_dir)
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
