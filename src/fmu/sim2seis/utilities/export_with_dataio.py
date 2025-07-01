from contextlib import suppress
from os import getenv, symlink, unlink
from pathlib import Path

import xtgeo

from fmu import dataio, tools
from fmu.pem.pem_utilities import restore_dir

from .sim2seis_class_definitions import (
    DifferenceSeismic,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
)
from .sim2seis_config_validation import Sim2SeisConfig


def cube_export(
    config_file: Sim2SeisConfig,
    export_cubes: dict[SeismicName, DifferenceSeismic | SingleSeismic],
    start_dir: Path,
    is_observed: bool = False,
) -> None:
    global_variables = config_file.global_params.global_config
    """Output depth cube via fmu.dataio"""
    try:
        # _ERT_RUNPATH will point to the top of the fmu directory structure, as
        # is expected by fmu-dataio, so no need to move up
        run_path = Path(getenv("_ERT_RUNPATH"))
        rel_dir = Path(".")
    except TypeError:
        # in case this is run from command line, _ERT_RUNPATH is not set, and start_dir
        # is at ./rms/model, relative to the top of the fmu directory structure. To get
        # the requirements of fmu-dataio right, we need to move up two levels
        run_path = Path(start_dir)
        rel_dir = Path("../..")

    with restore_dir(run_path / rel_dir):
        for key, value in export_cubes.items():
            if value.base_date is None and value.monitor_date is None:
                time_data = [[value.date]]
            else:
                time_data = [[value.monitor_date, "monitor"], [value.base_date, "base"]]
            if key.stack:
                tag_str = key.attribute + "_" + str(key.stack) + "_" + key.domain
            else:
                tag_str = key.attribute + "_" + key.domain
            export_obj = dataio.ExportData(
                config=global_variables,
                content="seismic",
                content_metadata={"attribute": key.attribute},
                timedata=time_data,
                is_observation=is_observed,
                name=key.process,
                tagname=tag_str,
                vertical_domain=key.domain,
                rep_include=False,
            )
            export_obj.export(value.cube)  # type: ignore


def attribute_export(
    config_file: Sim2SeisConfig,
    export_attributes: list[SeismicAttribute],
    start_dir: Path,
    is_observed: bool = False,
) -> None:
    global_variables = config_file.global_params.global_config
    """Output attribute map via fmu.dataio"""
    try:
        run_path = Path(getenv("_ERT_RUNPATH"))
    except TypeError:
        run_path = start_dir

    # prepare for ert/webviz export
    simgrid, zone_def, region_def = _get_grid_info(
        config_file=config_file,
        start_dir=start_dir,
    )
    # Must determine the absolute output path before changing directory
    output_path = config_file.webviz_map.output_path.resolve()
    with restore_dir(run_path.joinpath("../..")):
        for attr in export_attributes:
            for calc, value in zip(attr.calc_types, attr.value):
                key = attr.from_cube.cube_name
                if key.stack:
                    tag_str = (
                        key.attribute
                        + "_"
                        + str(key.stack)
                        + "_"
                        + calc
                        + "_"
                        + key.domain
                    )
                else:
                    tag_str = key.attribute + "_" + calc + "_" + key.domain
                export_obj = dataio.ExportData(
                    config=global_variables,
                    content="seismic",
                    content_metadata={
                            "attribute": attr.from_cube.cube_name.attribute,
                            "calculation": calc,
                            "zrange": attr.window_length,
                            "stacking_offset": attr.from_cube.cube_name.stack,
                        },
                    timedata=[
                        [attr.from_cube.monitor_date, "monitor"],
                        [attr.from_cube.base_date, "base"],
                    ],
                    is_observation=is_observed,
                    name=attr.surface.name,
                    tagname=tag_str,
                    vertical_domain=attr.from_cube.cube_name.domain,
                    rep_include=False,
                    table_index=["REGION"],
                )
                export_obj.export(value)  # type: ignore
                # Make ert/webviz dataframe
                attr_df = tools.sample_attributes_for_sim2seis(
                    grid=simgrid,
                    attribute=value,
                    attribute_error=config_file.webviz_map.attribute_error,
                    region=region_def,
                    zone=zone_def,
                )
                meta_data = Path(export_obj.export(attr_df))
                with restore_dir(output_path):
                    # Construct file names for output to webviz and ert
                    ert_filename = meta_data.name.replace(".csv", ".txt")
                    webviz_filename = "--".join(["meta", ert_filename])
                    if Path(webviz_filename).exists():
                        try:  # noqa: SIM105
                            unlink(Path(webviz_filename))
                        except FileNotFoundError:
                            pass
                    symlink(
                        src=meta_data,
                        dst=Path(webviz_filename)
                    )
                    # attr_df.to_csv(webviz_filename, index=False)
                    attr_df.to_csv(
                        ert_filename,
                        index=False,
                        header=False,
                        sep=" ",
                        float_format="%.6f",
                        columns=["OBS", "OBS_ERROR"],
                    )


def _get_grid_info(
    config_file: Sim2SeisConfig,
    start_dir: Path,
) -> (xtgeo.Grid, xtgeo.GridProperty, xtgeo.GridProperty):
    # Import grid, zones, regions
    with restore_dir(start_dir):
        grid = xtgeo.grid_from_file(
            config_file.webviz_map.grid_path.joinpath(config_file.webviz_map.grid_file)
        )
        zones = xtgeo.gridproperty_from_file(
            config_file.webviz_map.grid_path.joinpath(config_file.webviz_map.zone_file)
        )
        regions = xtgeo.gridproperty_from_file(
            config_file.webviz_map.grid_path.joinpath(
                config_file.webviz_map.region_file
            )
        )
        return grid, zones, regions
