"""
Run 4D relative seismic inversion (base and monitor).
The inversion parameters specified in the config file need field specific tuning.

The output is 4Drelai (in time) for each diffdate.

Note: Read env variable FLOWSIM_IS_PREDICTION to test for hist vs pred mode
If undefined it will assume history run and use HIST_DATES.
The variable can be set in ERT (setenv FLOWSIM_IS_PREDICTION True).

JRIV/EZA/RNYB
Adapted to fmu-sim2seis by HFLE
"""

import sys
from pathlib import Path

from fmu.pem.pem_utilities import restore_dir
from fmu.sim2seis.utilities import (
    check_startup_dir,
    cube_export,
    parse_arguments,
    read_yaml_file,
    retrieve_result_objects,
)

from ._dump_results import _dump_results
from ._retrieve_results import retrieve_seismic_forward_results
from .depth_convert_rel_ai import depth_convert_ai
from .relative_seismic_inversion import run_relative_inversion_si4ti


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(arguments, extra_arguments=["verbose"])

    run_folder = check_startup_dir(args.startdir)

    with restore_dir(run_folder):
        conf = read_yaml_file(
            args.startdir / args.configdir / args.configfile, args.startdir
        )

        # Retrieve the seismic time cubes from seismic forward modelling
        seismic_time_cubes = retrieve_seismic_forward_results(config=conf)

        # Use python interface to relative seismic inversion
        rel_ai_time_dict = run_relative_inversion_si4ti(
            time_cubes=seismic_time_cubes,
            config=conf,
            start_dir=args.startdir,
        )

        # Depth conversion, as the inversion is run in time domain
        velocity_model = retrieve_result_objects(
            input_path=conf.pickle_file_output_path,
            file_name=conf.seismic_fwd.pickle_file_prefix + "_velocity_model.pkl",
        )
        rel_ai_depth_dict = depth_convert_ai(
            velocity_model=velocity_model,
            config=conf,
            difference_cubes=rel_ai_time_dict,
        )

        # Dump all resulting objects to pickle files
        _dump_results(
            config=conf,
            time_object=rel_ai_time_dict,
            depth_object=rel_ai_depth_dict,
        )

        # Export inverted depth converted cubes in segy format
        cube_export(
            config_file=conf,
            export_cubes=rel_ai_depth_dict,
            start_dir=args.startdir,
            is_observed=False,
        )

        if args.verbose:
            print("Finished running seismic inversion")


if __name__ == "__main__":
    main()
