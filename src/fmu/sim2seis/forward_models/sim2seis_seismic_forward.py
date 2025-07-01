from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
    ForwardModelStepValidationError,
)

# from grid3d_maps.aggregate.grid3d_aggregate_map import DESCRIPTION


class SeismicForward(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="SEISMIC_FORWARD",
            command=[
                "sim2seis_seismic_forward",
                "--startdir",
                "<START_DIR>",
                "--configdir",
                "<CONFIG_DIR>",
                "--configfile",
                "<CONFIG_FILE>",
                "--verbose",
                "<VERBOSE>",
            ],
        )

    def validate_pre_realization_run(
        self, fm_step_json: ForwardModelStepJSON
    ) -> ForwardModelStepJSON:
        return fm_step_json

    def validate_pre_experiment(self, fm_step_json: ForwardModelStepJSON) -> None:
        import os
        from pathlib import Path

        from fmu.sim2seis.utilities import read_yaml_file

        model_dir_env = os.environ.get("SIM2SEIS_MODEL_DIR")
        if not model_dir_env:
            raise ValueError(
                'environment variable "SIM2SEIS_MODEL_DIR" must be set to '
                "validate SIM2SEIS model pre-experiment"
            )
        model_dir = Path(model_dir_env)

        runpath_config_dir = Path(fm_step_json["argList"][3])
        config_dir = (
            model_dir
            / "../.."
            / runpath_config_dir.parent.name
            / runpath_config_dir.name
        ).resolve()
        config_file = fm_step_json["argList"][5]
        try:
            os.chdir(model_dir)
            _ = read_yaml_file(config_dir / config_file, model_dir)
        except Exception as e:
            raise ForwardModelStepValidationError(
                f"sim2seis observed data validation failed:\n {e}"
            )

    @staticmethod
    def documentation() -> ForwardModelStepDocumentation | None:
        return ForwardModelStepDocumentation(
            category="modelling.reservoir",
            source_package="fmu.sim2seis",
            source_function_name="SeismicForward",
            description="",
            examples=(
                "code-block:: console\n\n"
                "FORWARD_MODEL MAP_ATTRIBUTES(<START_DIR>=.../rms/model, "
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml,"
                "<VERBOSE>=true/false)"
            ),
        )
