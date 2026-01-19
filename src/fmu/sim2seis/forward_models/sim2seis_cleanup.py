from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
)

# from grid3d_maps.aggregate.grid3d_aggregate_map import DESCRIPTION


class Cleanup(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="CLEANUP",
            command=[
                "sim2seis_cleanup",
                "--config-dir",
                "<CONFIG_DIR>",
                "--config-file",
                "<CONFIG_FILE>",
                "--global-dir",
                "<GLOBAL_DIR>",
                "--global-file",
                "<GLOBAL_FILE>",
                "--verbose",
                "<VERBOSE>",
                "--prefix-list",
                "<PREFIX_LIST>",
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
            source_function_name="Cleanup",
            description="",
            examples=(
                "code-block:: console\n\n"
                "FORWARD_MODEL CLEANUP("
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml, "
                "<GLOBAL_DIR>=../../fmuconfig/output, "
                "<GLOBAL_FILE>=global_variables.yml, "
                "<VERBOSE>=true/false)"
            ),
        )
