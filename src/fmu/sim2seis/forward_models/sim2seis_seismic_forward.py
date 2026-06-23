from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
)


class SeismicForward(ForwardModelStepPlugin):
    def __init__(self) -> None:
        super().__init__(
            name="SEISMIC_FORWARD",
            command=[
                "sim2seis_seismic_forward",
                "--config-file",
                "<CONFIG_FILE>",
                "--global-file",
                "<GLOBAL_FILE>",
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

    def validate_pre_experiment(self, _fm_step_json: ForwardModelStepJSON) -> None:
        # No-op: sim2seis_seismic_forward depends on files created later in the ERT
        # workflow so pre-experiment validation cannot meaningfully verify them.
        pass

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
                "<CONFIG_FILE>=<RUNPATH>/sim2seis/model/sim2seis_combined_config.yml, "
                "<GLOBAL_FILE>=<RUNPATH>/fmuconfig/output/global_variables.yml, "
                "<MOD_DATE_PREFIX>=HIST, "
                "<VERBOSE>=true/false)"
            ),
        )
