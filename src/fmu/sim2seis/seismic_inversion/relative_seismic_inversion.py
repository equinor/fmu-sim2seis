"""
Run 4D relative seismic inversion (base and monitor).
The inversion parameters specified in the script need field specific tuning.

The output is 4Drelai (in time) for each diffdate.

Note: Read env variable FLOWSIM_IS_PREDICTION to test for hist vs pred mode
If undefined it will assume history run and use HIST_DATES.
The variable can be set in ERT (setenv FLOWSIM_IS_PREDICTION True).

JRIV/EZA/RNYB/HFLE
"""

import os
from pathlib import Path

from si4ti import compute_impedance

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    DifferenceSeismic,
    SeismicDate,
    SeismicName,
    Sim2SeisConfig,
    SingleSeismic,
)


def run_relative_inversion_si4ti(
        start_dir: Path,
        time_cubes: dict[SeismicName, DifferenceSeismic],
        config: Sim2SeisConfig,
) -> dict[SeismicName, DifferenceSeismic]:
    # To get the paths right, both when run from ERT and command line -
    try:
        # _ERT_RUNPATH will point to the top of the fmu directory structure, as
        # is expected by fmu-dataio, so no need to move up
        run_path = Path(os.getenv("_ERT_RUNPATH"))
        rel_dir= Path(".")
    except TypeError:
        # in case this is run from command line, _ERT_RUNPATH is not set, and start_dir
        # is at ./rms/model, relative to the top of the fmu directory structure. To get
        # the requirements of fmu-dataio right, we need to move up two levels
        run_path = Path(start_dir)
        rel_dir = Path("../..")

    diff_rel_ai_dict = {}
    with restore_dir(run_path.joinpath(rel_dir)):
        for seis_diff_name, seis_diff_obj in time_cubes.items():
            tmp_inv_diff_name = SeismicName(
                process=seis_diff_name.process,
                attribute="relai",
                domain=seis_diff_name.domain,
                stack=seis_diff_name.stack,  # type: ignore
                date=seis_diff_name.date,
                ext=seis_diff_name.ext,
            )
            tmp_inv_base_name = SeismicName(
                process=seis_diff_obj.base.cube_name.process,
                attribute="relai",
                domain=seis_diff_obj.base.cube_name.domain,
                stack=seis_diff_obj.base.cube_name.stack,  # type: ignore
                date=seis_diff_obj.base.cube_name.date,
                ext=seis_diff_obj.base.cube_name.ext,
            )
            tmp_inv_monitor_name = SeismicName(
                process=seis_diff_obj.monitor.cube_name.process,
                attribute="relai",
                domain=seis_diff_obj.monitor.cube_name.domain,
                stack=seis_diff_obj.monitor.cube_name.stack,  # type: ignore
                date=seis_diff_obj.monitor.cube_name.date,
                ext=seis_diff_obj.monitor.cube_name.ext,
            )
            relai_time_cubes, _ = compute_impedance(
                input_cubes=[seis_diff_obj.base.cube, seis_diff_obj.monitor.cube],
                segments=config.seismic_inversion.inversion_parameters.segments,
                max_iter=config.seismic_inversion.inversion_parameters.max_iter,
                damping_3D=config.seismic_inversion.inversion_parameters.damping_3d,
                damping_4D=config.seismic_inversion.inversion_parameters.damping_4d,
                latsmooth_3D=config.seismic_inversion.inversion_parameters.lateral_smoothing_3d,
                latsmooth_4D=config.seismic_inversion.inversion_parameters.lateral_smoothing_4d,
            )
            diff_rel_ai_dict[tmp_inv_diff_name] = DifferenceSeismic(
                monitor=SingleSeismic(
                    from_dir=config.seismic_inversion.path.name,
                    cube_name=tmp_inv_monitor_name,
                    date=SeismicDate(tmp_inv_monitor_name.date),
                    cube=relai_time_cubes[-1],
                ),
                base=SingleSeismic(
                    from_dir=config.seismic_inversion.path.name,
                    cube_name=tmp_inv_base_name,
                    date=SeismicDate(tmp_inv_base_name.date),
                    cube=relai_time_cubes[0],
                ),
            )
    return diff_rel_ai_dict
