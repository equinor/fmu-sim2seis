# Attribute Maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. The definition of intervals
for estimating attribute maps is controlled by a separate YAML file.

## YAML File Section

Default values typically apply for attribute map generation in the `sim2seis` configuration file, as most information is
derived from the dedicated interval definition file. [Figure 1](#figure-1-seismic-attributes-in-yaml) shows the relevant
sections of the configuration file. `webviz_map` refers to export of attribute maps in formats that can be read by
`webviz` and `ert` for visualisation and history matching. As most parameters are commented out, this indicates that
the default settings in most cases are used. It is only the name of the attribute definition file in the
`main class setting` that must be specified. The settings for attribute error are used for [observed data](./observed-data.md).

```yaml
# # Section for ert and webviz export
#______________________________________________________________________________________________________________________#
webviz_map:
  # grid_file: simgrid_maps4ahm.roff
  # zone_file: simgrid_maps4ahm--zone.roff
  # region_file: simgrid_maps4ahm--region.roff
  attribute_error: 0.07
  attribute_error_minimum: 0.005


## Section for seismic forward amplitude maps
#______________________________________________________________________________________________________________________#
# amplitude_map:
#  attribute: *seismic_attribute
#  pickle_file_prefix: amplitude_maps


## Section for seismic inversion relai maps
#______________________________________________________________________________________________________________________#
# inversion_map:
#  attribute: *inversion_attribute
#  pickle_file_prefix: relai_maps
#


## From the main class
#______________________________________________________________________________________________________________________#
attribute_map_definition_file: modelled_data_intervals_drogon.yml


## From path definitions:
# paths:
#   webviz_map_dir: sim2seis/input/attribute_maps
```

<span id="figure-1-seismic-attributes-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to attribute maps.</span>

In addition, the file name for the interval definition file is specified in the main part of the configuration YAML  
file:

```yaml
attribute_map_definition_file: modelled_data_intervals_drogon.yml
```

## Interval Definition YAML File

The interval definition file provides flexibility in defining intervals, resulting in a complex structure.
[Figure 2](#figure-2-interval-definition-in-yaml) illustrates the structure of the interval definition YAML file.

<<< ../../tests/data/sim2seis/model/modelled_data_intervals_drogon.yml{yml}
<span id="figure-2-interval-definition-in-yaml"><strong>Figure 2:</strong> Parameters to define intervals for attribute map estimation.</span>

### Global Section

The `global` section defines parameters that apply to all interval definitions unless overridden later:

- Horizon path: Controlled by `fmu-dataio`, default value shown.
- Attributes: Select attributes to highlight important features in the 4D seismic.
- Scale factor: Used to match values in similar attributes from observed seismic data.
- Metadata fields: Used in `fmu-dataio`.

### Cube Section

- Cube names: Arbitrary values.
- Cube prefix: Concatenated with seismic difference dates defined in the global config file.
- Seismic path: Controlled by `fmu-dataio`, default value shown.
- Vertical domain: Default is `depth`.

### Formations Section

Several formations can be defined under each cube. Interval settings apply to all attribute calculations listed in the
`global` section unless specific values are set. Intervals can be defined in two ways:

1. **Top and Base Horizon**: Specify the top and base horizons, with optional shifts for each.
2. **Top Horizon and Interval Length**: Specify the top horizon and the interval length, with an optional shift of the
   top horizon.

For example:

- For `relai_depth` cubes:
  - `min` and `mean` are calculated from `Top Volantis` shifted 5 ms up to `Base Volantis` shifted 10 ms down.
  - `rms` is calculated from `Top Volantis` shifted 15 ms up to `Base Volantis`.
- For `amplitude_depth` cubes:
  - `mean` has a separate interval definition from `rms` and `min`.
  - `min` has a different scaling factor than the others.
  