"""
Parse yaml file with interval definitions and populate SeismicAttribute objects
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import xtgeo

from .sim2seis_class_definitions import (
    DifferenceSeismic,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
)

# Type aliases
SeismicCube = SingleSeismic | DifferenceSeismic
SurfaceDict = dict[str, xtgeo.RegularSurface]
CubeDict = dict[SeismicName, SeismicCube]


@dataclass(frozen=True)
class GlobalConfig:
    """Global configuration settings for seismic attribute generation.

    Args:
        gridhorizon_path: Path to directory containing surface files
        attributes: List of attribute types to calculate (e.g., ['rms', 'mean'])
        surface_postfix: Postfix to append to surface names
        scale_factor: Global scaling factor applied to all values
    """

    gridhorizon_path: str
    attributes: list[str]
    surface_postfix: str
    scale_factor: float

    @classmethod
    def from_dict(cls, config: dict) -> "GlobalConfig":
        """Create GlobalConfig from configuration dictionary."""
        return cls(
            gridhorizon_path=config["gridhorizon_path"],
            attributes=config["attributes"],
            surface_postfix=config["surface_postfix"],
            scale_factor=config["scale_factor"],
        )


@dataclass(frozen=True)
class IntervalConfig:
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

    top_horizon: str
    bottom_horizon: str
    top_surface_shift: float
    base_surface_shift: float
    window_length: Optional[float]
    scale_factor: float


@dataclass(frozen=True)
class FormationSettings:
    """Settings for a formation, including horizons, shifts, and attributes."""

    top_horizon: str
    bottom_horizon: str
    top_surface_shift: float
    base_surface_shift: float
    window_length: Optional[float]
    attributes: list[str]


def _create_interval_key(
    top_horizon: str,
    bottom_horizon: str,
    top_surface_shift: float,
    base_surface_shift: float,
    window_length: float | None,
    scale_factor: float,
) -> IntervalConfig:
    """Create an IntervalConfig that uniquely identifies an interval configuration."""
    return IntervalConfig(
        top_horizon=top_horizon,
        bottom_horizon=bottom_horizon,
        top_surface_shift=top_surface_shift,
        base_surface_shift=base_surface_shift,
        window_length=window_length,
        scale_factor=scale_factor,
    )


def _get_attribute_interval_settings(
    attribute: str,
    formation_info: dict,
    defaults: dict,
) -> IntervalConfig:
    """Get interval settings for a specific attribute, falling back to defaults if not
    specified.
    """
    # Get attribute-specific overrides, empty dict if none exist
    attr_overrides = formation_info.get(attribute, {})

    # For each setting, use attribute override if it exists, otherwise use formation
    # default
    return _create_interval_key(
        top_horizon=attr_overrides.get("top_horizon", defaults["top_horizon"]),
        bottom_horizon=attr_overrides.get("bottom_horizon", defaults["bottom_horizon"]),
        top_surface_shift=attr_overrides.get(
            "top_surface_shift", defaults["top_surface_shift"]
        ),
        base_surface_shift=attr_overrides.get(
            "base_surface_shift", defaults["base_surface_shift"]
        ),
        window_length=attr_overrides.get("window_length", defaults["window_length"]),
        scale_factor=attr_overrides.get("scale_factor", defaults["scale_factor"]),
    )


def _group_attributes_by_interval(
    attributes: list[str],
    formation_info: dict,
    top_horizon: str,
    bottom_horizon: str,
    top_surface_shift: float,
    base_surface_shift: float,
    window_length: Optional[float],
    global_config: GlobalConfig,
) -> dict[IntervalConfig, list[str]]:
    """Group attributes that share the same interval configuration.

    Each attribute (e.g., 'rms', 'mean', 'min') can override the formation's default
    interval settings. Attributes that end up with identical settings are grouped
    together.
    """
    defaults = {
        "top_horizon": top_horizon,
        "bottom_horizon": bottom_horizon,
        "top_surface_shift": top_surface_shift,
        "base_surface_shift": base_surface_shift,
        "window_length": window_length,
        "scale_factor": global_config.scale_factor,
    }

    interval_groups = defaultdict(list)
    for attribute in attributes:
        interval_key = _get_attribute_interval_settings(
            attribute, formation_info, defaults
        )
        interval_groups[interval_key].append(attribute)

    return dict(interval_groups)


def _load_surface(
    surface_name: str,
    surfaces: dict[str, xtgeo.RegularSurface],
    horizon_postfix: str,
    gridhorizon_path: str,
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
    attributes: list[str],
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
    cube_info: dict,
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
        domain=cube_info["vertical_domain"],
        window_length=interval_config.window_length,
        base_surface=attr_bottom_surface,
        top_surface_shift=interval_config.top_surface_shift,
        base_surface_shift=interval_config.base_surface_shift,
        info=cube_info,
    )


def _get_formation_settings(
    formation_info: dict, global_config: GlobalConfig
) -> FormationSettings:
    """Extract formation settings with fallbacks to global defaults."""
    return FormationSettings(
        top_horizon=formation_info.get("top_horizon", global_config.gridhorizon_path),
        bottom_horizon=formation_info.get(
            "bottom_horizon", global_config.gridhorizon_path
        ),
        top_surface_shift=formation_info.get("top_surface_shift", 0),
        base_surface_shift=formation_info.get("base_surface_shift", 0),
        window_length=formation_info.get("window_length"),
        attributes=formation_info.get("attributes", global_config.attributes),
    )


def _get_matching_cubes(cubes: CubeDict, cube_prefix: str) -> list[SeismicCube]:
    """Find all seismic cubes whose names match the given prefix."""
    return [
        cube
        for cube_name, cube in cubes.items()
        if cube_name.compare_without_date(cube_prefix)
    ]


def _create_formation_attributes(
    interval_groups: dict[IntervalConfig, list[str]],
    cube_info: dict,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
) -> list[SeismicAttribute]:
    """Create SeismicAttribute objects for each interval group and matching cube."""
    formation_attributes = []
    for interval_config, attrs in interval_groups.items():
        matching_cubes = _get_matching_cubes(cubes, cube_info["cube_prefix"])
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
    formation_info: dict,
    cube_info: dict,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
) -> list[SeismicAttribute]:
    """Process a single formation and create its SeismicAttribute objects."""
    settings = _get_formation_settings(formation_info, global_config)

    interval_groups = _group_attributes_by_interval(
        attributes=settings.attributes,
        formation_info=formation_info,
        top_horizon=settings.top_horizon,
        bottom_horizon=settings.bottom_horizon,
        top_surface_shift=settings.top_surface_shift,
        base_surface_shift=settings.base_surface_shift,
        window_length=settings.window_length,
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
    config: dict,
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
    global_config = GlobalConfig.from_dict(config["global"])
    seismic_attributes = []

    for cube_info in config["cubes"].values():
        for formation_info in cube_info["formations"].values():
            formation_attributes = _process_formation(
                formation_info=formation_info,
                cube_info=cube_info,
                cubes=cubes,
                surfaces=surfaces,
                global_config=global_config,
            )
            seismic_attributes.extend(formation_attributes)

    if not seismic_attributes:
        raise ValueError(
            "No attributes generated. Please check configuration settings."
        )

    return seismic_attributes
