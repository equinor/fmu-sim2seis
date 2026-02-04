"""
TRAL/RNYB/JRIV/HFLE
"""

from pathlib import Path

from fmu.pem.pem_utilities.pem_config_validation import SeismicSurvey
from fmu.sim2seis.utilities import (
    make_folders,
    make_symlink,
)


def make_symlinks_observed_seismic(
    vintages: dict[str, SeismicSurvey],
    input_datapath: Path,
    output_datapath: Path,
    verbose: bool = False,
) -> None:
    """Make symlinks from share/observations to real seismic

    Parameters
    ----------
    vintages : dict
        dictionary with seismic information for each vintage
    input_datapath : Path
        input path for seismic data
    output_datapath : Path
        output path for seismic data
    verbose : bool, optional
        level of output, by default False
    """
    sep = "--"
    make_folders([output_datapath])

    for vintage_info in vintages.values():
        date = "_".join(vintage_info.ecldate)
        if vintage_info.time:
            for link, cube in vintage_info.time.items():
                filename = Path(input_datapath, cube)
                link_name = Path(
                    output_datapath,
                    f"seismic{sep}{link}_time{sep}{date}.segy",
                )
                make_symlink(filename, link_name, verbose=verbose)
        if vintage_info.depth:
            for link, cube in vintage_info.depth.items():
                filename = Path(input_datapath, cube)
                link_name = Path(
                    output_datapath,
                    f"seismic{sep}{link}_depth{sep}{date}.segy",
                )
                make_symlink(filename, link_name, verbose=verbose)
