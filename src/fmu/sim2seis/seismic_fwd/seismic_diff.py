"""
Difference objects are made, based on the available cubes for the dates in the global
config file
"""

from fmu.sim2seis.utilities import (
    DifferenceSeismic,
    SeismicName,
    Sim2SeisConfig,
    SingleSeismic,
)


def calculate_seismic_diff(
    dates: Sim2SeisConfig,
    cubes: dict[SeismicName, SingleSeismic],
) -> dict[SeismicName, DifferenceSeismic]:
    diff_cubes = {}

    for date_pair in dates:
        monitor_date, base_date = date_pair

        # Get cubes that match date criterion - can be multiple stack cubes
        base_cubes = get_cubes_by_date(cubes, base_date)
        monitor_cubes = get_cubes_by_date(cubes, monitor_date)
        # Create single seismic and difference seismic objects
        for base_cube, monitor_cube in zip(base_cubes, monitor_cubes):
            monitor_name = monitor_cube.cube_name
            diff_date = str(monitor_date) + "_" + str(base_date)
            diff_name = SeismicName(
                process=monitor_name.process,  # type: ignore
                attribute=monitor_name.attribute,  # type: ignore
                domain=monitor_name.domain,  # type: ignore
                stack=monitor_name.stack,
                date=diff_date,
                ext=monitor_name.ext,
            )
            diff_cubes[diff_name] = DifferenceSeismic(
                base=base_cube,
                monitor=monitor_cube,
            )

    return diff_cubes


def get_cubes_by_date(
    seismic_dict: dict[SeismicName, SingleSeismic], target_date: str
) -> list[SingleSeismic]:
    # Assumes that there is only one cube of each date
    cube_list = [
        value for key, value in seismic_dict.items() if key.date == target_date
    ]
    if not cube_list:
        raise ValueError(f"get_cube_by_date: no matching date in dict: {target_date}")
    return cube_list
