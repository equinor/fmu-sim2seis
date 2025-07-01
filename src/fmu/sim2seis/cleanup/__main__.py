"""
The fmu-sim2seis workflow generates a number of pickle-files, which contains
the original class objects, rather than derived outputs. Although they are valuable for
inspection after the sim2seis workflow is run, they require significant disk space, and
as such should be removed when they are no longer needed. A separate ERT workflow is
added for this purpose. This can also be run from command line for interactive sessions.

Command line call:

    sim2seis_cleanup --startdir <...> --configdir <...> --configfile <...>
                     --prefixlist <...>

    --startdir: should be in rms/model level in an fmu directory structure
    --configdir: relative path to the configuration file for sim2seis or observed_data
                (note below)
    --configfile: yaml-file with configuration parameters
    --prefixlist: (optional) list of prefixes for pickle files if only some of the
                  saved pickle
                  files are to be deleted. If it is not included, all pickle files are
                  removed

    This routine can be used both for the synthetic modelling performed by fmu-sim2seis,
    or for the observed data. When the observed data is processed, a number of pickle
    files are also generated. To remove these, give the path and name to the observed
    data config file.
"""

import sys
from pathlib import Path

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
    run_folder = check_startup_dir(args.startdir)

    with restore_dir(run_folder):
        config = read_yaml_file(
            args.startdir / args.configdir / args.configfile, args.startdir
        )
        if hasattr(args, "prefixlist"):
            clear_result_objects(
                output_path=config.pickle_file_output_path, prefix_list=args.prefixlist
            )
        else:
            clear_result_objects(
                output_path=config.pickle_file_output_path,
            )


if __name__ == "__main__":
    main()
