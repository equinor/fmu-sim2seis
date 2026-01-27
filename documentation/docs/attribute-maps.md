# Attribute Maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. The definition of intervals
for estimating attribute maps is controlled by a separate YAML file.

## YAML File Section

Default values typically apply for attribute map generation in the `sim2seis` configuration file, as most information is
derived from the dedicated interval definition file. [Figure 1](#igure-1-seismic-attributes-in-yaml) shows the relevant
sections of the configuration file. `webviz_map` refers to export of attribute maps in formats that can be read by
`webviz` and `ert` for visualisation and history matching. As all parameters are commented out, this indicates that
the default settings are used. It is only the name of the attribute definition file in the `main class setting` that
must be specified.

```yaml
########################################################################################################################
#
# Amplitude map and inversion map settings
#
# Best left with default values. The actual settings that define intervals and operators for attribute maps are 
# placed in the `attribute_definition_file`, given in the main class
#
########################################################################################################################
# amplitude_map:
#  attribute: amplitude
# inversion_map:
#  attribute: *inversion_attribute

########################################################################################################################
#
# Main class settings
#
# For the main class, there are only two required parameters. `test_run` is used in tests, and should be False in 
# real runs
#______________________________________________________________________________________________________________________#
attribute_definition_file: data_intervals_drogon.yml
```

<span id="figure-1-seismic-attributes-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to attribute maps.</span>

In addition, the file name for the interval definition file is specified in the main part of the configuration YAML  
file:

```yaml
attribute_definition_file: modelled_data_intervals_drogon.yml
```

## Interval Definition YAML  File

The interval definition file provides flexibility in defining intervals, resulting in a complex structure.
[Figure 2](#figure-2-interval-definiiton-in-yaml) illustrates the structure of the interval definition YAML file.

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
  