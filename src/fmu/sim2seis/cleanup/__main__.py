"""
The fmu-sim2seis workflow generates a number of pickle-files, which contains
the original class objects, rather than derived outputs. Although they are valuable for
inspection after the sim2seis workflow is run, they require significant disk space, and
as such should be removed when they are no longer needed. A separate ERT workflow is
added for this purpose. This can also be run from command line for interactive sessions.

Command line call:

    sim2seis_cleanup --config-dir <...> --config-file <...>
                     --prefix-list <...>

    --config-dir: should be in sim2seis/model in an fmu directory structure
    --config-file: yaml-file with configuration parameters
    --prefix-list: (optional) list of prefixes for pickle files if only some of the
                  saved pickle
                  files are to be deleted. If it is not included, all pickle files are
                  removed

    This routine can be used both for the synthetic modelling performed by fmu-sim2seis,
    or for the observed data. When the observed data is processed, a number of pickle
    files are also generated. To remove these, give the path and name to the observed
    data config file.
"""

import sys

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    check_startup_dir,
    clear_result_objects,
    parse_arguments,
    read_yaml_file,
)


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments, extra_arguments=["cleanup"])
    # args may contain only an empty string in "prefixlist". If so, remove attribute
    run_folder = check_startup_dir(args.config_dir)

    with restore_dir(run_folder):
        config = read_yaml_file(
            sim2seis_config_dir=args.config_dir,
            sim2seis_config_file=args.config_file,
            global_config_dir=args.global_dir,
            global_config_file=args.global_file,
        )
        if hasattr(args, "prefix_list"):
            clear_result_objects(
                output_path=config.pickle_file_output_path, prefix_list=args.prefix_list
            )
        else:
            clear_result_objects(
                output_path=config.pickle_file_output_path,
            )


if __name__ == "__main__":
    main()
