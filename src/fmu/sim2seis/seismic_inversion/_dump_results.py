from pathlib import Path

from fmu.sim2seis.utilities import (
    DifferenceSeismic,
    Sim2SeisConfig,
    dump_result_objects,
)


def _dump_results(
    config: Sim2SeisConfig,
    time_object: dict[str, DifferenceSeismic],
    depth_object: dict[str, DifferenceSeismic],
) -> None:
    dump_result_objects(
        output_path=config.paths.pickle_file_output_dir,
        file_name=Path(config.pickle_file_prefix.relai_diff + "_depth.pkl"),
        output_obj=depth_object,
    )
    dump_result_objects(
        output_path=config.paths.pickle_file_output_dir,
        file_name=Path(config.pickle_file_prefix.relai_diff + "_time.pkl"),
        output_obj=time_object,
    )
