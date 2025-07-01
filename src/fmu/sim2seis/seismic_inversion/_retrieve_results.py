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
        input_path=config.pickle_file_output_path,
        file_name=Path(config.seismic_diff.pickle_file_prefix + "_time.pkl"),
    )
