import os
import pickle
import subprocess
from pathlib import Path

import pandas as pd
import xtgeo.surface
from numpy import isclose

from fmu.sim2seis.utilities import DifferenceSeismic, SeismicAttribute, SingleSeismic

# If there is a need to re-calibrate the test, set CALIBRATE to True
CALIBRATE = False
a_tol = 0.05
r_tol = 0.001


def get_sum_value(file_name: Path) -> float:
    """
    Read different file types, get the value property of the objects and return
    a sum of the values.
    """

    def get_gri_sum_value(f_name: Path) -> float:
        surf = xtgeo.surface_from_file(str(f_name))
        return surf.values.sum()

    def get_segy_sum_value(f_name: Path) -> float:
        cube = xtgeo.cube_from_file(str(f_name))
        return cube.values.sum()

    def get_csv_sum_value(f_name: Path) -> float:
        df = pd.read_csv(f_name)
        return df.values.sum()

    def get_attribute_sum_value(attr: SeismicAttribute) -> float:
        return sum(single_attribute.values.sum() for single_attribute in attr.value)

    def get_seismic_sum(single_seismic: SingleSeismic | DifferenceSeismic) -> float:
        return single_seismic.cube.values.sum()

    def get_pickle_sum_value(f_name: Path) -> float:
        """
        The pickle object can be a single class object, a dict or a list
        """
        with open(f_name, "rb") as fin:
            pickle_obj = pickle.load(fin)

        value_list = []
        if isinstance(pickle_obj, dict):
            obj_list = list(pickle_obj.values())
        elif isinstance(
            pickle_obj, (SingleSeismic, DifferenceSeismic, SeismicAttribute)
        ):
            obj_list = [pickle_obj]
        elif isinstance(pickle_obj, list):
            obj_list = pickle_obj  # already a list
        else:
            raise ValueError(f"unknown pickle object {type(pickle_obj)}")

        for instance in obj_list:
            if isinstance(instance, (SingleSeismic, DifferenceSeismic)):
                value_list.append(get_seismic_sum(instance))
            elif isinstance(instance, xtgeo.surface.RegularSurface):
                value_list.append(instance.values.sum())
            elif isinstance(instance, SeismicAttribute):
                value_list.append(get_attribute_sum_value(instance))
            else:
                raise ValueError(f"unknown object: {type(instance)}")

        return sum(value_list)

    file_type = file_name.suffix
    if file_type == ".gri":
        return get_gri_sum_value(file_name)
    if file_type == ".segy":
        return get_segy_sum_value(file_name)
    if file_type == ".csv":
        return get_csv_sum_value(file_name)
    return get_pickle_sum_value(file_name)


def test_sim2seis_ert(testdata, monkeypatch, data_dir):
    monkeypatch.chdir(data_dir / "rms/model")
    start_path = data_dir / "rms/model"
    subprocess.run(
        ["ert", "test_run", "../../ert/model/run_sim2seis.ert"],
        env={**os.environ, "SIM2SEIS_MODEL_DIR": str(start_path)},
    )

    # Check values in some of the resulting data files against truth values
    test_files = [
        Path("../../share/results/cubes/syntseis--amplitude_full_depth--20200701.segy"),
        Path(
            "../../share/results/cubes/syntseis--amplitude_full_depth--20180701_20180101.segy"
        ),
        Path("../../share/results/pickle_files/seismic_fwd_diff_time.pkl"),
        Path(
            "../../share/results/cubes/syntseis--relai_full_depth--20180701_20180101.segy"
        ),
        Path("../../share/results/pickle_files/relai_diff_depth.pkl"),
        Path("../../share/results/pickle_files/relai_diff_time.pkl"),
        Path(
            "../../share/results/maps/topvolantis--amplitude_full_rms_depth--20200701_20180101.gri"
        ),
        Path(
            "../../share/results/maps/topvolantis--relai_full_min_depth--20200701_20180101.gri"
        ),
        Path(
            "../../share/results/tables/topvolantis--amplitude_full_mean_depth--20200701_20180101.csv"
        ),
        Path(
            "../../share/results/tables/topvolantis--relai_full_mean_depth--20200701_20180101.csv"
        ),
        Path("../../share/results/pickle_files/amplitude_maps_depth_attributes.pkl"),
        Path("../../share/results/pickle_files/relai_maps_depth_attributes.pkl"),
    ]
    expected_values = [
        2507.2085,
        171.42592,
        617.4236145019531,
        -548.9944,
        -2752.0467529296875,
        111.36359786987305,
        1673.4673521434306,
        -2016.8209276186494,
        14371913848.28719,
        14371913844.76476,
        -5040.2057157847885,
        1469.659427370005,
    ]
    for test_file, truth_value in zip(test_files, expected_values):
        value = get_sum_value(test_file)
        if CALIBRATE:
            print(
                f"Value: {value}, {Path(__file__).name}, "
                f"test comparison: {test_file.name}"
            )
        else:
            assert isclose(value, truth_value, atol=a_tol, rtol=r_tol)
