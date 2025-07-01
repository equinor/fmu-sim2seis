from __future__ import annotations

import ert

from fmu.sim2seis.forward_models import (
    Cleanup,
    MapAttributes,
    RelativeInversion,
    SeismicForward,
)

PLUGIN_NAME = "sim2seis"


@ert.plugin(name=PLUGIN_NAME)
def installable_workflow_jobs() -> dict[str, str]:
    return {}


@ert.plugin(name=PLUGIN_NAME)
def installable_forward_model_steps() -> list[ert.ForwardModelStepPlugin]:
    return [  # type: ignore
        MapAttributes,
        RelativeInversion,
        SeismicForward,
        Cleanup,
    ]
