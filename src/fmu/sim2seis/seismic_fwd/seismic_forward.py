from pathlib import Path
from shutil import copy2, move as rename

import xtgeo
from seismic_forward.simulation import run_simulation

from fmu.sim2seis.utilities import (
    SeismicDate,
    SeismicName,
    Sim2SeisConfig,
    SingleSeismic,
    libseis,
)
from fmu.tools import DomainConversion


def exe_seismic_forward(
    config_file: Sim2SeisConfig,
    velocity_model: DomainConversion,
    verbose: bool = False,
    # ) -> Tuple[dict[SeismicName, SingleSeismic], dict[SeismicName, SingleSeismic]]:
) -> (dict[SeismicName, SingleSeismic], dict[SeismicName, SingleSeismic]):
    """
    Run seismic forward model, perform domain conversion on the depth
    cubes to time, return both depth and time cubes
    """

    depth_cubes = {}
    time_cubes = {}

    for date in libseis.get_listed_seis_dates(config_file.global_params.seis_dates):
        # Copy the right vintage PEM output file to generic pem.grdecl
        copy2(
            src=config_file.seismic_fwd.pem_output_dir
            / Path("pem--" + date + ".grdecl"),
            dst=config_file.seismic_fwd.pem_output_dir / Path("pem.grdecl"),
        )

        if date == config_file.global_params.seis_dates[0]:
            # Generate a twt framework for the initial conditions
            model_file = config_file.seismic_fwd.stack_model_path / "model_file_twt.xml"
            result = run_simulation(model_file)
            assert result["success"]  # Success == True

        for stack, model in config_file.seismic_fwd.stack_models.items():
            result = run_simulation(model)
            assert result["success"]
            if verbose:
                print(result)

            # Modify name of synthetic seismic segy files output
            s_depth_src = config_file.seismic_fwd.seismic_output_dir.joinpath(
                config_file.seismic_fwd.segy_depth
            )
            depth_name_str = f"syntseis--amplitude_{stack}_depth--{date}.segy"
            new_depth_name = SeismicName.parse_name(depth_name_str)
            s_depth_file = config_file.seismic_fwd.seismic_output_dir.joinpath(
                depth_name_str
            )
            rename(s_depth_src, s_depth_file)
            depth_cube = xtgeo.cube_from_file(s_depth_file)
            depth_cubes[new_depth_name] = SingleSeismic(
                from_dir=config_file.seismic_fwd.seismic_output_dir,
                cube_name=new_depth_name,
                date=SeismicDate(date),
                cube=depth_cube,
            )
            # To get consistent depth/time conversion, we use the method in fmu-tools
            time_cube = velocity_model.time_convert_cube(
                incube=depth_cube,
                tinc=config_file.depth_conversion.t_inc,
                tmax=config_file.depth_conversion.max_time,
                tmin=config_file.depth_conversion.min_time,
            )
            time_name_str = f"syntseis--amplitude_{stack}_time--{date}.segy"
            new_time_name = SeismicName.parse_name(time_name_str)
            time_cubes[new_time_name] = SingleSeismic(
                from_dir=config_file.seismic_fwd.seismic_output_dir,
                cube_name=new_time_name,
                date=SeismicDate(date),
                cube=time_cube,
            )

    # return depth_cubes, time_cubes
    return depth_cubes, time_cubes


def read_time_and_depth_horizons(
    config: Sim2SeisConfig,
) -> (dict[str, xtgeo.RegularSurface], dict[str, xtgeo.RegularSurface]):
    """
    Read the time and depth surfaces that are listed in the configuration file
    for time/depth conversions
    """
    time_surfs = {}
    depth_surfs = {}
    for horizon in config.depth_conversion.horizon_names:
        time_name = config.depth_conversion.horizon_dir.joinpath(
            horizon.lower() + config.depth_conversion.time_suffix
        )
        time_surf = xtgeo.surface_from_file(str(time_name))
        time_surf.name = horizon
        time_surfs[time_name.name] = time_surf

        depth_name = config.depth_conversion.horizon_dir.joinpath(
            horizon.lower() + config.depth_conversion.depth_suffix
        )
        depth_surf = xtgeo.surface_from_file(str(depth_name))
        depth_surf.name = horizon
        depth_surfs[depth_name.name] = depth_surf

    return time_surfs, depth_surfs
