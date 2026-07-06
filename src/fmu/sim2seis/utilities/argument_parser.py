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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--config-file",
        type=Path,
        required=True,
        help="Configuration yaml path name",
    )
    if "global_file" in extra_arguments:
        parser.add_argument(
            "-g",
            "--global-file",
            type=Path,
            required=True,
            help="Global configuration yaml path name (required)",
        )
    if "obs_date_prefix" in extra_arguments:
        parser.add_argument(
            "-o",
            "--obs-date-prefix",
            type=str,
            required=True,
            help="Global seismic section: Prefix for seismic dates for observed data",
        )
    if "mod_date_prefix" in extra_arguments:
        parser.add_argument(
            "-m",
            "--mod-date-prefix",
            type=str,
            required=True,
            help="Global seismic section: Prefix for seismic dates for modelled data",
        )
    if "attribute" in extra_arguments:
        parser.add_argument(
            "-a",
            "--attribute",
            type=str,
            required=True,
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
    if "seismic_cubes" in extra_arguments:
        parser.add_argument(
            "-s",
            "--include-seismic",
            type=_str2bool,
            required=False,
            default=True,
            help="(Optional) Include single date seismic cubes in the files to be "
            "deleted, default=True",
        )
    if "ensemble" in extra_arguments:
        parser.add_argument(
            "-i",
            "--is_ensemble",
            type=_str2bool,
            required=False,
            default=False,
            help="(Optional) Remove intermediate files for all realizations, "
            "default=False",
        )
    args = parser.parse_args(arguments)

    # Split config and global file paths and file names
    args.config_dir = Path(args.config_file.parent)
    args.config_file = Path(args.config_file.name)
    if hasattr(args, "global_file"):
        args.global_dir = Path(args.global_file.parent)
        args.global_file = Path(args.global_file.name)

    return args


def check_startup_dir(cwd: Path) -> Path:
    config_folder = cwd.absolute()
    if not str(config_folder).endswith("sim2seis/model"):
        warn("sim2seis workflow should be run from the sim2seis/model folder.")
    if not (config_folder.exists() and config_folder.is_dir()):
        raise ValueError(
            f"Start directory does not exist or is not a directory: {config_folder}"
        )
    return config_folder
