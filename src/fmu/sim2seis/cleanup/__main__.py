import sys
from collections.abc import Iterator
from pathlib import Path

from fmu.sim2seis.utilities import (
    SeismicDate,
    SeismicName,
    check_startup_dir,
    clear_result_objects,
    parse_arguments,
    read_yaml_file,
)

_CUBE_GLOB = "share/*/cubes"
_REALIZATION_GLOB = "realization-*/iter-*"


def crawl_structure(
    directory: Path,
    path_string: str,
) -> Iterator[Path]:
    """Yield the required subdirectories of every realisation/iteration.

    ``directory_path`` must be the top of the ensemble or fmu directory structure,
        either containing the results from a single run or an `ert` ensemble with
    ``realization-<n>/iter-<m>``.
    ``path_string`` contains names for subdirectories that are searched for.
        There is no upward or recursive search performed. Raises ``ValueError`` if no
        subdirectories are found. ``path_string`` may contain wildcard characters.
    """
    directory_path = directory.resolve()
    sub_dirs = sorted(
        path for path in directory_path.glob(path_string) if path.is_dir()
    )
    if not sub_dirs:
        raise ValueError(
            f"cleanup: {directory} is not the top of an FMU directory structure"
        )

    yield from sub_dirs


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(
        arguments=arguments,
        extra_arguments=["seismic_cubes", "ensemble"],
    )
    config_dir = check_startup_dir(args.config_dir)
    config = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=args.config_file,
    )
    # Determine case
    remove_seismic = hasattr(args, "include_seismic") and args.include_seismic
    is_ensemble = hasattr(args, "is_ensemble") and args.is_ensemble

    if is_ensemble:
        # Start at current working directory
        pickle_dirs: Iterator[Path] = crawl_structure(
            directory=Path.cwd(),
            path_string=f"{_REALIZATION_GLOB}/{config.paths.pickle_file_output_dir}",
        )
        if remove_seismic:
            seismic_dirs: Iterator[Path] = crawl_structure(
                directory=Path.cwd(),
                path_string=f"{_REALIZATION_GLOB}/{_CUBE_GLOB}",
            )
    else:
        pickle_dirs = iter(
            [config.paths.fmu_rootpath / config.paths.pickle_file_output_dir],
        )
        if remove_seismic:
            seismic_dirs: Iterator[Path] = crawl_structure(
                directory=config.paths.fmu_rootpath,
                path_string=_CUBE_GLOB,
            )

    # Remove pickle files
    for pickle_dir in pickle_dirs:
        clear_result_objects(output_path=pickle_dir)
    not_deleted = []
    if remove_seismic:
        for seis_dir in seismic_dirs:
            # Go via the classes SeismicName and SeismicDate to validate that only
            # segy files with recognised names and a single date are selected. Initial
            # filtering is set to `segy` extension
            all_files = seis_dir.glob("*.segy")
            for file in all_files:
                try:
                    accepted_name = SeismicName.parse_name(file.name)
                    accepted_date = SeismicDate(accepted_name.date)
                    if accepted_date.monitor_date is not None:
                        raise ValueError("difference object - should not be deleted")
                    try:
                        file.unlink(missing_ok=True)
                    except OSError:
                        not_deleted.append(file)
                except (AssertionError, TypeError, ValueError):
                    pass
        if not_deleted:
            raise OSError(
                "cleanup: could not delete the following files: "
                + ", ".join(str(path) for path in not_deleted)
            )


if __name__ == "__main__":
    main()
