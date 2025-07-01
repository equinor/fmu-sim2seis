from pathlib import Path

import xtgeo

from fmu.sim2seis.utilities import SeismicName, Sim2SeisConfig, retrieve_result_objects


def retrieve_inversion_results(
    config: Sim2SeisConfig,
) -> tuple[dict[SeismicName, any], dict[str, xtgeo.RegularSurface]]:
    return retrieve_seismic_forward_results(config=config, inversion_flag=True)


def retrieve_seismic_forward_results(
    config: Sim2SeisConfig, inversion_flag: bool = False
) -> tuple[dict[SeismicName, any], dict[str, xtgeo.RegularSurface]]:
    """
    Retrieve pickled objects from seismic forward modelling
    """
    # Single depth cubes may not be needed
    if inversion_flag:
        # read depth cubes from inversion instead
        depth_cubes = retrieve_result_objects(
            input_path=config.pickle_file_output_path,
            file_name=Path(config.seismic_inversion.pickle_file_prefix + "_depth.pkl"),
        )
    else:
        depth_cubes = retrieve_result_objects(
            input_path=config.pickle_file_output_path,
            file_name=Path(config.seismic_diff.pickle_file_prefix + "_depth.pkl"),
        )

    depth_surfaces = retrieve_result_objects(
        input_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_fwd.pickle_file_prefix + "_depth_horizons.pkl"),
    )

    return depth_cubes, depth_surfaces
