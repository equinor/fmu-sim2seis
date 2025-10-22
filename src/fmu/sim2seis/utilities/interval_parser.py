from __future__ import annotations

"""
Parse yaml file with interval definitions and populate SeismicAttribute objects
"""

from collections import defaultdict
from pydantic import BaseModel, ConfigDict, DirectoryPath, Field, model_validator
from typing import Any, get_args
import xtgeo
from pathlib import Path

from .sim2seis_class_definitions import (
    DifferenceSeismic,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
    KnownAttributes,
    DomainDef,
)

# Type aliases
SeismicCube = SingleSeismic | DifferenceSeismic
SurfaceDict = dict[str, xtgeo.RegularSurface]
CubeDict = dict[SeismicName, SeismicCube]


class GlobalConfig(BaseModel):
    """Global configuration settings for seismic attribute generation.

    Args:
        gridhorizon_path: Path to directory containing surface files
        attributes: List of attribute types to calculate (e.g., ['rms', 'mean'])
        surface_postfix: Postfix to append to surface names
        scale_factor: Global scaling factor applied to all values
    """

    model_config = ConfigDict(frozen=True)

    gridhorizon_path: DirectoryPath
    attributes: list[KnownAttributes]
    surface_postfix: str
    scale_factor: float


class RootConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    global_config: GlobalConfig = Field(alias="global")
    cubes: dict[str, CubeConfig] = Field(default_factory=dict)


class CubeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    cube_prefix: str
    filename_tag_prefix: str
    seismic_path: DirectoryPath
    vertical_domain: DomainDef
    depth_reference: str
    offset: str
    formations: dict[str, FormationSettings]


class FormationSettings(BaseModel):
    """Settings for a formation, including horizons, shifts, and attributes."""

    model_config = ConfigDict(frozen=True)

    top_horizon: str
    bottom_horizon: str

    top_surface_shift: float = 0
    base_surface_shift: float = 0
    window_length: float | None = None

    attribute_overrides: dict[KnownAttributes, dict[str, Any]] = Field(
        default_factory=dict, exclude=True
    )

    @model_validator(mode="before")
    @classmethod
    def extract_attributes(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        attribute_overrides = {}
        for attr in get_args(KnownAttributes):
            if attr in data:
                attribute_overrides[attr] = data.pop(attr)

        data["attribute_overrides"] = attribute_overrides
        return data

    def build_interval_config(
        self, attribute: KnownAttributes, global_scale_factor: float
    ) -> IntervalConfig:
        config_dict: dict[str, Any]
        config_dict = {
            "top_horizon": self.top_horizon,
            "bottom_horizon": self.bottom_horizon,
            "top_surface_shift": self.top_surface_shift,
            "base_surface_shift": self.base_surface_shift,
            "window_length": self.window_length,
            "scale_factor": global_scale_factor,
        }

        if attribute in self.attribute_overrides:
            config_dict.update(self.attribute_overrides[attribute])

        return IntervalConfig(**config_dict)


class IntervalConfig(BaseModel):
    """Configuration for a seismic interval.

    An interval is uniquely defined by six parameters:
    - top_horizon: Name of the upper boundary surface
    - bottom_horizon: Name of the lower boundary surface (ignored if window_length is
    set)
    - top_surface_shift: Vertical shift applied to the top surface
    - base_surface_shift: Vertical shift applied to the base surface
    - window_length: Optional fixed interval length from top surface
    - scale_factor: Scaling factor applied to the values
    """

    model_config = ConfigDict(frozen=True)

    top_horizon: str
    bottom_horizon: str

    top_surface_shift: float
    base_surface_shift: float
    window_length: float | None = None
    scale_factor: float


def _group_attributes_by_interval(
    formation_settings: FormationSettings,
    global_config: GlobalConfig,
) -> dict[IntervalConfig, list[KnownAttributes]]:
    """Group attributes that share the same interval configuration.

    Each attribute (e.g., 'rms', 'mean', 'min') can override the formation's default
    interval settings. Attributes that end up with identical settings are grouped
    together.
    """

    interval_groups = defaultdict(list)
    for attribute in global_config.attributes:
        interval_key = formation_settings.build_interval_config(
            attribute, global_config.scale_factor
        )
        interval_groups[interval_key].append(attribute)

    return dict(interval_groups)


def _load_surface(
    surface_name: str,
    surfaces: dict[str, xtgeo.RegularSurface],
    horizon_postfix: str,
    gridhorizon_path: Path,
    window_length: float | None = None,
    base_surface: xtgeo.RegularSurface | None = None,
) -> xtgeo.RegularSurface:
    """Load a surface from either the surfaces dictionary or from file."""
    if window_length is not None and base_surface is not None:
        return base_surface + window_length

    surface_key = surface_name + horizon_postfix
    try:
        surface = surfaces.get(
            surface_key, xtgeo.surface_from_file(f"{gridhorizon_path}/{surface_key}")
        )
        surface.name = surface_name
        return surface
    except FileNotFoundError:
        raise ValueError(f"Surface file not found: {surface_key}")


def _create_seismic_attribute(
    interval_config: IntervalConfig,
    attributes: list[KnownAttributes],
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
    cube_info: CubeConfig,
    cube: SeismicCube,
) -> SeismicAttribute:
    """Create a single SeismicAttribute object for a given interval configuration."""
    attr_top_surface = _load_surface(
        surface_name=interval_config.top_horizon,
        surfaces=surfaces,
        horizon_postfix=global_config.surface_postfix,
        gridhorizon_path=global_config.gridhorizon_path,
    )

    attr_bottom_surface = _load_surface(
        surface_name=interval_config.bottom_horizon,
        surfaces=surfaces,
        horizon_postfix=global_config.surface_postfix,
        gridhorizon_path=global_config.gridhorizon_path,
        window_length=interval_config.window_length,
        base_surface=attr_top_surface,
    )

    return SeismicAttribute(
        surface=attr_top_surface,
        calc_types=attributes,
        scale_factor=interval_config.scale_factor,
        from_cube=cube,
        domain=cube_info.vertical_domain,
        window_length=interval_config.window_length,
        base_surface=attr_bottom_surface,
        top_surface_shift=interval_config.top_surface_shift,
        base_surface_shift=interval_config.base_surface_shift,
        info=cube_info,
    )


def _get_matching_cubes(cubes: CubeDict, cube_prefix: str) -> list[SeismicCube]:
    """Find all seismic cubes whose names match the given prefix."""
    return [
        cube
        for cube_name, cube in cubes.items()
        if cube_name.compare_without_date(cube_prefix)
    ]


def _create_formation_attributes(
    interval_groups: dict[IntervalConfig, list[KnownAttributes]],
    cube_info: CubeConfig,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
) -> list[SeismicAttribute]:
    """Create SeismicAttribute objects for each interval group and matching cube."""
    formation_attributes = []
    for interval_config, attrs in interval_groups.items():
        matching_cubes = _get_matching_cubes(cubes, cube_info.cube_prefix)
        for seismic_cube in matching_cubes:
            attribute = _create_seismic_attribute(
                interval_config=interval_config,
                attributes=attrs,
                surfaces=surfaces,
                global_config=global_config,
                cube_info=cube_info,
                cube=seismic_cube,
            )
            formation_attributes.append(attribute)
    return formation_attributes


def _process_formation(
    formation_settings: FormationSettings,
    cube_info: CubeConfig,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
) -> list[SeismicAttribute]:
    """Process a single formation and create its SeismicAttribute objects."""

    interval_groups = _group_attributes_by_interval(
        formation_settings=formation_settings,
        global_config=global_config,
    )

    return _create_formation_attributes(
        interval_groups=interval_groups,
        cube_info=cube_info,
        cubes=cubes,
        surfaces=surfaces,
        global_config=global_config,
    )


def populate_seismic_attributes(
    config: dict[str, Any],
    cubes: CubeDict,
    surfaces: SurfaceDict,
) -> list[SeismicAttribute]:
    """Create SeismicAttribute objects for each unique interval configuration.

    Args:
        config: Configuration dictionary containing global settings,
            cube name prefixes and window definition for each attribute
        cubes: Available seismic cubes indexed by their SeismicName
        surfaces: Available surfaces indexed by their names

    Returns:
        List of SeismicAttribute objects, one for each unique interval configuration

    Raises:
        ValueError: If no attributes could be generated (likely due to configuration
        mismatch)
    """
    root_config = RootConfig(**config)
    seismic_attributes = []
    for cube_info in root_config.cubes.values():
        for formation_settings in cube_info.formations.values():
            formation_attributes = _process_formation(
                formation_settings=formation_settings,
                cube_info=cube_info,
                cubes=cubes,
                surfaces=surfaces,
                global_config=root_config.global_config,
            )
            seismic_attributes.extend(formation_attributes)

    if not seismic_attributes:
        raise ValueError(
            "No attributes generated. Please check configuration settings."
        )

    return seismic_attributes
