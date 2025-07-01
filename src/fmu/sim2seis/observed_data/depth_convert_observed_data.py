"""Extract necessary time and depth surfaces, and perform depth conversion of
relative ai"""

import xtgeo

from fmu.sim2seis.utilities import (
    DifferenceSeismic,
    ObservedDataConfig,
    SeismicName,
    SingleSeismic,
)
from fmu.tools.domainconversion import DomainConversion


def depth_convert_observed_data(
    time_cubes: dict[SeismicName, DifferenceSeismic | SingleSeismic],
    config: ObservedDataConfig,
    depth_surfaces: dict[str, xtgeo.RegularSurface],
    time_surfaces: dict[str, xtgeo.RegularSurface],
) -> dict[SeismicName, DifferenceSeismic | SingleSeismic]:
    depth_cubes = {}

    seismic_dates = list(time_cubes.keys())

    if isinstance(time_cubes[seismic_dates[0]], (DifferenceSeismic, SingleSeismic)):
        velocity_model = DomainConversion(
            depth_surfaces=list(depth_surfaces.values()),
            time_surfaces=list(time_surfaces.values()),
        )
    else:
        raise ValueError(
            f"{__file__}: unknown type of observed cube, is "
            f"{type(time_cubes[seismic_dates[0]])} "
            f"should be SingleSeismic or DifferenceSeismic object"
        )

    for time_name, observed_seismic_cube in time_cubes.items():
        # set domain to depth from time
        depth_name = SeismicName(
            process=time_name.process,  # type: ignore
            attribute=time_name.attribute,  # type: ignore
            domain="depth",
            stack=time_name.stack,  # type: ignore
            date=time_name.date,
            ext=time_name.ext,
        )
        depth_monitor_name = SeismicName(
            process=time_name.process,  # type: ignore
            attribute=time_name.attribute,  # type: ignore
            domain="depth",
            stack=time_name.stack,  # type: ignore
            date=time_name.monitor_date,
            ext=time_name.ext,
        )
        depth_base_name = SeismicName(
            process=time_name.process,  # type: ignore
            attribute=time_name.attribute,  # type: ignore
            domain="depth",
            stack=time_name.stack,  # type: ignore
            date=time_name.base_date,
            ext=time_name.ext,
        )
        if isinstance(observed_seismic_cube, DifferenceSeismic):
            depth_cubes[depth_name] = observed_seismic_cube
            depth_cubes[depth_name].base.cube = velocity_model.depth_convert_cube(
                incube=observed_seismic_cube.base.cube,
                zinc=config.depth_conversion.z_inc,
                zmin=config.depth_conversion.min_depth,
                zmax=config.depth_conversion.max_depth,
            )
            depth_cubes[depth_name].base.cube_name = depth_base_name
            depth_cubes[depth_name].monitor.cube = velocity_model.depth_convert_cube(
                incube=observed_seismic_cube.monitor.cube,
                zinc=config.depth_conversion.z_inc,
                zmin=config.depth_conversion.min_depth,
                zmax=config.depth_conversion.max_depth,
            )
            depth_cubes[depth_name].monitor.cube_name = depth_monitor_name
        elif isinstance(observed_seismic_cube, SingleSeismic):
            depth_cubes[depth_name] = observed_seismic_cube
            depth_cubes[depth_name].cube_name = depth_name
            depth_cubes[depth_name].cube = velocity_model.depth_convert_cube(
                incube=observed_seismic_cube.cube,
                zinc=config.depth_conversion.z_inc,
                zmin=config.depth_conversion.min_depth,
                zmax=config.depth_conversion.max_depth,
            )
        else:
            raise ValueError(
                f"{__file__}: unknown type of observed cube, is "
                f"{(type(observed_seismic_cube),)} "
                f"should be SingleSeismic or DifferenceSeismic object"
            )

    return depth_cubes
