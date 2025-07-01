from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
)

# from grid3d_maps.aggregate.grid3d_aggregate_map import DESCRIPTION


class MapAttributes(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="MAP_ATTRIBUTES",
            command=[
                "sim2seis_map_attributes",
                "--startdir",
                "<START_DIR>",
                "--configdir",
                "<CONFIG_DIR>",
                "--configfile",
                "<CONFIG_FILE>",
                "--attribute",
                "<ATTRIBUTE>",
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
            source_function_name="MapAttributes",
            description="",
            examples=(
                "code-block:: console\n\n"
                "FORWARD_MODEL MAP_ATTRIBUTES(<START_DIR>=.../rms/model, "
                "<CONFIG_DIR>=../../sim2seis/model, "
                "<CONFIG_FILE>=sim2seis_config.yml, "
                "<ATTRIBUTE>=amplitude/relai)"
            ),
        )
