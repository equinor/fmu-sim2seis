from pathlib import Path

from fmu.sim2seis.utilities import SeismicName, Sim2SeisConfig, retrieve_result_objects


def retrieve_seismic_forward_results(
    config: Sim2SeisConfig, inversion_flag: bool = False
) -> tuple[dict[SeismicName, any]]:
    """
    Retrieve pickled objects from seismic forward modelling
    """
    # Single depth cubes may not be needed
    return retrieve_result_objects(
        input_path=config.paths.pickle_file_output_dir,
        file_name=Path(config.pickle_file_prefix.seismic_diff + "_time.pkl"),
    )
