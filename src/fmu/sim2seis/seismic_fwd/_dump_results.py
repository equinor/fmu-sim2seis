from pathlib import Path

import xtgeo

from fmu.sim2seis.utilities import (
    DifferenceSeismic,
    SeismicName,
    Sim2SeisConfig,
    SingleSeismic,
    dump_result_objects,
)
from fmu.tools import DomainConversion


def _dump_results(
    config: Sim2SeisConfig,
    time_object: dict[SeismicName, SingleSeismic],
    depth_object: dict[SeismicName, SingleSeismic],
    time_diff_object: dict[SeismicName, DifferenceSeismic],
    depth_diff_object: dict[SeismicName, DifferenceSeismic],
    time_horizon_object: dict[str, xtgeo.RegularSurface],
    depth_horizon_object: dict[str, xtgeo.RegularSurface],
    velocity_model_object: DomainConversion,
) -> None:
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_depth.pkl"),
        output_obj=depth_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_time.pkl"),
        output_obj=time_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_diff.pickle_file_prefix + "_depth.pkl"),
        output_obj=depth_diff_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_diff.pickle_file_prefix + "_time.pkl"),
        output_obj=time_diff_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_depth_horizons.pkl"),
        output_obj=depth_horizon_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_time_horizons.pkl"),
        output_obj=time_horizon_object,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_velocity_model.pkl"),
        output_obj=velocity_model_object,
    )
