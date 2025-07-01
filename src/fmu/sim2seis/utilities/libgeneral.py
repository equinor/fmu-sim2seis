"""
Various general common routines.

NB! When editing this, always save the full project to make edits available!

JRIV
"""

import shutil
import subprocess
from pathlib import Path
from typing import List

import fmu.config.utilities as utils

WARN_METADATA = True  # False will silence Warnings messages


def global_config(path_to_global_var_yml_file: Path | str) -> dict:
    """Get the correct global config dictionary; inludes also some checks.

    The paths to the global config files are here hardcoded.

    Args:
        path_to_global_var_yml_file: e.g. ../../fmu_config/global_variables.yml

    Returns:
        The global_config, as a dict
    """

    cfg = utils.yaml_load(str(path_to_global_var_yml_file))

    for required_key in ["global", "masterdata", "access", "model"]:
        if required_key not in cfg and WARN_METADATA:
            print(
                "Warning! The global config is missing {required_key}! "
                "The fmu.dataio will export data, but without metadata."
            )

    return cfg


def cleanup_folders_dataio() -> None:
    """Make the necessary folders and cleanup for dataio output."""
    dataio_folders = [
        "../../share/results",
        "../../share/preprocessed",
        "../../share/observations",
    ]

    current = Path(".")
    current_abs = current.absolute()

    if current_abs.name == "model" and current_abs.parent.name == "rms":
        print("Seems that you run from rms/model folder --- good!")
    else:
        raise RuntimeError(
            f"You do not run this from the rms/model folder but from {current_abs}!"
        )

    for folder in dataio_folders:
        shutil.rmtree(folder, ignore_errors=True)
        print("Removed:", folder)


def make_folders(list_of_input_paths: List[Path | str]) -> None:
    """Make folders if they do not exist."""

    if not isinstance(list_of_input_paths, list):
        raise ValueError("Input must be a list of folders")

    for input_path in list_of_input_paths:
        if not isinstance(input_path, Path):
            input_path = Path(input_path)

        if input_path.is_file():
            raise ValueError(
                "STOP! Your input is already an existing file, not a folder"
            )

        # this will create the folder unless it already exists:
        input_path.mkdir(parents=True, exist_ok=True)


def make_symlink(
    source: Path | str, link_name: Path | str, verbose: bool = False
) -> None:
    """Create or update a symbolic link, with additional checks.

    Args:
        source (str, Path): Filename or folder as source, relative to path given
            in link_name!
        link_name (str, Path): Name of symbolic link
        verbose: (bool): Print progress information

    """
    if not isinstance(source, Path):
        source = Path(source)
    if not isinstance(link_name, Path):
        link_name = Path(link_name)

    target_folder = link_name.parent

    relative_source = target_folder / source
    if relative_source.is_file():
        source_type = "file"
    elif relative_source.exists():
        source_type = "folder"
    else:
        raise (
            FileNotFoundError(
                f"Something is wrong with: {relative_source}. Perhaps not existing?"
            )
        )

    # -n: treat link_name as a normal file if it is a symbolic link to a directory
    subprocess.run(["ln", "-sfn", source, link_name], check=True)

    if source_type == "file" and not link_name.is_file():
        raise FileNotFoundError(
            f"The source or link file does exist, broken link?: {source} -> {link_name}"
        )
    if source_type == "file" and not relative_source.is_file():
        raise FileNotFoundError(f"The source file does not exist: {source}")
    if source_type == "folder" and not link_name.exists():
        raise FileNotFoundError(
            f"The result folder does exist, broken link?: {source} -> {link_name}"
        )
    if verbose:
        print("\nOK")

    if verbose:
        print(
            f"Seen from folder [{target_folder}]: "
            f"symlinked {source_type} [{source}] to "
            f"[{link_name.name}]"
        )


def run_external_silent(commands: List[str], timeout: int | None = None) -> str:
    result = subprocess.run(
        commands,
        capture_output=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with error: {result.stderr}")
    return str(result.stdout)
