import argparse
from pathlib import Path
from warnings import warn


def _str2bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(
        f"Invalid boolean value: {value!r}. Expected true/false."
    )


def parse_arguments(
    arguments, extra_arguments: list[str] | None = None
) -> argparse.Namespace:
    """
    Uses argparse to parse arguments as expected from command line invocation
    """
    extra_arguments = extra_arguments or []
    parser = argparse.ArgumentParser(__file__)
    parser.add_argument(
        "-c",
        "--config-dir",
        type=Path,
        required=True,
        help="Path to config directory (required), should end with 'sim2seis/model'",
    )
    parser.add_argument(
        "-f",
        "--config-file",
        type=Path,
        required=True,
        help="Configuration yaml file name",
    )
    parser.add_argument(
        "-g",
        "--global-dir",
        type=Path,
        required=True,
        help="Relative path to global config file (required)",
    )
    parser.add_argument(
        "-o",
        "--global-file",
        type=Path,
        required=True,
        help="Global configuration yaml file name (required)",
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
            type=_str2bool,
            required=False,
            default=False,
            help="Select verbose or minimal output",
        )
    if "no_attributes" in extra_arguments:
        parser.add_argument(
            "-n",
            "--no-attributes",
            type=_str2bool,
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
    if not str(run_folder).endswith("sim2seis/model"):
        warn("sim2seis workflow should be run from the sim2seis/model folder.")
    if not (run_folder.exists() and run_folder.is_dir()):
        raise ValueError(
            f"Start directory does not exist or is not a directory: {run_folder}"
        )
    return run_folder
