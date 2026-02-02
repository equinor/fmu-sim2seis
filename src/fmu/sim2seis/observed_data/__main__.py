"""
Handle observed seismic data: depth convert seismic cubes and extract seismic 4D
attributes

Adapted to fmu-sim2seis from RMS based sim2seis by HFLE
Original scripts by TRAL/RNYB/JRIV/EZA
"""

import sys

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    attribute_export,
    check_startup_dir,
    cube_export,
    parse_arguments,
    populate_seismic_attributes,
    read_cubes,
    read_surfaces,
    read_yaml_file,
)

from ._dump_results import _dump_observed_results
from .depth_convert_observed_data import depth_convert_observed_data
from .symlink import make_symlinks_observed_seismic


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(
        arguments=arguments,
        extra_arguments=[
            "verbose",
            "no_attributes",
            "global_dir",
            "global_file",
            "obs_date_prefix",
        ],
    )
    # Validate startup directory
    run_folder = check_startup_dir(args.config_dir)

    with restore_dir(run_folder):
        # Read configuration file, including global configuration
        config = read_yaml_file(
            sim2seis_config_dir=args.config_dir,
            sim2seis_config_file=args.config_file,
            global_config_dir=args.global_dir,
            global_config_file=args.global_file,
            obs_prefix=args.obs_date_prefix,
        )

        # Establish symlinks to the observed seismic data, make exception for
        # tests runs, where a test dataset is copied instead
        if not (config.test_run or args.no_attributes):
            make_symlinks_observed_seismic(
                # vintages=config.global_params.global_config["global"]["seismic"][
        # for key in vintage_info:
        #     if key == "ecldate":
        #         in_dates = vintage_info[key]
        #         monitor_date, base_date = (
        #             str(my_date).replace("-", "") for my_date in in_dates
        #         )  # vintage_dates  # split into two dates
        #         date = monitor_date + "_" + base_date
        #         if verbose:
        #             print("=" * 80, "\nDatapair:", date)
        #     elif key in ("time", "depth"):
        #         cubes = vintage_info[key]
        #         for attr in cubes:
        #             link_name = Path(
        #                 output_datapath,
        #                 "seismic" + sep + attr + "_" + key + sep + date + ".segy",
        #             )

        #     else:
        #         print(f"Key {key} is not a valid key in fmuconfig _seismic")
                #     "real_4d"
                # ],
                vintages=config.global_params.seismic.real_4d,
                # input_datapath=config.global_params.global_config["global"]["seismic"][
                #     "real_4d_cropped_path"
                # ],
                input_datapath=config.global_params.seismic.real_4d_cropped_path,
                output_datapath=config.paths.preprocessed_seismic_dir,
            )

        # Create depth surfaces
        depth_horizons = read_surfaces(
            horizon_dir=config.paths.depth_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.depth_suffix,
        )

        # Read observed data in time
        time_horizons = read_surfaces(
            horizon_dir=config.paths.time_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.time_suffix,
        )
        time_cubes = read_cubes(
            cube_dir=config.paths.preprocessed_seismic_dir,
            cube_prefix=config.depth_conversion.time_cube_prefix,
            domain="time",
            dates=config.global_params.obs_dates,
            diff_dates=config.global_params.obs_diffdates,
        )

        # Run depth conversion
        depth_cubes = depth_convert_observed_data(
            time_cubes=time_cubes,
            depth_conversion=config.depth_conversion,
            depth_surfaces=depth_horizons,
            time_surfaces=time_horizons,
        )

        # Extract attributes
        if args.no_attributes:
            attr_list = []
        else:
            attr_list = populate_seismic_attributes(
                config=read_yaml_file(
                    sim2seis_config_dir=run_folder,
                    sim2seis_config_file=config.attribute_definition_file,
                    parse_inputs=False,
                ),
                cubes=depth_cubes,
                surfaces=depth_horizons,
            )
            attribute_export(
                config_file=config,
                export_attributes=attr_list,
                config_dir=run_folder,
                is_observed=True,
                is_preprocessed=not config.test_run,
            )

        # Dump results - empty attribute list will skip attribute export
        _dump_observed_results(
            config=config,
            time_surfaces=time_horizons,
            depth_surfaces=depth_horizons,
            time_cubes=time_cubes,
            depth_cubes=depth_cubes,
            attributes=attr_list,
        )
        if args.verbose:
            print("Finished processing observed data")

        # Export by dataio
        cube_export(
            config_file=config,
            export_cubes=depth_cubes,
            config_dir=run_folder,
            is_observed=True,
            # If there is per-realisation depth uncertainty, we
            # must set the 'preprocessed' attribute for fmu-dataio
            # This takes precedence over is_observation
            is_preprocessed=not (args.no_attributes or config.test_run),
        )


if __name__ == "__main__":
    main()
