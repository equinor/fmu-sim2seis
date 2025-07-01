"""
Set up symbolic links to real seismic data stored outside revision
This is to reduce the amount of data copied with fmu_copy_revision.

It is here assumed that the real seismic data are provided as difference cubes. The cube
names/paths are defined in the file fmuconfig/input/_seismic.yml

This job is only run if SIM2SEIS is run in a history run as there are no observed data
for prediction runs.If SIM2SEIS is run in a prediction  workflow, it is skipped. Whether
in history or in prediction is controlled by the environment variable
FLOWSIM_IS_PREDICTION. The variable can be set in ERT (setenv FLOWSIM_IS_PREDICTION)

If FLOWSIM_IS_PREDICTION is undefined (or not equal to PRED) it will assume history run
and create symlinks.

TRAL/RNYB/JRIV/HFLE
"""

from os import getenv
from pathlib import Path

from fmu.sim2seis.utilities import (
    ObservedDataConfig,
    libgeneral as libgen,
)


def _startup(config: ObservedDataConfig):
    cfg = config.global_params.global_config

    vintages = cfg["global"]["seismic"]["real_4d"]

    datapath = cfg["global"]["seismic"]["real_4d_cropped_path"]

    sim2_seis_pred = getenv("FLOWSIM_IS_PREDICTION")
    return cfg, vintages, datapath, sim2_seis_pred


def make_symlinks_observed_seismic(conf: ObservedDataConfig, verbose: bool = False):
    """Make symlinks from share/observations to real seismic."""
    cfg, vintages, datapath, sim2_seis_pred = _startup(conf)
    sep = "--"
    date = ""
    libgen.make_folders([conf.observed_data_path])

    for vintage in vintages:
        vintage_info = vintages[vintage]
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
                    filename = Path(datapath, cubes[attr])
                    link_name = Path(
                        conf.observed_data_path,
                        "seismic" + sep + attr + "_" + key + sep + date + ".segy",
                    )
                    libgen.make_symlink(filename, link_name, verbose=verbose)
            else:
                print(f"Key {key} is not a valid key in fmuconfig _seismic")


# ToDo: is this still necessary?
def main(config: ObservedDataConfig):
    # Create symlinks for history run and pass for prediction run.
    if getenv("FLOWSIM_IS_PREDICTION", False):
        print(f"SIM2SEIS_PRED is {True}, skip this task!")
    else:
        make_symlinks_observed_seismic(config)
        print("Done symbolic linking.")
