from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
)


class ObservedData(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="OBSERVED_DATA",
            command=[
                "sim2seis_observed_data",
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
                "--verbose",
                "<VERBOSE>",
            ],
        )

    def validate_pre_realization_run(
        self, fm_step_json: ForwardModelStepJSON
    ) -> ForwardModelStepJSON:
        return fm_step_json

    def validate_pre_experiment(self, fm_step_json: ForwardModelStepJSON) -> None:
        pass

    @staticmethod
    def documentation() -> ForwardModelStepDocumentation | None:
        return ForwardModelStepDocumentation(
            category="modelling.reservoir",
            source_package="fmu.sim2seis",
            source_function_name="ObservedData",
            description="",
            examples=(
                "code-block:: console\n\n"
                "FORWARD_MODEL OBSERVED_DATA("
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml, "
                "<GLOBAL_DIR>=../../fmuconfig/output, "
                "<GLOBAL_FILE>=global_variables.yml, "
                "<MODEL_DIR>=/my_fmu_structure/sim2seis/model, "
                "<VERBOSE>=true/false)"
            ),
        )
