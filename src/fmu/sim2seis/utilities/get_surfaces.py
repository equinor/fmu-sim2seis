"""
Get depth surfaces (HUM in prediction mode) to define velocity model from pairs
of depth and time surfaces. This is used to depth convert real seismic to
the depth framework of the current realization.

EZA/JRIV/HFLE
"""

from pathlib import Path

import xtgeo


def read_surfaces(
    horizon_dir: Path,
    horizon_names: list[str],
    horizon_suffix: str,
) -> dict[str, xtgeo.RegularSurface]:
    """Get top/base for reservoir"""
    surface_dict = {}
    for top in horizon_names:
        tmp_name_input = top.lower() + horizon_suffix
        f_in_name = horizon_dir / tmp_name_input
        srf = xtgeo.surface_from_file(f_in_name)
        srf.name = top
        surface_dict[top] = srf

    return surface_dict
