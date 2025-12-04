from __future__ import annotations

from pathlib import Path

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
    ForwardModelStepValidationError,
)

from fmu.sim2seis.utilities import read_yaml_file


class SeismicForward(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="SEISMIC_FORWARD",
            command=[
                "sim2seis_seismic_forward",
                "--start-dir",
                "<START_DIR>",
                "--config-dir",
                "<CONFIG_DIR>",
                "--config-file",
                "<CONFIG_FILE>",
                "--model-dir",
                "<MODEL_DIR>",
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
        config_file = Path(fm_step_json["argList"][5])
        model_dir = Path(fm_step_json["argList"][7])
        start_dir = model_dir / "../../rms/model"
        try:
            _ = read_yaml_file(model_dir / config_file, start_dir)
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
                "FORWARD_MODEL MAP_ATTRIBUTES(<START_DIR>=.../rms/model, "
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml,"
                "<VERBOSE>=true/false)"
            ),
        )
