"""
Handle observed seismic data: depth convert seismic cubes and extract seismic 4D
attributes

Adapted to fmu-sim2seis from RMS based sim2seis by HFLE
Original scripts by TRAL/RNYB/JRIV/EZA
"""

import os
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
    # Establish if this in run from ERT. If so, we only want to depth convert observed
    # seismic cubes. `preprocessed` is only when this is NOT run from ERT
    is_preprocessed = not bool(os.environ.get("_ERT_RUNPATH", None))

    # Validate startup directory
    config_dir = check_startup_dir(args.config_dir)
    # Read configuration file, including global configuration
    config = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=args.config_file,
        global_config_dir=args.global_dir,
        global_config_file=args.global_file,
        obs_prefix=args.obs_date_prefix,
    )

    with restore_dir(config.paths.fmu_rootpath):
        # Establish symlinks to the observed seismic data, make exception for
        # tests runs, where a test dataset is copied instead
        if not config.test_run:
            make_symlinks_observed_seismic(
                vintages=config.global_params.seismic.real_4d,
                input_datapath=config.global_params.seismic.real_4d_cropped_path,
                output_datapath=config.paths.preprocessed_seismic_dir,
            )

        # Read depth surfaces
        depth_horizons = read_surfaces(
            horizon_dir=config.paths.depth_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.depth_suffix,
        )

        # Read observed time horizons
        time_horizons = read_surfaces(
            horizon_dir=config.paths.time_horizon_dir,
            horizon_names=config.depth_conversion.horizon_names,
            horizon_suffix=config.depth_conversion.time_suffix,
        )

        # Read observed seismic cubes
        time_cubes = read_cubes(
            cube_dir=config.paths.preprocessed_seismic_dir,
            cube_prefix=config.depth_conversion.cube_prefix,
            domain="time",
            dates=config.global_params.obs_dates,
            diff_dates=config.global_params.obs_diffdates,
        )
        if not time_cubes:
            raise ValueError(
                f"no time cubes imported from {config.paths.preprocessed_seismic_dir} "
                f"with prefix {config.depth_conversion.cube_prefix}, please check "
                "settings"
            )

        # Depth conversion is run in both cases
        depth_cubes = depth_convert_observed_data(
            time_cubes=time_cubes,
            depth_conversion=config.depth_conversion,
            depth_surfaces=depth_horizons,
            time_surfaces=time_horizons,
        )
        if not depth_cubes:
            raise ValueError(
                f"no depth cubes imported from {config.paths.preprocessed_seismic_dir} "
                f"with prefix {config.depth_conversion.cube_prefix}, please check "
                "settings"
            )

        # Extract attributes only in the case that the no_attributes flag is
        # not set, and when the workflow is not run from ERT
        if not args.no_attributes and is_preprocessed:
            attr_list = populate_seismic_attributes(
                config=read_yaml_file(
                    sim2seis_config_dir=config_dir,
                    sim2seis_config_file=config.attribute_map_definition_file,
                    parse_inputs=False,
                ),
                cubes=depth_cubes,
                surfaces=depth_horizons,
            )
            attribute_export(
                config_file=config,
                export_attributes=attr_list,
                is_observed=True,
                is_preprocessed=True,
            )
        else:
            attr_list = []

        # Export by dataio
        # If there is per-realisation depth uncertainty, `fmu-dataio` defines
        # the data as `observations`. If not, they are `preprocessed`
        cube_export(
            config_file=config,
            export_cubes=depth_cubes,
            is_observed=True,
            is_preprocessed=is_preprocessed,
        )

        if args.verbose:
            print("Finished processing observed data")


if __name__ == "__main__":
    main()
