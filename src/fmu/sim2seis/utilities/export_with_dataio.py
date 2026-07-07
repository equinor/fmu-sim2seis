from os import symlink, unlink
from pathlib import Path

import numpy as np
import xtgeo

from fmu import dataio, tools
from fmu.pem.pem_utilities import restore_dir

from .sim2seis_class_definitions import (
    DifferenceSeismic,
    ErrorConfig,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
)
from .sim2seis_config_validation import Sim2SeisConfig


def cube_export(
    config_file: Sim2SeisConfig,
    export_cubes: dict[SeismicName, DifferenceSeismic | SingleSeismic],
    is_observed: bool = False,
    is_preprocessed: bool = False,
    override_folder: str = "",
) -> None:
    """Output depth cube via fmu.dataio"""
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
    is_observed: bool = False,
    is_preprocessed: bool = False,
) -> None:
    """Output attribute map via fmu.dataio"""
    fmu_rootpath = config_file.paths.fmu_rootpath

    # prepare for ert/webviz export
    simgrid, zone_def, region_def = _get_grid_info(
        config_file=config_file,
        root_dir=fmu_rootpath,
    )
    # Resolve the absolute output path against fmu_rootpath, so it does not
    # depend on the current working directory at call time.
    if is_observed:
        output_path = (
            fmu_rootpath / config_file.paths.output_dir_observed_data
        ).resolve()
    else:
        output_path = (
            fmu_rootpath / config_file.paths.output_dir_modelled_data
        ).resolve()
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
                    name=attr.formation,
                    tagname=tag_str,
                    vertical_domain=attr.from_cube.cube_name.domain,
                    rep_include=False,
                    table_index=["REGION"],
                )
                export_obj.export(value)  # type: ignore
                # Make ert/webviz dataframe. Observation error only applies to
                # observed data; modelled data are written without error.
                if is_observed and attr.error is not None:
                    attribute_error: xtgeo.RegularSurface | float = (
                        _build_error_surface(value, attr.error)
                    )
                    attribute_error_minimum = attr.error.minimum or None
                else:
                    attribute_error = 0.0
                    attribute_error_minimum = None
                attr_df = tools.sample_attributes_for_sim2seis(
                    grid=simgrid,
                    attribute=value,
                    attribute_error=attribute_error,
                    attribute_error_minimum=attribute_error_minimum,
                    region=region_def,
                    zone=zone_def,
                )
                meta_data = Path(export_obj.export(attr_df))
                with restore_dir(output_path):
                    # Construct file names for output to webviz and ert.
                    # These are bare basenames, written into the current
                    # ``output_path`` cwd established by ``restore_dir`` above.
                    # Using ``Path`` ensures only the suffix is replaced and
                    # avoids accidentally rewriting an inner ``.csv`` substring.
                    ert_filename = Path(meta_data.name).with_suffix(".txt")
                    webviz_filename = ert_filename.with_name(
                        "meta--" + ert_filename.name
                    )
                    parquet_filename = ert_filename.with_suffix(".parquet")
                    # ``exists()`` follows symlinks, so a broken symlink would
                    # be missed and the subsequent ``symlink`` call would then
                    # fail with ``FileExistsError``; ``is_symlink`` catches that
                    # case as well.
                    if webviz_filename.exists() or webviz_filename.is_symlink():
                        try:  # noqa: SIM105
                            unlink(webviz_filename)
                        except FileNotFoundError:
                            pass
                    symlink(src=meta_data, dst=webviz_filename)
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
                    # Parquet copy of the same dataframe for downstream consumers.
                    # Floats are downcast to float32 (~7 significant digits) to
                    # cut file size; integer columns are preserved. UTM columns
                    # fit comfortably as long as sub-decimetre precision is not
                    # required.
                    float_cols = attr_df.select_dtypes(include="floating").columns
                    attr_df.astype(dict.fromkeys(float_cols, "float32")).to_parquet(
                        parquet_filename,
                        engine="pyarrow",
                        compression="zstd",
                        index=False,
                    )


def _build_error_surface(
    attribute_map: xtgeo.RegularSurface,
    error: ErrorConfig,
) -> xtgeo.RegularSurface:
    """Build an absolute observation-error surface for an attribute map.

    Supports the four combinations of {relative, absolute} error given either
    as a single scalar ``value`` or as a spatially varying ``error_surface``.
    A relative error is multiplied by the attribute values; an absolute error
    is used directly. The error surface is imported with xtgeo and must share
    the geometry of the attribute maps.
    """
    if error.error_surface is not None:
        err = xtgeo.surface_from_file(error.error_surface)
        if not err.compare_topology(attribute_map):
            raise ValueError(
                f"Error surface '{error.error_surface}' does not have the same "
                "geometry as the attribute maps."
            )
    else:
        err = attribute_map.copy()
        err.values = error.value

    if error.type == "relative":
        err.values = attribute_map.values * err.values
    err.values = np.abs(err.values)
    return err


def _get_grid_info(
    config_file: Sim2SeisConfig,
    root_dir: Path,
) -> tuple[xtgeo.Grid, xtgeo.GridProperty, xtgeo.GridProperty]:
    # Import grid, zones, regions
    with restore_dir(root_dir):
        grid = xtgeo.grid_from_file(
            config_file.paths.webviz_map_dir.joinpath(config_file.webviz_map.grid_file)
        )
        zones = xtgeo.gridproperty_from_file(
            config_file.paths.webviz_map_dir.joinpath(config_file.webviz_map.zone_file)
        )
        regions = xtgeo.gridproperty_from_file(
            config_file.paths.webviz_map_dir.joinpath(
                config_file.webviz_map.region_file
            )
        )
        return grid, zones, regions
