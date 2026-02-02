"""
Run seismic forward for 4D (base and monitor).

The input model parameters must be adapted to the actual field.
Model files are found here: /sim2seis/model/seismic_forward.
In the present setup, the monitor is timeshifted to match the base survey.
Output is single cubes for each date, under sim2seis/output/seismic_forward.

EZA/RNYB/JRIV
Adapted to fmu-sim2seis by HFLE
"""

import sys

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    check_startup_dir,
    cube_export,
    parse_arguments,
    read_surfaces,
    read_yaml_file,
)
from fmu.tools import DomainConversion

from ._dump_results import _dump_results
from .seismic_diff import calculate_seismic_diff
from .seismic_forward import exe_seismic_forward


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(
        arguments=arguments,
        extra_arguments=[
            "verbose",
            "model_dir",
            "global_dir",
            "global_file",
            "mod_date_prefix",
        ],
    )
    run_folder = check_startup_dir(args.config_dir)

    with restore_dir(run_folder):
        # Get configuration parameters
        config = read_yaml_file(
            sim2seis_config_dir=args.config_dir,
            sim2seis_config_file=args.config_file,
            global_config_dir=args.global_dir,
            global_config_file=args.global_file,
            mod_prefix=args.mod_date_prefix,
        )

        # Read the horizons that are used in depth conversion and later for extraction
        # of attributes
        time_horizons = read_surfaces(
            horizon_dir=config.paths.time_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.time_suffix,
        )
        depth_horizons = read_surfaces(
            horizon_dir=config.paths.depth_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.depth_suffix,
        )

        # Establish velocity model for time/depth conversion
        velocity_model = DomainConversion(
            time_surfaces=list(time_horizons.values()),
            depth_surfaces=list(depth_horizons.values()),
        )

        # Seismic forward modelling
        depth_cubes, time_cubes = exe_seismic_forward(
            config_file=config,
            config_dir=run_folder,
            velocity_model=velocity_model,
            verbose=args.verbose,
        )

        # Get the dates to estimate 4D differences for and do
        # calculations for time and depth cubes
        diff_depth = calculate_seismic_diff(
            dates=config.global_params.mod_diffdates,
            cubes=depth_cubes,
        )
        diff_time = calculate_seismic_diff(
            dates=config.global_params.mod_diffdates,
            cubes=time_cubes,
        )

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
            config_dir=run_folder,
            is_observed=False,
        )

        # Time cubes are used for seismic inversion
        cube_export(
            config_file=config,
            export_cubes=time_cubes,
            config_dir=run_folder,
            is_observed=False,
        )

        if args.verbose:
            print("Finished seismic forward modelling")


if __name__ == "__main__":
    main()
