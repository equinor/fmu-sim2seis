# Attribute maps

Attribute maps can be generated both from observed seismic data and from modelled seismics. Definition of intervals
in which the attribute maps are estimated are controlled by a separate yaml-file.

## Yaml-file section
Default values normally apply for attribute map generation in the `sim2seis` *config* file, as most information is
taken from the dedicated interval definition file.

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

## Interval definition yaml file
The design criterion for interval definitions is to have much freedom, which results in a rather complicated
structure in the yaml file.

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