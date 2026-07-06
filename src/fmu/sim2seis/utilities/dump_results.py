from pathlib import Path
from pickle import dump, load
from typing import Any


def dump_result_objects(
    output_path: Path,
    file_name: Path,
    output_obj: Any,
) -> None:
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        full_path = output_path / file_name
        with full_path.open(mode="wb") as f_out:
            dump(output_obj, f_out)  # type: ignore
    except OSError as e:
        raise ValueError(f"{__file__}: unable to dump pickle objects: {e}")


def retrieve_result_objects(
    input_path: Path,
    file_name: Path,
) -> Any:
    try:
        full_path = input_path / file_name
        with full_path.open(mode="rb") as f_in:
            return load(f_in)
    except OSError as e:
        raise ValueError(f"{__file__}: unable to load pickle objects: {e}")


def clear_result_objects(
    output_path: Path,
) -> None:
    try:
        [f.unlink() for f in output_path.glob("*.pkl")]
    except FileNotFoundError as e:
        raise ValueError(f"{__file__}: unable to remove file\nError message: {e}")
