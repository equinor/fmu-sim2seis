from __future__ import annotations

from pathlib import Path

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
    ForwardModelStepValidationError,
)

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import read_yaml_file


class SeismicForward(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="SEISMIC_FORWARD",
            command=[
                "sim2seis_seismic_forward",
                "--config-dir",
                "<CONFIG_DIR>",
                "--config-file",
                "<CONFIG_FILE>",
                "--global-dir",
                "<GLOBAL_DIR>",
                "--global-file",
                "<GLOBAL_FILE>",
                "--model-dir",
                "<MODEL_DIR>",
                "--mod-date-prefix",
                "<MOD_DATE_PREFIX>",
                "--verbose",
                "<VERBOSE>",
            ],
        )

    def validate_pre_realization_run(
        self, fm_step_json: ForwardModelStepJSON
    ) -> ForwardModelStepJSON:
        return fm_step_json

    def validate_pre_experiment(self, fm_step_json: ForwardModelStepJSON) -> None:
        # Parse YAML parameter file by pydantic pre-experiment to catch errors at an
        # early stage

        config_file = Path(fm_step_json["argList"][3])
        model_dir = Path(fm_step_json["argList"][9])
        config_dir = model_dir
        global_dir = model_dir / Path(fm_step_json["argList"][5])
        global_file = Path(fm_step_json["argList"][7])

        try:
            with restore_dir(config_dir):
                _ = read_yaml_file(
                    sim2seis_config_dir=config_dir,
                    sim2seis_config_file=config_file,
                    global_config_dir=global_dir,
                    global_config_file=global_file,
                )
        except Exception as e:
            raise ForwardModelStepValidationError(
                f"sim2seis seismic forward validation failed:\n {e}"
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
                "FORWARD_MODEL SEISMIC_FORWARD("
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml, "
                "<GLOBAL_DIR>=../../fmuconfig/output, "
                "<GLOBAL_FILE>=global_variables.yml, "
                "<MODEL_DIR>=/my_fmu_structure/sim2seis/model, "
                "<MOD_DATE_PREFIX>=HIST, "
                "<VERBOSE>=true/false)"
            ),
        )
