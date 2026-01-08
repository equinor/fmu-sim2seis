import argparse
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
        "--start-dir",
        type=Path,
        required=True,
        help="Start directory for running script (required)",
    )
    parser.add_argument(
        "-c",
        "--config-dir",
        type=Path,
        required=True,
        help="Path to config file (required)",
    )
    parser.add_argument(
        "-f",
        "--config-file",
        type=Path,
        required=True,
        help="Configuration yaml file name",
    )
    parser.add_argument(
        "-m",
        "--model-dir",
        type=Path,
        required=False,
        help="For ERT run: Absolute directory name for the configuration parameter"
        " file within the FMU project",
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
            "--no-attributes",
            type=bool,
            required=False,
            default=False,
            help="Skip generation of observed data attributes",
        )
    if "cleanup" in extra_arguments:
        parser.add_argument(
            "-p",
            "--prefix-list",
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
    run_folder = cwd.absolute()
    if not str(run_folder).endswith("rms/model"):
        warn("sim2seis workflow should be run from the rms/model folder.")
    if not run_folder.exists() and run_folder.is_dir():
        raise ValueError(
            f"Start directory does not exist or is not a directory: {run_folder}"
        )
    return run_folder
