"""
Handle observed seismic data: depth convert seismic cubes and extract seismic 4D
attributes

Adapted to fmu-sim2seis from RMS based sim2seis by HFLE
Original scripts by TRAL/RNYB/JRIV/EZA
"""

import sys
from pathlib import Path

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    attribute_export,
    check_startup_dir,
    cube_export,
    parse_arguments,
    populate_seismic_attributes,
    read_yaml_file,
)

from ._dump_results import _dump_observed_results
from .depth_convert_observed_data import depth_convert_observed_data
from .depth_surf import get_depth_surfaces
from .import_time_data import read_time_data
from .symlink import make_symlinks_observed_seismic


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments, extra_arguments=["verbose", "no_attributes"])
    # Validate startup directory
    run_folder = check_startup_dir(args.startdir)

    with restore_dir(run_folder):
        # Read configuration file, including global configuration
        config = read_yaml_file(
            args.startdir / args.configdir / args.configfile, args.startdir
        )

        # Establish symlinks to the observed seismic data, make exception for
        # tests runs, where a test dataset is copied instead
        if not config.test_run:
            make_symlinks_observed_seismic(config)

        # Create depth surfaces
        depth_surf = get_depth_surfaces(config)

        # Read observed data in time
        time_cubes, time_surfaces = read_time_data(config)

        # Run depth conversion
        depth_cubes = depth_convert_observed_data(
            time_cubes=time_cubes,
            config=config,
            depth_surfaces=depth_surf,
            time_surfaces=time_surfaces,
        )

        # Extract attributes
        if args.no_attributes:
            attr_list = []
        else:
            attr_list = populate_seismic_attributes(
                config=read_yaml_file(
                    args.startdir / args.configdir / config.attribute_definition_file,
                    args.startdir,
                    update_with_global=False,
                    parse_inputs=False,
                ),
                cubes=depth_cubes,
                surfaces=depth_surf,
            )
            attribute_export(
                config_file=config,
                export_attributes=attr_list,
                start_dir=run_folder,
                is_observed=True,
            )

        # Dump results
        _dump_observed_results(
            config=config,
            time_surfaces=time_surfaces,
            depth_surfaces=depth_surf,
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
            start_dir=run_folder,
            is_observed=True,
        )



if __name__ == "__main__":
    main()
