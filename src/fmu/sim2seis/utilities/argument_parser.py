import argparse
from email.policy import default
from pathlib import Path
from warnings import warn


def parse_arguments(
    arguments, extra_arguments: list[str] | None = None
) -> argparse.Namespace:
    """
    Uses argparse to parse arguments as expected from command line invocation
    """
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument(
        "-s",
        "--startdir",
        type=Path,
        required=True,
        help="Start directory for running script (required)",
    )
    parser.add_argument(
        "-c",
        "--configdir",
        type=Path,
        required=True,
        help="Path to config file (required)",
    )
    parser.add_argument(
        "-f",
        "--configfile",
        type=Path,
        required=True,
        help="Configuration yaml file name",
    )
    if "attribute" in extra_arguments:
        parser.add_argument(
            "-a",
            "--attribute",
            type=str,
            required=False,
            default=False,
            help="Selection of 'amplitude' or 'relai' attributes. "
            "For sim2seis_map_attributes only",
        )
    if "verbose" in extra_arguments:
        parser.add_argument(
            "-v",
            "--verbose",
            type=bool,
            required=False,
            default=False,
            help="Select verbose or minimal output",
        )
    if "no_attributes" in extra_arguments:
        parser.add_argument(
            "-n",
            "--no_attributes",
            type=bool,
            required=False,
            default=False,
            help="Skip generation of observed data attributes",
        )
    if "cleanup" in extra_arguments:
        parser.add_argument(
            "-p",
            "--prefixlist",
            required=False,
            default=False,
            nargs="+",
            type=str,
            help="(Optional) List of prefixes in result pickle files to remove.\n"
            "Possible values: \n"
            "'observed_data', 'seis_4d', 'seis_4d_diff', 'relai', "
            "'depth_convert', 'amplitude_maps', 'relai_maps')\n"
            "If no prefixes are given, all pickle files will be removed",
        )
    return parser.parse_args(arguments)


def check_startup_dir(cwd: Path) -> Path:
    if str(cwd.absolute()).endswith("rms/model"):
        run_folder = cwd
    else:
        try:
            run_folder = cwd.joinpath("rms/model")
            assert run_folder.exists() and run_folder.is_dir()
        except AssertionError as e:
            warn(f"sim2seis workflow should be run from the rms/model folder. {e}")
            run_folder = cwd
    return run_folder
