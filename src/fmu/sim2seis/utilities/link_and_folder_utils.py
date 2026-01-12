"""
Various general common routines.

NB! When editing this, always save the full project to make edits available!

JRIV
"""

import subprocess
from pathlib import Path


def make_folders(list_of_input_paths: list[Path | str]) -> None:
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
