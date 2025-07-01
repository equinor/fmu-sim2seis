from pathlib import Path

import xtgeo

from fmu.sim2seis.utilities import (
    SeismicAttribute,
    Sim2SeisConfig,
    SingleSeismic,
    dump_result_objects,
)


def _dump_observed_results(
    config: Sim2SeisConfig,
    time_surfaces: dict[str, xtgeo.RegularSurface],
    depth_surfaces: dict[str, xtgeo.RegularSurface],
    time_cubes: dict[any, SingleSeismic],
    depth_cubes: dict[any, SingleSeismic],
    attributes: list[SeismicAttribute],
) -> None:
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.pickle_file_prefix + "_depth_surfaces.pkl"),
        output_obj=depth_surfaces,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.pickle_file_prefix + "_time_surfaces.pkl"),
        output_obj=time_surfaces,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.pickle_file_prefix + "_depth_cubes.pkl"),
        output_obj=depth_cubes,
    )
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.pickle_file_prefix + "_time_cubes.pkl"),
        output_obj=time_cubes,
    )
    if attributes:
        dump_result_objects(
            output_path=config.pickle_file_output_path,
            file_name=Path(config.pickle_file_prefix + "_depth_attributes.pkl"),
            output_obj=attributes,
        )
