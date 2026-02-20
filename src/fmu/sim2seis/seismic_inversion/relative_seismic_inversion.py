"""
Run 4D relative seismic inversion (base and monitor).
The inversion parameters specified in the script need field specific tuning.

The output is 4Drelai (in time) for each diffdate.

JRIV/EZA/RNYB/HFLE
"""

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
    config_dir: Path,
    time_cubes: dict[SeismicName, DifferenceSeismic],
    config: Sim2SeisConfig,
) -> dict[SeismicName, DifferenceSeismic]:
    fmu_rootpath = config.paths.fmu_rootpath

    diff_rel_ai_dict = {}
    with restore_dir(fmu_rootpath):
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
                    from_dir=config.paths.modelled_seismic_dir.name,
                    cube_name=tmp_inv_monitor_name,
                    date=SeismicDate(tmp_inv_monitor_name.date),
                    cube=relai_time_cubes[-1],
                ),
                base=SingleSeismic(
                    from_dir=config.paths.modelled_seismic_dir.name,
                    cube_name=tmp_inv_base_name,
                    date=SeismicDate(tmp_inv_base_name.date),
                    cube=relai_time_cubes[0],
                ),
            )
    return diff_rel_ai_dict
