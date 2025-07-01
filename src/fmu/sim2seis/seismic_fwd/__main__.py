"""
Run seismic forward for 4D (base and monitor).

The input model parameters must be adapted to the actual field.
Model files are found here: /sim2seis/model/seismic_forward.
In the present setup, the monitor is timeshifted to match the base survey.
Output is single cubes for each date, under sim2seis/output/seismic_forward.

Note: Read env variable to test for hist vs pred mode. If undefined it will assume
history run. The variable can be (and is usually) set in ERT (setenv
FLOWSIM_IS_PREDICTION pred).

EZA/RNYB/JRIV
Adapted to fmu-sim2seis by HFLE
"""

import sys
from pathlib import Path

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    check_startup_dir,
    cube_export,
    get_pred_or_hist_seis_diff_dates,
    parse_arguments,
    read_yaml_file,
)
from fmu.tools import DomainConversion

from ._dump_results import _dump_results
from .seismic_diff import calculate_seismic_diff
from .seismic_forward import exe_seismic_forward, read_time_and_depth_horizons


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments, extra_arguments=["verbose"])
    run_folder = check_startup_dir(args.startdir)

    with restore_dir(run_folder):
        # Get configuration parameters
        config = read_yaml_file(
            args.startdir / args.configdir / args.configfile, args.startdir
        )

        # Read the horizons that are used in depth conversion and later for extraction
        # of attributes
        time_horizons, depth_horizons = read_time_and_depth_horizons(config)

        # Establish velocity model for time/depth conversion
        velocity_model = DomainConversion(
            time_surfaces=list(time_horizons.values()),
            depth_surfaces=list(depth_horizons.values()),
        )

        # Seismic forward modelling
        depth_cubes, time_cubes = exe_seismic_forward(
            config_file=config,
            velocity_model=velocity_model,
            verbose=args.verbose,
        )

        # Get the dates to estimate 4D differences for and do
        # calculations for time and depth cubes
        dates = get_pred_or_hist_seis_diff_dates(config)
        diff_depth = calculate_seismic_diff(dates=dates, cubes=depth_cubes)
        diff_time = calculate_seismic_diff(dates=dates, cubes=time_cubes)

        # Export class objects for QC
        _dump_results(
            config=config,
            time_object=time_cubes,
            depth_object=depth_cubes,
            time_diff_object=diff_time,
            depth_diff_object=diff_depth,
            time_horizon_object=time_horizons,
            depth_horizon_object=depth_horizons,
            velocity_model_object=velocity_model,
        )

        # Export depth cubes
        cube_export(
            config_file=config,
            export_cubes=diff_depth,
            start_dir=args.startdir,
            is_observed=False,
        )

        # Time cubes are used for seismic inversion
        cube_export(
            config_file=config,
            export_cubes=time_cubes,
            start_dir=args.startdir,
            is_observed=False,
        )

        if args.verbose:
            print("Finished seismic forward modelling")


if __name__ == "__main__":
    main()
