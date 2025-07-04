# Attribute maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. Definition of intervals
in which the attribute maps are estimated are controlled by a separate yaml-file.

## Yaml-file section
Default values normally apply for attribute map generation in the `sim2seis` *config* file, as most information is
taken from the dedicated interval definition file, see [Figure 1](#igure-1-seismic-attributes-in-yaml).

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

In addition, the file name for the interval definition file is set in the main part of the config yaml file:
```yaml
attribute_definition_file: modelled_data_intervals_drogon.yml
```

## Interval definition yaml file
The design criterion for interval definitions is to have much freedom, which results in a rather complicated
structure in the yaml file, [Figure 2](#figure-2-interval-definiiton-in-yaml). The different sections in the interval 
definition are described below. A separate file is required for defining attribute map intervals for observed
seismic data.

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

#### global:
`global` sets up parameters that apply to all interval definitions, unless they are overruled later. 
- The *horizon path* is normally controlled by `fmu-dataio`, the default value is shown
- The *list of attributes* is chosen in each case. Make a selection of attributes that can highlight important features 
  in the 4D seismic
- *Scale factor* can be used to match values in similar attributes from observed seismic data
- *Metadata fields* are used in `fmu-dataio`

#### cubes:
- *Cube names* are arbitrary values
- *Cube prefix* is concatenated with the seismic difference dates that are defined in the global config file and all 
  matching cubes are selected
- *Seismic path* is normally controlled by `fmu-dataio`, the default value is shown
- *Vertical domain* is by default *depth*

#### formations:
Several formations can be defined under each cube. There are several ways the intervals can be defined:

- Top and base horizon, with optional shift for each of them
- Top horizon and interval length, with optional shift of the top horizon

The interval settings will apply to all attribute calculations that are listed in the `global` section, unless a 
specific value is set. In the case above, for the `relai_depth`-cubes, `min` and `mean` are calculated from 
`Top Volantis` shifted 5 ms up to `Base Volantis` shifted 10 ms down, whereas the `rms` attribute is calculated from
`Top Volantis` shifted 15 ms up to `Base Volantis`. For the cubes `amplitude_depth`, `mean` has a separate interval 
definition from `rms` and `min`, and `min` has a different scaling than the others.