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
    Field,
    ValidationInfo,
    model_validator,
)
from pydantic_core import PydanticCustomError

from .sim2seis_class_definitions import (
    AttributeDef,
    DifferenceSeismic,
    DomainDef,
    ErrorConfig,
    KnownAttributes,
    PositionType,
    ProcessDef,
    SeismicAttribute,
    SeismicName,
    SingleSeismic,
    StackDef,
)
from .sim2seis_config_validation import Sim2SeisPaths

# Type aliases
SeismicCube = SingleSeismic | DifferenceSeismic
SurfaceDict = dict[str, xtgeo.RegularSurface]
CubeDict = dict[SeismicName, SeismicCube]


def _alternatives(literal: Any) -> str:
    return "|".join(get_args(literal))


# Date-independent part of a cube name, see SeismicName.__str__
CUBE_PREFIX_PATTERN = (
    rf"^({_alternatives(ProcessDef)})--({_alternatives(AttributeDef)})_"
    rf"(({_alternatives(StackDef)})_)?({_alternatives(DomainDef)})(--)?$"
)

_HORIZON_NOTE = (
    "Horizon names are those produced by the depth conversion; any other "
    "horizon is read from `gridhorizon_path` as `<name><surface_postfix>`."
)
_SHIFT_NOTE = "Negative values move the surface up (shallower), positive values down."


def _null_paths(data: Any, path: str) -> list[str]:
    """Return the location of every ``None`` value in raw configuration data.

    Nested dicts and lists are searched recursively. Locations are written as
    dotted keys with list indices in brackets, e.g. ``cubes.amp.windows.beta.error``
    or ``global.attributes[0]``, prefixed by ``path`` (empty at the top level).
    """
    if data is None:
        return [path]
    if isinstance(data, dict):
        return [
            null_path
            for key, value in data.items()
            for null_path in _null_paths(value, f"{path}.{key}" if path else str(key))
        ]
    if isinstance(data, list):
        return [
            null_path
            for index, value in enumerate(data)
            for null_path in _null_paths(value, f"{path}[{index}]")
        ]
    return []


class GlobalConfig(BaseModel):
    """Settings that apply to every cube and window unless overridden."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        title="Global settings",
    )

    gridhorizon_path: Path = Field(
        default=Sim2SeisPaths.model_fields["depth_horizon_dir"].default,
        description="Directory with horizon surface files. " + _HORIZON_NOTE,
    )
    attributes: list[KnownAttributes] = Field(
        description="Attributes calculated for every window. Only these attributes "
        "may be adjusted by per-attribute overrides within a window."
    )
    surface_postfix: str = Field(
        default="--depth.gri",
        description="Postfix appended to a horizon name to form the surface file "
        "name, e.g. `--depth.gri`.",
    )
    scale_factor: float = Field(
        default=1.0,
        description="Scaling applied to modelled attributes only, to match their "
        "level to the observed attributes. Observed data is never scaled.",
    )
    error: ErrorConfig | None = Field(
        default=None,
        description="Default observation error for observed-data attribute maps. "
        "A cube- or window-level `error` block replaces this one entirely.",
    )
    error_path: Path | None = Field(
        default=None,
        description="Directory containing `error_surface` files. Required when "
        "any `error_surface` is used.",
    )

    @model_validator(mode="after")
    def validate_directories(self, info: ValidationInfo) -> GlobalConfig:
        if (info.context or {}).get("validate_paths") is False:
            return self
        for field_name, path in (
            ("gridhorizon_path", self.gridhorizon_path),
            ("error_path", self.error_path),
        ):
            if path is not None and not path.is_dir():
                raise ValueError(f"{field_name}: '{path}' is not an existing directory")
        return self


class RootConfig(BaseModel):
    """Interval definitions for attribute map generation."""

    model_config = ConfigDict(frozen=True, extra="forbid", title="Interval definition")

    global_config: GlobalConfig = Field(alias="global")
    cubes: dict[str, CubeConfig] = Field(
        default_factory=dict,
        description="Cubes to generate maps for. Each entry is identified by a "
        "free-text key; choose a descriptive name such as `relai_depth` or "
        "`amplitude_depth`.",
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, data: Any) -> Any:
        if isinstance(data, dict):
            null_paths = _null_paths(data, "")
            if null_paths:
                raise ValueError(
                    "Null values are not allowed in the interval definition; "
                    f"omit the key instead: {', '.join(null_paths)}"
                )
        return data

    @model_validator(mode="after")
    def check_override_attributes(self) -> RootConfig:
        """Reject overrides for attributes that are not calculated."""
        allowed = set(self.global_config.attributes)
        for cube_name, cube in self.cubes.items():
            for window_name, window in cube.windows.items():
                unknown = [a for a in window.attribute_overrides if a not in allowed]
                if unknown:
                    raise ValueError(
                        f"In cube '{cube_name}', window '{window_name}': override "
                        f"given for {unknown}, but only "
                        f"{sorted(allowed)} are listed under 'global.attributes'."
                    )
        return self

    @model_validator(mode="after")
    def resolve_error_surfaces(self) -> RootConfig:
        """Validate and resolve every ``error_surface`` in the configuration.

        Error blocks may appear at the global, cube, and window level. Any
        ``error_surface`` name is resolved against the single global
        ``error_path`` and its existence is verified. The resolved absolute
        path is stored back on the error block so consumers do not need the
        directory.
        """
        error_blocks = [self.global_config.error]
        for cube in self.cubes.values():
            error_blocks.append(cube.error)
            error_blocks.extend(window.error for window in cube.windows.values())

        surface_errors = [
            error
            for error in error_blocks
            if error is not None and error.error_surface is not None
        ]
        if not surface_errors:
            return self

        if self.global_config.error_path is None:
            raise ValueError(
                "An 'error_surface' is configured but 'error_path' is not set "
                "in the global section of the interval definition file."
            )

        for error in surface_errors:
            full_path = (self.global_config.error_path / error.error_surface).resolve()
            if not full_path.is_file():
                raise ValueError(f"Error surface file not found: {full_path}")
            # ErrorConfig is frozen; normalise the field to the absolute path.
            object.__setattr__(error, "error_surface", full_path)
        return self


class AttributeOverride(BaseModel):
    """Adjustments of the window interval for a single attribute.

    The key of this entry is the attribute name, e.g. `rms`, and must be one
    of the attributes listed under `global.attributes`. Only the fields given
    here replace the window settings; `zone`, `position` and `error` are
    window-level and cannot be overridden.

    The base of the interval is replaced as a unit: when `bottom_horizon` or
    `window_length` is given here, neither is inherited from the window. If
    both are given here, `window_length` takes precedence.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        title="Attribute override",
    )

    top_horizon: str | None = Field(
        default=None,
        min_length=1,
        pattern=r"\S",
        description="Replaces the window `top_horizon`.",
    )
    bottom_horizon: str | None = Field(
        default=None,
        min_length=1,
        pattern=r"\S",
        description="Base horizon for this attribute. When given, the window "
        "`bottom_horizon` and `window_length` are not inherited.",
    )
    top_surface_shift: float | None = Field(
        default=None,
        description="Replaces the window `top_surface_shift`. " + _SHIFT_NOTE,
    )
    bottom_surface_shift: float | None = Field(
        default=None,
        description="Replaces the window `bottom_surface_shift`. " + _SHIFT_NOTE,
    )
    window_length: float | None = Field(
        default=None,
        gt=0,
        description="Window length for this attribute. When given, the window "
        "`bottom_horizon` and `window_length` are not inherited; takes "
        "precedence over a `bottom_horizon` in the same override.",
    )
    scale_factor: float | None = Field(
        default=None,
        description="Replaces the global `scale_factor` for this attribute. "
        "Modelled data only.",
    )

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, data: Any) -> Any:
        if isinstance(data, dict):
            null_keys = [key for key, value in data.items() if value is None]
            if null_keys:
                raise ValueError(
                    f"{null_keys} must not be null; omit the key to inherit the "
                    "window value."
                )
        return data


class WindowSettings(BaseModel):
    """Interval definition for one window.

    The key of this entry is a free-text name that is also used as the name
    of the exported attribute maps, e.g. `volantis`.

    Besides the fields below, a window may contain one block per attribute
    listed in `global.attributes` (e.g. `rms: {top_surface_shift: -15}`) that
    adjusts the interval for that attribute only.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        title="Window",
    )

    top_horizon: str = Field(
        min_length=1,
        pattern=r"\S",
        description="Horizon defining the top of the window. " + _HORIZON_NOTE,
    )
    bottom_horizon: str | None = Field(
        default=None,
        min_length=1,
        pattern=r"\S",
        description="Horizon defining the base of the window. Either this or "
        "`window_length` must be given; `window_length` takes precedence.",
    )
    top_surface_shift: float = Field(
        default=0,
        description="Shift of the top surface in depth units. " + _SHIFT_NOTE,
    )
    bottom_surface_shift: float = Field(
        default=0,
        description="Shift of the bottom surface in depth units. Ignored when "
        "`window_length` is used. " + _SHIFT_NOTE,
    )
    window_length: float | None = Field(
        default=None,
        gt=0,
        description="Window thickness measured from the shifted top surface. "
        "Alternative to `bottom_horizon`; takes precedence when both are given, "
        "and `bottom_horizon` is then ignored.",
    )
    error: ErrorConfig | None = Field(
        default=None,
        description="Observation error for this window (observed data only). "
        "Replaces the cube- or global-level block entirely.",
    )
    zone: str = Field(
        default="",
        description="Grid zone to sample attribute values within. Empty means the "
        "full grid interval.",
    )
    position: PositionType = Field(
        default="center",
        description="Vertical sampling position within the zone.",
    )

    attribute_overrides: dict[KnownAttributes, AttributeOverride] = Field(
        default_factory=dict, exclude=True
    )

    @model_validator(mode="before")
    @classmethod
    def extract_attributes(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "attribute_overrides" in data:
            raise ValueError(
                "'attribute_overrides' is internal; specify overrides using "
                "attribute names directly, e.g. 'rms'."
            )
        attribute_overrides = {}
        for attr in get_args(KnownAttributes):
            if attr in data:
                attribute_overrides[attr] = data.pop(attr)

        data["attribute_overrides"] = attribute_overrides
        return data

    @model_validator(mode="after")
    def require_base(self) -> WindowSettings:
        if self.bottom_horizon is None and self.window_length is None:
            raise ValueError(
                "Either 'bottom_horizon' or 'window_length' must be specified."
            )
        return self

    def build_interval_config(
        self,
        attribute: KnownAttributes,
        global_scale_factor: float,
        window_name: str,
        cube_name: str,
    ) -> IntervalConfig:
        config_dict: dict[str, Any] = {
            "top_horizon": self.top_horizon,
            "bottom_horizon": self.bottom_horizon,
            "top_surface_shift": self.top_surface_shift,
            "bottom_surface_shift": self.bottom_surface_shift,
            "window_length": self.window_length,
            "scale_factor": global_scale_factor,
            "zone": self.zone,
            "position": self.position,
        }

        override = self.attribute_overrides.get(attribute)
        if override is not None:
            values = override.model_dump(exclude_unset=True)
            if values.keys() & {"bottom_horizon", "window_length"}:
                config_dict["bottom_horizon"] = None
                config_dict["window_length"] = None
            config_dict.update(values)

        return IntervalConfig.model_validate(
            config_dict,
            context={
                "cube_name": cube_name,
                "window_name": window_name,
                "attribute": attribute,
            },
        )


class CubeConfig(BaseModel):
    """Windows and settings for all cubes matching `cube_prefix`.

    The key of this entry is a free-text label used only to identify the
    cube set in messages; pick a descriptive name, e.g. `relai_depth`.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        title="Cube",
    )

    cube_prefix: str = Field(
        pattern=CUBE_PREFIX_PATTERN,
        description="Date-independent cube name in the format "
        "`seismic--<amplitude|relai>_[<full|near|mid|far>_]<time|depth>`, "
        "optionally followed by `--` (e.g. `seismic--relai_full_depth--` or "
        "`seismic--amplitude_near_time`). The cube name without its date must "
        "match this value exactly.",
    )
    error: ErrorConfig | None = Field(
        default=None,
        description="Observation error for all windows of this cube (observed "
        "data only). Replaces the global block entirely.",
    )
    windows: dict[str, WindowSettings] = Field(
        description="Windows to generate maps for. Each entry is identified by a "
        "free-text key that also becomes the name of the exported maps; use a "
        "descriptive name such as the reservoir zone, e.g. `volantis`."
    )


class IntervalConfig(BaseModel):
    """Resolved interval for one attribute group.

    Two attributes share an interval (and hence a SeismicAttribute) when all
    fields below are equal. `zone` and `position` always come from the window;
    the remaining fields may be adjusted per attribute.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    top_horizon: str = Field(min_length=1, pattern=r"\S")
    bottom_horizon: str | None = Field(default=None, min_length=1, pattern=r"\S")

    top_surface_shift: float
    bottom_surface_shift: float
    window_length: float | None = None
    scale_factor: float
    zone: str
    position: PositionType

    @model_validator(mode="after")
    def validate_horizon_requirements(self, info: ValidationInfo) -> IntervalConfig:
        ctx = info.context or {}
        cube_name = ctx.get("cube_name", "unknown")
        window_name = ctx.get("window_name", "unknown")
        attribute = ctx.get("attribute", "unknown")

        location = (
            f"In cube '{cube_name}', window '{window_name}', attribute '{attribute}'"
        )

        if self.bottom_horizon is None and self.window_length is None:
            raise PydanticCustomError(
                "missing_bottom_horizon",
                f"{location}: Either 'bottom_horizon' or 'window_length' must be"
                " specified. "
                "Provide 'bottom_horizon' at window level or in attribute override, "
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
    window_settings: WindowSettings,
    global_config: GlobalConfig,
    window_name: str,
    cube_name: str,
) -> dict[IntervalConfig, list[KnownAttributes]]:
    """Group attributes that share the same interval configuration.

    Each attribute (e.g., 'rms', 'mean', 'min') can override the window's default
    interval settings. Attributes that end up with identical settings are grouped
    together.
    """

    interval_groups = defaultdict(list)
    for attribute in global_config.attributes:
        interval_key = window_settings.build_interval_config(
            attribute,
            global_config.scale_factor,
            window_name,
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
    window_name: str,
    error: ErrorConfig | None = None,
    is_observed: bool = False,
) -> SeismicAttribute:
    """Create a single SeismicAttribute object for a given interval configuration."""
    attr_top_surface = _load_surface(
        surface_name=interval_config.top_horizon,
        surfaces=surfaces,
        horizon_postfix=global_config.surface_postfix,
        gridhorizon_path=global_config.gridhorizon_path,
    )
    if interval_config.window_length is not None:
        # Calculated in post init of SeismicAttribute
        attr_bottom_surface = None
    else:
        # Without window_length, IntervalConfig requires bottom_horizon.
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
        # Observed data defines the reference level and must not be scaled; only
        # modelled attributes are scaled to match it.
        scale_factor=1.0 if is_observed else interval_config.scale_factor,
        from_cube=cube,
        window_length=interval_config.window_length,
        bottom_surface=attr_bottom_surface,
        top_surface_shift=interval_config.top_surface_shift,
        bottom_surface_shift=interval_config.bottom_surface_shift,
        window=window_name,
        info=cube_info,
        error=error,
        zone=interval_config.zone,
        position=interval_config.position,
    )


def _get_matching_cubes(cubes: CubeDict, cube_prefix: str) -> list[SeismicCube]:
    """Find all seismic cubes whose names match the given prefix."""
    return [
        cube
        for cube_name, cube in cubes.items()
        if cube_name.compare_without_date(cube_prefix)
    ]


def _create_window_attributes(
    interval_groups: dict[IntervalConfig, list[KnownAttributes]],
    cube_info: CubeConfig,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
    window_name: str,
    error: ErrorConfig | None = None,
    is_observed: bool = False,
) -> list[SeismicAttribute]:
    """Create SeismicAttribute objects for each interval group and matching cube."""
    window_attributes = []
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
                window_name=window_name,
                error=error,
                is_observed=is_observed,
            )
            window_attributes.append(attribute)
    return window_attributes


def _resolve_error_block(
    global_config: GlobalConfig,
    cube_info: CubeConfig,
    window_settings: WindowSettings,
) -> ErrorConfig | None:
    """Select the observation error for a window.

    The most specific error block wins (whole-block replacement): window
    overrides cube, which overrides the global setting. ``error_surface`` paths
    have already been validated and resolved to absolute paths by
    ``RootConfig.resolve_error_surfaces``.
    """
    return window_settings.error or cube_info.error or global_config.error


def _process_window(
    cube_name: str,
    window_name: str,
    window_settings: WindowSettings,
    cube_info: CubeConfig,
    cubes: CubeDict,
    surfaces: SurfaceDict,
    global_config: GlobalConfig,
    is_observed: bool = False,
) -> list[SeismicAttribute]:
    """Process a single window and create its SeismicAttribute objects."""

    interval_groups = _group_attributes_by_interval(
        window_settings=window_settings,
        global_config=global_config,
        window_name=window_name,
        cube_name=cube_name,
    )
    error = _resolve_error_block(global_config, cube_info, window_settings)
    return _create_window_attributes(
        interval_groups=interval_groups,
        cube_info=cube_info,
        cubes=cubes,
        surfaces=surfaces,
        global_config=global_config,
        window_name=window_name,
        error=error,
        is_observed=is_observed,
    )


def populate_seismic_attributes(
    config: dict[str, Any],
    cubes: CubeDict,
    surfaces: SurfaceDict,
    is_observed: bool = False,
) -> list[SeismicAttribute]:
    """Create SeismicAttribute objects for each unique interval configuration.

    Args:
        config: Configuration dictionary containing global settings,
            cube name prefixes and window definition for each attribute
        cubes: Available seismic cubes indexed by their SeismicName
        surfaces: Available surfaces indexed by their names
        is_observed: When True the attributes are for observed data, which
            defines the reference level and is therefore left unscaled;
            ``scale_factor`` is applied to modelled attributes only.

    Returns:
        List of SeismicAttribute objects, one for each unique interval configuration

    Raises:
        ValueError: If no attributes could be generated (likely due to configuration
        mismatch)
    """
    root_config = RootConfig(**config)
    seismic_attributes = []
    for cube_name, cube_info in root_config.cubes.items():
        for window_name, window_settings in cube_info.windows.items():
            window_attributes = _process_window(
                cube_name=cube_name,
                window_name=window_name,
                window_settings=window_settings,
                cube_info=cube_info,
                cubes=cubes,
                surfaces=surfaces,
                global_config=root_config.global_config,
                is_observed=is_observed,
            )
            seismic_attributes.extend(window_attributes)

    if not seismic_attributes:
        raise ValueError(
            "No attributes generated. Please check configuration settings."
        )

    return seismic_attributes
