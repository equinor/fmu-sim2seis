from pathlib import Path
from pickle import dump, load


def dump_result_objects(
    output_path: Path,
    file_name: Path,
    output_obj: any,
) -> None:
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        full_path = output_path / file_name
        with full_path.open(mode="wb") as f_out:
            dump(output_obj, f_out)  # type: ignore
    except IOError as e:
        raise ValueError(f"{__file__}: unable to dump pickle objects: {e}")


def retrieve_result_objects(
    input_path: Path,
    file_name: Path,
) -> any:
    try:
        full_path = input_path / file_name
        with full_path.open(mode="rb") as f_in:
            return load(f_in)
    except IOError as e:
        raise ValueError(f"{__file__}: unable to load pickle objects: {e}")


def clear_result_objects(
    output_path: Path,
    prefix_list: list[str] | None = None,
) -> None:
    try:
        if not prefix_list:
            [f.unlink() for f in output_path.glob("*.pkl")]
        else:
            for pre_fix in prefix_list:
                [f.unlink() for f in output_path.glob(pre_fix + "*.pkl")]
    except FileNotFoundError as e:
        raise ValueError(f"{__file__}: unable to remove file\nError message: {e}")
