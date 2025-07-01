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
                "--startdir",
                "<START_DIR>",
                "--configdir",
                "<CONFIG_DIR>",
                "--configfile",
                "<CONFIG_FILE>",
                "--prefixlist",
                "<PREFIX_LIST>",
            ],
            default_mapping={"<PREFIX_LIST>": ""},
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
                "FORWARD_MODEL CLEANUP(<START_DIR>=.../rms/model, "
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml,"
                "<PREFIX_LIST>=relai_)"
            ),
        )
