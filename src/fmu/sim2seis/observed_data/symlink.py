"""
TRAL/RNYB/JRIV/HFLE
"""

from os import getenv
from pathlib import Path

from fmu.sim2seis.utilities import (
    ObservedDataConfig,
    make_folders,
    make_symlink,
)


def make_symlinks_observed_seismic(
        conf: ObservedDataConfig,
        vintages: dict,
        input_datapath: Path,
        output_datapath: Path,
        verbose: bool = False) -> None:
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
    # _cfg, vintages, datapath, _sim2_seis_pred = _startup(conf)
    sep = "--"
    date = ""
    make_folders([output_datapath])

    for vintage_info in vintages.values():
        for key in vintage_info:
            if key == "ecldate":
                in_dates = vintage_info[key]
                monitor_date, base_date = (
                    str(my_date).replace("-", "") for my_date in in_dates
                )  # vintage_dates  # split into two dates
                date = monitor_date + "_" + base_date
                if verbose:
                    print("=" * 80, "\nDatapair:", date)
            elif key in ("time", "depth"):
                cubes = vintage_info[key]
                for attr in cubes:
                    filename = Path(input_datapath, cubes[attr])
                    link_name = Path(
                        output_datapath,
                        "seismic" + sep + attr + "_" + key + sep + date + ".segy",
                    )
                    make_symlink(filename, link_name, verbose=verbose)
            else:
                print(f"Key {key} is not a valid key in fmuconfig _seismic")
