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

### Global Section

The `global` section defines parameters that apply to all interval definitions unless overridden later:

- Horizon path: Controlled by `fmu-dataio`, default value shown.
- Attributes: Select attributes to highlight important features in the 4D seismic.
- Scale factor: Applied to **modelled** attributes only, to match their level to the observed seismic attributes.
  Observed-data attributes define the reference level and are never scaled, so the factor cancels in any
  modelled-versus-observed comparison unless it is applied to the modelled side alone.
- Surface postfix: File-name postfix appended to each horizon name when reading the surface files (e.g. `--depth.gri`).
- Metadata fields: (**Obsolete**) This is removed, as all metadata-related matters are handled by `fmu-dataio`.
- Error settings: `error` and `error_path` define the observation error, see [Error settings](#error-settings).

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

The `error` block can be given at the `global`, cube, or formation level. A block at a more specific level fully
replaces the one at the level above it (whole-block replacement); individual fields are not merged. For example:

```yaml
global:
  gridhorizon_path: share/results/maps # path for input horizons
  attributes: # attributes to be made for each cube
    - rms
    - mean
    - min
  scale_factor: 1.02
  surface_postfix: --depth.gri
  error_path: share/results/maps # directory for error surface files (global only)
  error: # observation error for observed-data attribute maps (observed data only)
    type: relative # 'relative' (fraction of attribute) or 'absolute'
    value: 0.07 # single scalar; use 'error_surface' instead for a spatially varying error
    minimum: 0.005 # absolute floor applied after the error is computed
cubes: # Setup for the cubes for which maps will be generated
  relai_depth: # arbitrary name of cube
    cube_prefix: seismic--relai_full_depth-- # start of observed cube name
    # A cube- or formation-level 'error' block fully replaces the global one, e.g.:
    # error:
    #   type: absolute
    #   error_surface: relai_error.gri # resolved against global 'error_path'
    #   minimum: 0.005
    formations: # settings for each formation maps will be generated for
      volantis:
        top_horizon: topvolantis # Horizon used as top of the formation. ".gri" assumed as extension
        bottom_horizon: basevolantis # Horizon used as base of the formation ".gri" assumed as extension
        top_surface_shift: -5 # Extension of the window upwards from top surface
        bottom_surface_shift: 10 # Extension of the window downwards from bottom surface
        zone: Valysar
        position: top
        rms: # Special requirements for 'rms' attribute
          top_horizon: topvolantis
          bottom_horizon: basevolantis
          top_surface_shift: -15
          scale_factor: 1.05
  amplitude_depth: # arbitrary name of cube
    cube_prefix: seismic--amplitude_full_depth-- # start of cube name
    formations: # settings for each formation maps will be generated for
      volantis:
        top_horizon: topvolantis # Horizon used as top of the formation. ".gri" assumed as extension
        bottom_horizon: basevolantis # Horizon used as base of the formation ".gri" assumed as extension
        top_surface_shift: -17 # Extension of the window upwards from top surface
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
- `cube_prefix`: The leading, date-independent part of the cube name (e.g. `seismic--relai_full_depth--`). It is matched against each available cube name after the date component has been stripped, and thereby selects which cubes maps are generated for. The seismic dates themselves are resolved separately, when the cubes are imported and differenced.
- `error`: Optional observation-error block that overrides the global one for all formations of this cube (observed data only); see [Error settings](#error-settings).

### Formations Section

Several formations can be defined under each cube. Interval settings apply to all attribute calculations listed in the
`global` section unless specific values are set. Intervals can be defined in two ways:

1. **Top and Base Horizon**: Specify the top and base horizons, with optional shifts for each.
2. **Top Horizon and Window Length**: Specify the top horizon and the window length, with an optional shift of the
   top horizon.

In addition, each formation controls which grid cells the attribute is sampled from. These cells are then aggregated
per region (from the Webviz grid and region definition files) when the ERT and Webviz attribute tables are written:

- `zone`: name of the grid zone to sample within. Default is empty (`""`), which uses the full grid interval.
- `position`: vertical sampling position within that zone, one of `top`, `center`, or `base`. Default is `center`.

### Example in Figure 2 explained

This is how the example in [Figure 2](#figure-2-interval-definition-in-yaml) should be interpreted:

- From `global` settings
  - three attributes are selected (rms, mean, min)
  - modelled attributes are scaled by a factor of 1.02 to match observed seismic attributes
  - the error for observed data is of type **relative** with a constant scalar of 0.07 and an absolute minimum of 0.005
- For `relai_depth` cubes:
  - a single formation (or interval) is selected, named `volantis`
  - the gridding is set to the zone `Valysar`, with the coordinates from the top layer
  - `min` and `mean` attributes are calculated from `Top Volantis` shifted 5 m up, to `Base Volantis` shifted 10 ms down.
  - `rms` attribute is calculated from `Top Volantis` shifted 15 m up, to `Base Volantis` shifted 10 m down (the base
    shift is inherited from the formation). The standard scaling factor for `rms` attribute is modified to 1.05
- For `amplitude_depth` cubes:
  - a single formation (or interval) is selected, named `volantis`
  - the attributes are calculated from `Top Volantis` with a shift upwards of 17 m, to `Base Volantis` with a shift upwards of 2 m
  - the gridding is set to the zone `Valysar`, with the coordinates from the top layer
  - `mean` attribute has a separate interval definition from `rms` and `min` with modified surface shifts
  - `min` has a different scaling factor than `rms` and `mean`
