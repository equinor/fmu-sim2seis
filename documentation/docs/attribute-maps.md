# Attribute Maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. The definition of intervals
for estimating attribute maps is controlled by a separate YAML file.

## Config YAML File Section

Default values typically apply for attribute map generation in the `sim2seis` configuration file, as most information is
derived from the dedicated interval definition file. [Figure 1](#figure-1-seismic-attributes-in-yaml) shows the relevant
sections of the configuration file. `webviz_map` refers to export of attribute maps in formats that can be read by
`webviz` and `ert` for visualisation and history matching. As most parameters are commented out, this indicates that
the default settings in most cases are used. It is only the name of the attribute definition file in the
`main class setting` that must be specified. The settings for the observation error are given in the
[interval definition file](#error-settings) and apply to [observed data](./observed-data.md) only.

The snippets below from the config YAML file show some of the parameters which are related to attribute maps

```yaml
# # Section for ert and webviz export
#______________________________________________________________________________________________________________________#
webviz_map:
  # grid_file: simgrid_maps4ahm.roff
  # zone_file: simgrid_maps4ahm--zone.roff
  # region_file: simgrid_maps4ahm--region.roff


## Section for seismic forward amplitude maps
#______________________________________________________________________________________________________________________#
# amplitude_map:
#  attribute: amplitude


## Section for seismic inversion relai maps
#______________________________________________________________________________________________________________________#
# inversion_map:
#  attribute: relai
#


## From the main class
#______________________________________________________________________________________________________________________#
attribute_map_definition_file: data_intervals_drogon.yml


## From path definitions:
# paths:
#   webviz_map_dir: sim2seis/input/attribute_maps
```

<span id="figure-1-seismic-attributes-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to attribute maps.</span>

The most important setting is the file name for the interval definition file. This is specified in the main part of the
configuration YAML file.

## Interval Definition YAML File

The interval definition file provides flexibility in defining intervals, which may result in a complex structure.
[Figure 2](#figure-2-interval-definition-in-yaml) illustrates the structure of the interval definition YAML file.
The file can also be created or checked with the [interval definition form](./interval-definition.md), which is
generated from the same validation rules as described below.

### Global Section

The `global` section defines parameters that apply to all interval definitions unless overridden later:

- Horizon path: Directory for horizons that are not provided by the depth conversion. Controlled by `fmu-dataio`, default value shown.
- Attributes: Select attributes to highlight important features in the 4D seismic. Only attributes listed here may be
  adjusted per attribute within a window.
- Scale factor: Applied to **modelled** attributes only, to match their level to the observed seismic attributes. Observed-data attributes define the reference level and are never scaled.
- Surface suffix: File-name suffix appended to each horizon name when reading the surface files (e.g. `--depth.gri`).
- Error settings: `error` and `error_path` define the observation error, see [Error settings](#error-settings).

Unknown keys are rejected at every level of the file, so obsolete settings from older versions (e.g. the former
metadata fields, now handled by `fmu-dataio`) must be removed.

### Error settings

The observation error is written as an `OBS_ERROR` column in the exported CSV or parquet files and applies to
[observed data](./observed-data.md) only. It is defined by an `error` block with the following fields:

- `type`: `relative` (a fraction of the attribute value) or `absolute` (the error itself).
- `value`: a single scalar error, or
- `error_surface`: the name of a spatially varying error map, resolved against the global `error_path`. The file is
  read with `xtgeo` and must have the same geometry as the attribute maps. Exactly one of `value` or `error_surface`
  must be given.
- `minimum`: an absolute floor applied after the error is computed (default `0.0`).

All four combinations of `type` and source (scalar `value` or `error_surface`) are supported. The `error_path`
directory is set once, in the `global` section only.

The `error` block can be given at the `global`, cube, or window level. A block at a more specific level fully
replaces the one at the level above it (whole-block replacement); individual fields are not merged. For example:

```yaml
global:
  gridhorizon_path: share/results/maps # path for horizons not provided by the depth conversion
  attributes: # attributes to be made for each cube; only these can be adjusted per window
    - rms
    - mean
    - min
  scale_factor: 1.02
  surface_postfix: --depth.gri # appended to horizon names when reading surface files
  error_path: share/results/maps # directory for error surface files (global only)
  error: # observation error for observed-data attribute maps (observed data only)
    type: relative # 'relative' (fraction of attribute) or 'absolute'
    value: 0.07 # single scalar; use 'error_surface' instead for a spatially varying error
    minimum: 0.005 # absolute floor applied after the error is computed
cubes: # Setup for the cubes for which maps will be generated
  relai_depth: # arbitrary name of cube
    cube_prefix: seismic--relai_full_depth-- # exact date-independent cube name
    # A cube- or window-level 'error' block fully replaces the global one, e.g.:
    # error:
    #   type: absolute
    #   error_surface: relai_error.gri # resolved against global 'error_path'
    #   minimum: 0.005
    windows: # settings for each window maps will be generated for
      volantis:
        top_horizon: topvolantis # Horizon used as top of the window; name as given by the depth conversion
        bottom_horizon: basevolantis # Horizon used as base of the window (alternative: window_length)
        top_surface_shift: -5 # Shift of the top surface; negative is upwards
        bottom_surface_shift: 10 # Shift of the bottom surface; positive is downwards
        zone: Valysar # zone and position apply to the whole window and cannot be overridden
        position: top
        rms: # Special requirements for 'rms' attribute (must be listed under global attributes)
          top_horizon: topvolantis
          bottom_horizon: basevolantis
          top_surface_shift: -15
          scale_factor: 1.05
  amplitude_depth: # arbitrary name of cube
    cube_prefix: seismic--amplitude_full_depth-- # exact date-independent cube name
    windows: # settings for each window maps will be generated for
      volantis:
        top_horizon: topvolantis
        bottom_horizon: basevolantis
        top_surface_shift: -17
        bottom_surface_shift: -2
        zone: Valysar
        position: top
        mean: # Special requirements for 'mean' attribute
          top_horizon: topvolantis
          bottom_horizon: basevolantis
          top_surface_shift: -10
          bottom_surface_shift: -5
        min:
          scale_factor: 2.0
```

<span id="figure-2-interval-definition-in-yaml"><strong>Figure 2:</strong> Parameters to define intervals for attribute map estimation.</span>

### Cube Section

- Cube names: Arbitrary values.
- `cube_prefix`: The date-independent cube name, following the pattern
  `seismic--<amplitude|relai>_[<full|near|mid|far>_]<time|depth>`, optionally followed by `--` (e.g.
  `seismic--relai_full_depth--` or `seismic--amplitude_near_time`). The pattern is checked when the file is read.
  The value is compared for exact equality with each available cube name
  after its date component has been stripped; the stack must match as well. Seismic dates are resolved separately,
  when the cubes are imported and differenced.
- `error`: Optional observation-error block that overrides the global one for all windows of this cube (observed data only); see [Error settings](#error-settings).

### Windows Section

Several windows can be defined under each cube. Each window must define its interval, which applies to all attribute
calculations listed in the `global` section unless adjusted per attribute. Intervals can be defined in two ways:

1. **Top and Base Horizon**: Specify the top and base horizons, with optional shifts for each.
2. **Top Horizon and Window Length**: Specify the top horizon and the window length, with an optional shift of the
   top horizon. If both `bottom_horizon` and `window_length` are given, `window_length` takes precedence and a warning
   is issued.

`top_horizon` is always required, and one of `bottom_horizon` or `window_length` (which must be positive) must be
given. Keys must not be left empty (`null`) anywhere in the file; omit a key to use its default. Horizon names are those produced by the depth conversion; any other horizon is read from `gridhorizon_path` as
`<name><surface_postfix>`. Surface shifts are signed: negative values move a surface upwards (shallower), positive
values downwards.

In addition, each window controls which grid cells the attribute is sampled from. These cells are then aggregated
per region (from the Webviz grid and region definition files) when the ERT and Webviz attribute tables are written:

- `zone`: name of the grid zone to sample within. Default is empty (`""`), which uses the full grid interval.
- `position`: vertical sampling position within that zone, one of `top`, `center`, or `base`. Default is `center`.

### Attribute overrides

A window may contain one block per attribute, named after the attribute (`rms:`, `mean:`, …), that adjusts the
interval for that attribute only. The attribute must be listed under `global.attributes`; an override for any other
attribute is an error. An override may set `top_horizon`, `bottom_horizon`, `top_surface_shift`,
`bottom_surface_shift`, `window_length` and `scale_factor`. `zone`, `position` and `error` apply to the whole window
(or cube) and cannot be overridden per attribute. Attributes that end up with identical interval settings are
calculated together.

The base of the interval is replaced as a unit. When an override sets `bottom_horizon` or `window_length`, neither
value is inherited from the window, so an override can use a base horizon even when the window uses `window_length`,
and vice versa. If an override sets both, `window_length` takes precedence as for windows.

### Example in Figure 2 explained

This is how the example in [Figure 2](#figure-2-interval-definition-in-yaml) should be interpreted:

- From `global` settings
  - three attributes are selected (rms, mean, min)
  - modelled attributes are scaled by a factor of 1.02 to match observed seismic attributes
  - the error for observed data is of type **relative** with a constant scalar of 0.07 and an absolute minimum of 0.005
- For `relai_depth` cubes:
  - a single window is selected, named `volantis`
  - the gridding is set to the zone `Valysar`, with the coordinates from the top layer
  - `min` and `mean` attributes are calculated from `Top Volantis` shifted 5 m up, to `Base Volantis` shifted 10 m down.
  - `rms` attribute is calculated from `Top Volantis` shifted 15 m up, to `Base Volantis` shifted 10 m down (the base
    shift is inherited from the window). The standard scaling factor for `rms` attribute is modified to 1.05
- For `amplitude_depth` cubes:
  - a single window is selected, named `volantis`
  - the attributes are calculated from `Top Volantis` with a shift upwards of 17 m, to `Base Volantis` with a shift upwards of 2 m
  - the gridding is set to the zone `Valysar`, with the coordinates from the top layer
  - `mean` attribute has a separate interval definition from `rms` and `min` with modified surface shifts
  - `min` has a different scaling factor than `rms` and `mean`
