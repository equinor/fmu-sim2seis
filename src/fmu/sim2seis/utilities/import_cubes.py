from pathlib import Path
from typing import Literal

import xtgeo

from .sim2seis_class_definitions import (
    SeismicName,
    SingleSeismic,
)


def read_cubes(
    cube_dir: Path,
    cube_prefix: str,
    domain: Literal["time", "depth"],
    dates: list[str],
    diff_dates: list[str],
) -> tuple[dict[(str, str), SingleSeismic], dict[str, xtgeo.RegularSurface]]:
    time_cube_dict = {}
    # Extract file names with the correct prefix
    cube_names = [
        tmp_names
        for tmp_names in cube_dir.glob(cube_prefix + "*")
        if str(domain) in tmp_names.stem.lower()
    ]
    # Extract date - single or difference date
    for path_name in cube_names:
        # Use class objects to parse strings
        seis_name = SeismicName.parse_name(path_name.name)
        seis_date = seis_name.date
        # Limit the cube import to those that match the seismic single or difference
        # dates
        if (seis_date in dates) or (seis_date in _diff_string(diff_dates)):
            time_cube_dict[seis_name] = SingleSeismic(
                from_dir=cube_dir,
                cube_name=seis_name,
                date=seis_date,
                cube=xtgeo.cube_from_file(path_name),
            )

    return time_cube_dict


def _diff_string(diff_dates: list[list[str]]) -> list[str]:
    return ["_".join(two_dates) for two_dates in diff_dates]
