import xtgeo

from fmu.sim2seis.utilities import (
    SeismicName,
    Sim2SeisConfig,
    SingleSeismic,
)


def read_time_data(
    config: Sim2SeisConfig,
) -> tuple[dict[(str, str), SingleSeismic], dict[str, xtgeo.RegularSurface]]:
    time_cube_dict = {}
    # Extract file names with the correct prefix
    time_cube_names = [
        time_cube_names
        for time_cube_names in config.observed_time_data.time_cube_dir.glob(
            config.observed_time_data.time_cube_prefix + "*"
        )
        if "time" in time_cube_names.stem.lower()
    ]
    # Extract date - single or difference date
    for path_name in time_cube_names:
        # Use class objects to parse strings
        seis_name = SeismicName.parse_name(path_name.name)
        seis_date = seis_name.date
        # Limit the cube import to those that match the seismic single or difference
        # dates
        if (seis_date in config.global_params.seis_dates) or (
            seis_date in _diff_string(config.global_params.diff_dates)
        ):
            time_cube_dict[seis_name] = SingleSeismic(
                from_dir=config.observed_time_data.time_cube_dir,
                cube_name=seis_name,
                date=seis_date,
                cube=xtgeo.cube_from_file(path_name),
            )
    # Read time horizons
    time_surfs = {}
    for horizon in config.observed_depth_surf.horizon_names:
        time_name = config.observed_time_data.horizon_dir.joinpath(
            horizon.lower() + config.observed_time_data.time_suffix
        )
        try:
            time_surf = xtgeo.surface_from_file(str(time_name).lower())
        except ValueError as e:
            raise ValueError(f"unable to load time surface {time_name}: {e}")
        time_surf.name = horizon
        time_surfs[horizon] = time_surf

    return time_cube_dict, time_surfs


def _diff_string(diff_dates: list[list[str]]) -> list[str]:
    return ["_".join(two_dates) for two_dates in diff_dates]
