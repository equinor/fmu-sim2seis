"""Extract necessary time and depth surfaces, and perform depth conversion of
relative ai"""

import copy

import xtgeo

from fmu.sim2seis.utilities import DifferenceSeismic, SeismicName, Sim2SeisConfig
from fmu.tools.domainconversion import DomainConversion


def depth_convert_ai(
    difference_cubes: dict[SeismicName, DifferenceSeismic],
    velocity_model: DomainConversion,
    config: Sim2SeisConfig,
) -> dict[(str, str), DifferenceSeismic]:
    """
    Perform depth conversion using the velocity model established in seismic forward
    """

    depth_cubes = {}

    for time_name, diff_obj in difference_cubes.items():
        depth_name = SeismicName(
            process=time_name.process,
            attribute=time_name.attribute,
            domain="depth",
            stack=time_name.stack,
            date=time_name.date,
            ext=time_name.ext,
        )
        time_monitor_name = diff_obj.monitor.cube_name
        depth_monitor_name = SeismicName(
            process=time_monitor_name.process,
            attribute=time_monitor_name.attribute,
            domain="depth",
            stack=time_monitor_name.stack,
            date=time_monitor_name.date,
            ext=time_monitor_name.ext,
        )
        time_base_name = diff_obj.base.cube_name
        depth_base_name = SeismicName(
            process=time_base_name.process,
            attribute=time_base_name.attribute,
            domain="depth",
            stack=time_base_name.stack,
            date=time_base_name.date,
            ext=time_base_name.ext,
        )
        depth_cubes[depth_name] = copy.deepcopy(diff_obj)
        depth_cubes[depth_name].cube_name = depth_name

        depth_cubes[depth_name].base.cube = velocity_model.depth_convert_cube(
            incube=diff_obj.base.cube,
            zinc=config.depth_conversion.z_inc,
            zmax=config.depth_conversion.max_depth,
            zmin=config.depth_conversion.min_depth,
        )
        depth_cubes[depth_name].base.cube_name = depth_base_name
        depth_cubes[depth_name].monitor.cube = velocity_model.depth_convert_cube(
            incube=diff_obj.monitor.cube,
            zinc=config.depth_conversion.z_inc,
            zmax=config.depth_conversion.max_depth,
            zmin=config.depth_conversion.min_depth,
        )
        depth_cubes[depth_name].monitor.cube_name = depth_monitor_name

    return depth_cubes
