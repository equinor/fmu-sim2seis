from os import symlink, unlink
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
    config_dir: Path,
    is_observed: bool = False,
    is_preprocessed: bool = False,
    override_folder: str = "",
) -> None:
    """Output depth cube via fmu.dataio"""
    global_variables = config_file.global_params.global_config
    fmu_rootpath = config_file.paths.fmu_rootpath

    with restore_dir(fmu_rootpath):
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
                preprocessed=is_preprocessed,
                forcefolder=override_folder,
                name=key.process,
                tagname=tag_str,
                vertical_domain=key.domain,
                rep_include=False,
            )
            export_obj.export(value.cube)  # type: ignore


def attribute_export(
    config_file: Sim2SeisConfig,
    export_attributes: list[SeismicAttribute],
    config_dir: Path,
    is_observed: bool = False,
    is_preprocessed: bool = False,
) -> None:
    """Output attribute map via fmu.dataio"""
    global_variables = config_file.global_params.global_config
    fmu_rootpath = config_file.paths.fmu_rootpath

    # prepare for ert/webviz export
    simgrid, zone_def, region_def = _get_grid_info(
        config_file=config_file,
        config_dir=config_dir,
    )
    # Resolve the absolute output path against config_dir, so it does not
    # depend on the current working directory at call time.
    if is_preprocessed:
        output_path = (config_dir / config_file.paths.output_dir_observed_data).resolve()
    else:
        output_path = (config_dir / config_file.paths.output_dir_modelled_data).resolve()
    with restore_dir(fmu_rootpath):
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
                        "workflow": "sim2seis",
                        "calculation": calc,
                        "zrange": attr.window_length,
                        "stacking_offset": attr.from_cube.cube_name.stack,
                    },
                    timedata=[
                        [attr.from_cube.monitor_date, "monitor"],
                        [attr.from_cube.base_date, "base"],
                    ],
                    is_observation=is_observed,
                    preprocessed=is_preprocessed,
                    name=attr.top_surface.name,
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
                    symlink(src=meta_data, dst=Path(webviz_filename))
                    # attr_df.to_csv(webviz_filename, index=False)
                    # Modelled data will not have observation error
                    columns = ["OBS", "OBS_ERROR"] if is_observed else ["OBS"]
                    attr_df.to_csv(
                        ert_filename,
                        index=False,
                        header=False,
                        sep=" ",
                        float_format="%.6f",
                        columns=columns,
                    )


def _get_grid_info(
    config_file: Sim2SeisConfig,
    config_dir: Path,
) -> tuple[xtgeo.Grid, xtgeo.GridProperty, xtgeo.GridProperty]:
    # Import grid, zones, regions
    with restore_dir(config_dir):
        grid = xtgeo.grid_from_file(
            config_file.paths.grid_dir.joinpath(config_file.webviz_map.grid_file)
        )
        zones = xtgeo.gridproperty_from_file(
            config_file.paths.grid_dir.joinpath(config_file.webviz_map.zone_file)
        )
        regions = xtgeo.gridproperty_from_file(
            config_file.paths.grid_dir.joinpath(config_file.webviz_map.region_file)
        )
        return grid, zones, regions
