# pylint: disable=missing-module-docstring
import sys
from pathlib import Path

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    attribute_export,
    check_startup_dir,
    parse_arguments,
    populate_seismic_attributes,
    read_yaml_file,
)

from ._dump_results import _dump_map_results
from ._retrieve_results import (
    retrieve_inversion_results,
    retrieve_seismic_forward_results,
)


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments, extra_arguments=["attribute", "verbose"])
    run_folder = check_startup_dir(args.startdir)

    with restore_dir(run_folder):
        # Read configuration file
        config = read_yaml_file(
            args.startdir / args.configdir / args.configfile, args.startdir
        )

        # Determine if the attributes are from seismic amplitude or inverted
        # seismic data to read the correct set of input cubes
        if args.attribute == config.amplitude_map.attribute:  # 'amplitude'
            depth_cubes, depth_surfaces = retrieve_seismic_forward_results(
                config=config
            )
        elif args.attribute == config.inversion_map.attribute:  # 'relai'
            depth_cubes, depth_surfaces = retrieve_inversion_results(config=config)
        else:
            raise ValueError(
                f"{__file__}: unknown attribute for map generation: {args.attribute}"
            )

        # Generate attributes
        attr_list = populate_seismic_attributes(
            config=read_yaml_file(
                args.startdir / args.configdir / config.attribute_definition_file,
                args.startdir,
                update_with_global=False,
                parse_inputs=False,
            ),
            cubes=depth_cubes,
            surfaces=depth_surfaces,
        )

        # Dump results
        _dump_map_results(
            config=config,
            depth_surfaces=depth_surfaces,
            attributes=attr_list,
            attribute_type=args.attribute,
        )

        # Export with dataio
        attribute_export(
            config_file=config,
            export_attributes=attr_list,
            start_dir=args.startdir,
            is_observed=False,
        )

    if args.verbose:
        print("Finished generating maps")


if __name__ == "__main__":
    main()
