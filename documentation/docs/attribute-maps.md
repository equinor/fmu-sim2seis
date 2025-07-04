# Attribute maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. The definition of intervals
for estimating attribute maps is controlled by a separate YAML file.

## YAML File Section
Default values typically apply for attribute map generation in the `sim2seis` configuration file, as most information is
derived from the dedicated interval definition file. [Figure 1](#igure-1-seismic-attributes-in-yaml) shows the relevant
sections of the configuration file.

```yaml
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
```
<span id="figure-1-seismic-attributes-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to attribute maps.</span>

In addition, the file name for the interval definition file is specified in the main part of the configuration YAML  
file:
```yaml
attribute_definition_file: modelled_data_intervals_drogon.yml
```

## Interval definition YAML  file
The interval definition file provides flexibility in defining intervals, resulting in a complex structure.
[Figure 2](#figure-2-interval-definiiton-in-yaml) illustrates the structure of the interval definition YAML file.

```yaml
global:
  gridhorizon_path: ../../share/results/maps  # path for input horizons
  attributes:      # attributes to be made for each cube
  - rms
  - mean
  - min
  scale_factor: 1.02
  workflow: "rms/sim2seis"                        # Metadata on workflow
  access_ssdl: {"rep_include": False, "access_level": "asset"}  # Metadata on access
  export_subfolder: "prm"                # Export subfolder (relative to ../../share/results/maps/)
  surface_postfix: --depth.gri
cubes:  # Setup for the cubes for which maps will be generated
  relai_depth:                               # arbitrary name of cube
    cube_prefix: syntseis--relai_full_depth--      # start of observed cube name
    filename_tag_prefix: relai_depth         # prefix of outputmap file name
    seismic_path: ../../share/results/seismic     # relative file path of seismic input cube
    vertical_domain: depth                        # depth or time
    depth_reference: msl                          # msl or null
    offset: full                                  # near, far, full, etc
    formations:                                   # settings for each formation maps will be generated for
      volantis:
        top_horizon: topvolantis           # Horizon used as top of the formation. ".gri" assumed as extension
        bottom_horizon: basevolantis       # Horizon used as base of the formation ".gri" assumed as extension
        top_surface_shift: -5                       # Extension of the window upwards from top surface
        base_surface_shift: 10                    # Extension of the window downwards from bottom surface
        rms:                               # Special requirements for 'rms' attribute
          top_horizon: topvolantis
          bottom_horizon: basevolantis
          top_surface_shift: -15
          scale_factor: 1.05
  amplitude_depth:                               # arbitrary name of cube
    cube_prefix: syntseis--amplitude_full_depth--      # start of cube name
    filename_tag_prefix: amplitude_depth         # prefix of outputmap file name
    seismic_path: ../../share/results/seismic         # relative file path of seismic input cube
    vertical_domain: depth                            # depth or time
    depth_reference: msl                              # msl or null
    offset: full                                      # near, far, full, etc
    formations:                                       # settings for each formation maps will be generated for
      volantis:
        top_horizon: topvolantis           # Horizon used as top of the formation. ".gri" assumed as extension
        bottom_horizon: basevolantis       # Horizon used as base of the formation ".gri" assumed as extension
        top_surface_shift: -17                      # Extension of the window upwards from top surface
        base_surface_shift: -2
        mean:                              # Special requirements for 'mean' attribute
          top_horizon: topvolantis
          bottom_horizon: basevolantis
          top_surface_shift: -10
          base_surface_shift: -5
        min:
          scale_factor: 2.0
```
<span id="figure-2-interval-definition-in-yaml"><strong>Figure 2:</strong> Parameters to define intervals for attribute map estimation.</span>

#### Global Section
The `global` section defines parameters that apply to all interval definitions unless overridden later:

- Horizon path: Controlled by `fmu-dataio`, default value shown.
- Attributes: Select attributes to highlight important features in the 4D seismic.
- Scale factor: Used to match values in similar attributes from observed seismic data.
- Metadata fields: Used in `fmu-dataio`.

#### Cube Section
- Cube names: Arbitrary values.
- Cube prefix: Concatenated with seismic difference dates defined in the global config file.
- Seismic path: Controlled by `fmu-dataio`, default value shown.
- Vertical domain: Default is `depth`.

#### Formations Section
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