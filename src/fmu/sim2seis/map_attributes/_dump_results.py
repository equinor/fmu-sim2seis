from pathlib import Path
from typing import Literal

import xtgeo

from fmu.sim2seis.utilities import (
    SeismicAttribute,
    Sim2SeisConfig,
    dump_result_objects,
)


def _dump_map_results(
    config: Sim2SeisConfig,
    depth_surfaces: dict[str, xtgeo.RegularSurface],
    attributes: list[SeismicAttribute],
    attribute_type: Literal["amplitude", "relai"],
) -> None:
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(config.amplitude_map.pickle_file_prefix + "_depth_surfaces.pkl"),
        output_obj=depth_surfaces,
    )
    if attribute_type == "amplitude":
        attr_prefix = config.amplitude_map.pickle_file_prefix
    else:
        attr_prefix = config.inversion_map.pickle_file_prefix
    dump_result_objects(
        output_path=config.pickle_file_output_path,
        file_name=Path(attr_prefix + "_depth_attributes.pkl"),
        output_obj=attributes,
    )

    return
