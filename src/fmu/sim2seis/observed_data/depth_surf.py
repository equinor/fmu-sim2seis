"""
Get depth surfaces (HUM in prediction mode) to define velocity model from pairs
of depth and time surfaces. This is used to depth convert real seismic to
the depth framework of the current realization.

EZA/JRIV
"""

import xtgeo

from fmu.sim2seis.utilities import ObservedDataConfig


def get_depth_surfaces(conf: ObservedDataConfig) -> dict[str, xtgeo.RegularSurface]:
    """Get top/base for reservoir"""
    surface_dict = {}
    for top in conf.observed_depth_surf.horizon_names:
        tmp_name_input = (
            top.lower() + "--" + conf.observed_depth_surf.suffix_name + ".gri"
        )
        f_in_name = conf.observed_depth_surf.depth_dir.joinpath(tmp_name_input)
        srf = xtgeo.surface_from_file(f_in_name)
        srf.name = top
        surface_dict[top] = srf

    return surface_dict
