"""
The fmu-sim2seis workflow generates a number of pickle-files, which contains
the original class objects, rather than derived outputs. Although they are valuable for
inspection after the sim2seis workflow is run, they require significant disk space, and
as such should be removed when they are no longer needed. A separate ERT workflow is
added for this purpose. This can also be run from command line for interactive sessions.

Command line call:

    sim2seis_cleanup --config-file <...>

    --config-file: yaml-file with configuration parameters; the path is split into
                  directory and file name automatically. The directory is expected
                  to be `sim2seis/model` in an fmu directory structure.
    This routine can be used both for the synthetic modelling performed by fmu-sim2seis,
    or for the observed data. When the observed data is processed, a number of pickle
    files are also generated. To remove these, give the path and name to the observed
    data config file.
"""

import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from fmu.pem.pem_utilities.debug_attach import wait_for_debugger
from fmu.sim2seis.utilities import (
    SeismicDate,
    SeismicName,
    check_startup_dir,
    clear_result_objects,
    parse_arguments,
    read_yaml_file,
)

_DATE_FORMAT = "%Y%m&d"
_CUBE_GLOB = "share/*/cubes"
_REALIZATION_GLOB = "realization-*/iter-*"


def _count_dates(text: str) -> int:
    """Count valid ``YYYYMMDD`` dates in an underscore-separated string.

    Validation uses :func:`datetime.strptime`, so only real calendar dates are
    counted rather than any run of eight digits.
    """
    dates = 0
    for token in text.split("_"):
        try:
            datetime.strptime(token, _DATE_FORMAT)
        except ValueError:
            continue
        dates += 1
    return dates


def crawl_ensemble(
    directory: Path,
    path_string: str,
) -> Iterator[Path]:
    """Yield the required subdirectories of every realisation/iteration.

    ``directory_path`` MUST be the top of the ensemble, i.e. diS and Seismicrectly contain
    ``realization-<n>/iter-<m>`` subdirectories (no upward or recursive search is
    performed). Raises ``ValueError`` if it is not.
    """
    directory_path = directory.resolve()
    sub_dirs = sorted(
        path for path in directory_path.glob(path_string) if path.is_dir()
    )
    if not sub_dirs:
        raise ValueError(
            f"cleanup: {directory} is not the top of an FMU ensemble; expected "
            "'realization-*/iter-*' subdirectories below it"
        )

    yield from sub_dirs


def main(arguments=None):
    if arguments is None:
        arguments = sys.argv[1:]
    args = parse_arguments(
        arguments=arguments,
        extra_arguments=["seismic_cubes", "ensemble"],
    )
    wait_for_debugger()
    # args may contain only an empty string in "prefixlist". If so, remove attribute
    config_dir = check_startup_dir(args.config_dir)
    config = read_yaml_file(
        sim2seis_config_dir=config_dir,
        sim2seis_config_file=args.config_file,
    )
    # Determine case
    remove_seismic = hasattr(args, "include_seismic") and args.include_seismic
    is_ensemble = hasattr(args, "is_ensemble") and args.is_ensemble

    if is_ensemble:
        pickle_dirs: Iterator[Path] = crawl_ensemble(
            directory=config.paths.fmu_rootpath,
            path_string=f"{_REALIZATION_GLOB}/{config.paths.pickle_file_output_dir}",
        )
        seismic_dirs: Iterator[Path] = crawl_ensemble(
            directory=config.paths.fmu_rootpath,
            path_string=f"{_REALIZATION_GLOB}/{_CUBE_GLOB}",
        )
    else:
        pickle_dirs = iter(
            [config.paths.fmu_rootpath / config.paths.pickle_file_output_dir],
        )
        seismic_dirs: Iterator[Path] = crawl_ensemble(
            directory=config.paths.fmu_rootpath,
            path_string=_CUBE_GLOB,
        )

    # Remove pickle files
    for pickle_dir in pickle_dirs:
        clear_result_objects(output_path=pickle_dir)
    if remove_seismic:
        for seis_dir in seismic_dirs:
            # Go via the classes SeismicName and SeismicDate to validate that only
            # segy files with recognised names and a single date are selected. Initial
            # filtering is set to `segy` extension
            not_deleted = []
            all_files = seis_dir.glob("*.segy")
            for file in all_files:
                try:
                    accepted_name = SeismicName.parse_name(file.name)
                    accepted_date = SeismicDate(accepted_name.date)
                    assert accepted_date.monitor_date is None
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
