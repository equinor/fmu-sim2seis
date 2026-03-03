from __future__ import annotations

from ert import (
    ForwardModelStepDocumentation,
    ForwardModelStepJSON,
    ForwardModelStepPlugin,
    ForwardModelStepValidationError,
)

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import parse_arguments, read_yaml_file


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
        # Parse YAML parameter file by pydantic pre-experiment to catch configuration
        # errors at an early stage.
        #
        # At this point ERT has not yet created the per-realization directory
        # structure, so realization-specific file/directory existence checks must
        # be skipped. pre_experiment=True is passed to read_yaml_file so that
        # realization-specific filesystem validators are suppressed, while
        # config-resident file checks and non-path validators (types, ranges,
        # etc.) still run normally.

        args = parse_arguments(
            arguments=fm_step_json["argList"],
            extra_arguments=[
                "verbose",
                "global_dir",
                "global_file",
                "mod_date_prefix",
            ],
        )
        # Hard-code relative path to global config file
        global_dir = args.config_dir / args.global_dir

        try:
            with restore_dir(args.config_dir):
                _ = read_yaml_file(
                    sim2seis_config_dir=args.config_dir,
                    sim2seis_config_file=args.config_file,
                    global_config_dir=global_dir,
                    global_config_file=args.global_file,
                    pre_experiment=True,
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
                "<MOD_DATE_PREFIX>=HIST, "
                "<VERBOSE>=true/false)"
            ),
        )
