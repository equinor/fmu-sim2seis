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
            input_path=config.paths.pickle_file_output_dir,
            file_name=Path(config.pickle_file_prefix.relai_diff + "_depth.pkl"),
        )
    else:
        depth_cubes = retrieve_result_objects(
            input_path=config.paths.pickle_file_output_dir,
            file_name=Path(config.pickle_file_prefix.seismic_diff + "_depth.pkl"),
        )

    depth_surfaces = retrieve_result_objects(
        input_path=config.paths.pickle_file_output_dir,
        file_name=Path(
            config.pickle_file_prefix.seismic_forward + "_depth_horizons.pkl"
        ),
    )

    return depth_cubes, depth_surfaces
