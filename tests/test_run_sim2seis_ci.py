import pickle
from pathlib import Path

import pandas as pd
import xtgeo.surface
import yaml
from fmu.pem.pem_utilities import restore_dir
from numpy import isclose

from fmu.sim2seis.map_attributes import main as map_attributes
from fmu.sim2seis.observed_data import main as run_obs_data
from fmu.sim2seis.seismic_fwd import main as run_seismic_forward
from fmu.sim2seis.seismic_inversion import main as run_seismic_inversion
from fmu.sim2seis.utilities import DifferenceSeismic, SeismicAttribute, SingleSeismic

obs_data_config_file_name = Path("obs_data_config.yml")
sim2seis_config_file_name = Path("sim2seis_config.yml")

# If there is a need to re-calibrate the test, set CALIBRATE to True
CALIBRATE = False
a_tol = 0.05
r_tol = 0.001


def test_obs_data(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    # Modify the config file: add `test_run = True`
    with open(obs_data_config_file_name) as fin:
        conf_dict = yaml.safe_load(fin)
        conf_dict["test_run"] = True
    fout_name = Path(
        obs_data_config_file_name.stem + "_test" + obs_data_config_file_name.suffix
    )
    with open(fout_name, "w") as fout:
        yaml.safe_dump(conf_dict, fout)
    run_obs_data(
        [
            "--config-dir",
            str(config_dir),
            "--config-file",
            str(fout_name),
        ]
    )

    # Check values in some of the resulting data files against truth values
    test_files = [
        Path(
            "../../share/preprocessed/maps/topvolantis--amplitude_rms_depth--20200701_20180101.gri"
        ),
        Path(
            "../../share/preprocessed/maps/topvolantis--relai_min_depth--20200701_20180101.gri"
        ),
        Path(
            "../../share/preprocessed/tables/topvolantis--amplitude_mean_depth--20200701_20180101.csv"
        ),
        Path(
            "../../share/preprocessed/tables/topvolantis--relai_rms_depth--20200701_20180101.csv"
        ),
        Path("../../share/preprocessed/pickle_files/observed_data_time_cubes.pkl"),
    ]
    expected_values = [
        737.739982963365,
        -1128.321365091755,
        14371913838.663399,
        14371913847.189327,
        46.49933598935604,
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


def test_sim2seis(monkeypatch, data_dir):
    run_test_sim2seis_seismic_forward(monkeypatch, data_dir)
    run_test_sim2seis_seismic_inversion(monkeypatch, data_dir)
    run_test_sim2seis_map(monkeypatch, data_dir)


def run_test_sim2seis_seismic_forward(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    run_seismic_forward(
        [
            "--config-dir",
            str(config_dir),
            "--config-file",
            str(sim2seis_config_file_name),
            "--verbose",
            False,
        ]
    )

    # Check values in some of the resulting data files against truth values
    test_files = [
        Path("../../share/results/cubes/seismic--amplitude_full_depth--20200701.segy"),
        Path(
            "../../share/results/cubes/seismic--amplitude_full_depth--20180701_20180101.segy"
        ),
        Path("../../share/results/pickle_files/seismic_fwd_diff_time.pkl"),
    ]
    expected_values = [
        2507.2085,
        171.42592,
        617.4236145019531,
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


def run_test_sim2seis_seismic_inversion(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    run_seismic_inversion(
        [
            "--config-dir",
            str(config_dir),
            "--config-file",
            str(sim2seis_config_file_name),
            "--verbose",
            False,
        ]
    )

    # Check values in some of the resulting data files against truth values
    test_files = [
        Path(
            "../../share/results/cubes/seismic--relai_full_depth--20180701_20180101.segy"
        ),
        Path("../../share/results/pickle_files/relai_diff_depth.pkl"),
        Path("../../share/results/pickle_files/relai_diff_time.pkl"),
    ]
    expected_values = [
        -548.9944,
        -2752.0467529296875,
        111.36359786987305,
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


def run_test_sim2seis_map(monkeypatch, data_dir):
    config_dir = data_dir / "sim2seis" / "model"
    monkeypatch.chdir(config_dir)
    for attribute in ["amplitude", "relai"]:
        with restore_dir(config_dir):
            map_attributes(
                [
                    "--config-dir",
                    str(config_dir),
                    "--config-file",
                    str(sim2seis_config_file_name),
                    "--attribute",
                    attribute,
                ]
            )

    # Check values in some of the resulting data files against truth values
    test_files = [
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
        1673.4673521434306,
        -2016.8209276186494,
        14371913848.28719,
        14371913843.33451,
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
