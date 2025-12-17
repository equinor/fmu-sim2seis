"""
Parse yaml file with interval definitions and populate SeismicAttribute objects
"""

from __future__ import annotations

import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, cast, get_args

import xtgeo
from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    ValidationInfo,
    model_validator,
)
from pydantic_core import PydanticCustomError

from .sim2seis_class_definitions import (
    DifferenceSeismic,
    KnownAttributes,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
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


class FormationSettings(BaseModel):

    model_config = ConfigDict(frozen=True)

    top_horizon: str | None = None
    bottom_horizon: str | None = None

    top_surface_shift: float = 0
    bottom_surface_shift: float = 0
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
        self,
        attribute: KnownAttributes,
        global_scale_factor: float,
        formation_name: str,
        cube_name: str,
    ) -> IntervalConfig:
        config_dict: dict[str, Any] = {
            "top_horizon": self.top_horizon,
            "bottom_horizon": self.bottom_horizon,
            "top_surface_shift": self.top_surface_shift,
            "bottom_surface_shift": self.bottom_surface_shift,
            "window_length": self.window_length,
            "scale_factor": global_scale_factor,
        }

        if attribute in self.attribute_overrides:
            config_dict.update(self.attribute_overrides[attribute])

        return IntervalConfig.model_validate(
            config_dict,
            context={
                "cube_name": cube_name,
                "formation_name": formation_name,
                "attribute": attribute,
            },
        )


class CubeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    cube_prefix: str
    formations: dict[str, FormationSettings]


class IntervalConfig(BaseModel):
    """Configuration for a seismic interval.

    An interval is uniquely defined by six parameters:
    - top_horizon: Name of the upper boundary surface
    - bottom_horizon: Name of the lower boundary surface (ignored if window_length is
    set)
    - top_surface_shift: Vertical shift applied to the top surface
    - bottom_surface_shift: Vertical shift applied to the bottom surface
    - window_length: Optional fixed interval length from top surface
    - scale_factor: Scaling factor applied to the values
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    top_horizon: str | None = None
    bottom_horizon: str | None = None

    top_surface_shift: float
    bottom_surface_shift: float
    window_length: float | None = None
    scale_factor: float

    @model_validator(mode="after")
    def validate_horizon_requirements(self, info: ValidationInfo) -> IntervalConfig:
        ctx = info.context or {}
        cube_name = ctx.get("cube_name", "unknown")
        formation_name = ctx.get("formation_name", "unknown")
        attribute = ctx.get("attribute", "unknown")

        location = (
            f"In cube '{cube_name}', formation '{formation_name}'"
            f", attribute '{attribute}'"
        )

        if not self.top_horizon:
            raise PydanticCustomError(
                "missing_top_horizon",
                f"{location}: 'top_horizon' is required."
                " Specify it either at the formation level "
                "or in the attribute-specific override"
                " (e.g., rms: {{top_horizon: ...}})",
            )

        if self.bottom_horizon is None and self.window_length is None:
            raise PydanticCustomError(
                "missing_bottom_horizon",
                f"{location}: Either 'bottom_horizon' or 'window_length' must be"
                " specified. "
                "Provide 'bottom_horizon' at formation level or in attribute override, "
                "or use 'window_length' to calculate from 'top_horizon'",
            )
        if self.bottom_horizon is not None and self.window_length is not None:
            warnings.warn(
                f"{location}: Both 'bottom_horizon' ('{self.bottom_horizon}') "
                f"and 'window_length' ({self.window_length}) are specified. "
                f"'window_length' will take precedence and 'bottom_horizon'"
                " will be ignored.",
                UserWarning,
                stacklevel=2,
            )

        return self


def _group_attributes_by_interval(
    formation_settings: FormationSettings,
    global_config: GlobalConfig,
    formation_name: str,
    cube_name: str,
) -> dict[IntervalConfig, list[KnownAttributes]]:
    """Group attributes that share the same interval configuration.

    Each attribute (e.g., 'rms', 'mean', 'min') can override the formation's default
    interval settings. Attributes that end up with identical settings are grouped
    together.
    """

    interval_groups = defaultdict(list)
    for attribute in global_config.attributes:
        interval_key = formation_settings.build_interval_config(
            attribute,
            global_config.scale_factor,
            formation_name,
            cube_name,
        )
        interval_groups[interval_key].append(attribute)
    return dict(interval_groups)


def _load_surface(
    surface_name: str,
    surfaces: dict[str, xtgeo.RegularSurface],
    horizon_postfix: str,
    gridhorizon_path: Path,
) -> xtgeo.RegularSurface:
    """
    Load a surface from either the surfaces dictionary or from file.
    """

    surface_key = surface_name + horizon_postfix
    if surface_key in surfaces:
        surface = surfaces[surface_key]
        surface.name = surface_name
        return surface
    try:
        surface = xtgeo.surface_from_file(f"{gridhorizon_path}/{surface_key}")
        surface.name = surface_name
        # This will cache the surface for later
        surfaces[surface_key] = surface
        return surface
    except FileNotFoundError:
        raise ValueError(f"Surface file not found: {gridhorizon_path / surface_key}")


def _create_seismic_attribute(
    interval_config: IntervalConfig,
    attributes: list[KnownAttributes],
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
    cube_info: CubeConfig,
    cube: SeismicCube,
) -> SeismicAttribute:
    """Create a single SeismicAttribute object for a given interval configuration."""
    # Pydantic validation in IntervalConfig ensures top_horizon is always set
    top_horizon = cast(str, interval_config.top_horizon)
    attr_top_surface = _load_surface(
        surface_name=top_horizon,
        surfaces=surfaces,
        horizon_postfix=global_config.surface_postfix,
        gridhorizon_path=global_config.gridhorizon_path,
    )
    if interval_config.window_length is not None:
        # Calculated in post init of SeismicAttribute
        attr_bottom_surface = None
    else:
        # Pydantic validation in IntervalConfig ensures bottom_horizon is always set
        bottom_horizon = cast(str, interval_config.bottom_horizon)
        attr_bottom_surface = _load_surface(
            surface_name=bottom_horizon,
            surfaces=surfaces,
            horizon_postfix=global_config.surface_postfix,
            gridhorizon_path=global_config.gridhorizon_path,
        )

    return SeismicAttribute(
        top_surface=attr_top_surface,
        calc_types=attributes,
        scale_factor=interval_config.scale_factor,
        from_cube=cube,
        window_length=interval_config.window_length,
        bottom_surface=attr_bottom_surface,
        top_surface_shift=interval_config.top_surface_shift,
        bottom_surface_shift=interval_config.bottom_surface_shift,
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
    cube_name: str,
    formation_name: str,
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
        formation_name=formation_name,
        cube_name=cube_name,
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
    for cube_name, cube_info in root_config.cubes.items():
        for formation_name, formation_settings in cube_info.formations.items():
            formation_attributes = _process_formation(
                cube_name=cube_name,
                formation_name=formation_name,
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
