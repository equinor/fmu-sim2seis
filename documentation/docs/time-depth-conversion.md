# Domain conversion between time and depth

Domain conversion between time and depth is needed to be able to compare observed seismic data (normally in time) with
synthetic seismic (can be time or depth) and geomodel and simulation model (in depth). The time-to-depth or vice versa
is performed in a simplified way, with a velocity model calculated from a matching pairs of time- and depth-surfaces.

It is normally not required by a `sim2seis` user to alter any code for the domain conversion - it is integrated in the
scripts. Examples on use of the code are shown in [fmu-tools documentation](https://equinor.github.io/fmu-tools/domain_conversion.html)

## Yaml-file section
Several parameters are required to control the domain conversion. [Figure 1](#figure-1-domain-conversion-in-yaml) shows 
the domain conversion-part of the `sim2seis` configuration file. Horizon names and limits for the generated cubes in 
time and depth need to be set. The horizon file names are expected to be lower-case version of the horizon names, with
a postfix `--time.gri` or `--depth.gri`, depending on the domain.

Depth parameters are given in unit `m`, time parameters in unit `ms`.

```yaml
## Section for depth conversion
#______________________________________________________________________________________________________________________#
depth_conversion:
  horizon_names: [MSL, TopVolantis, BaseVolantis, BaseVelmodel]
  min_depth: 1500.0
  max_depth: 2000.0
  z_inc: 4.0
  min_time: 1500.0
  max_time: 2000.0
  t_inc: 4.0
#  time_cube_dir: ../../share/results/cubes
#  depth_cube_dir: ../../share/results/cubes
#  horizon_dir: ../../share/results/maps
#  depth_suffix: --depth.gri
#  time_suffix: --time.gri
```
<span id="figure-1-domain-conversion-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic forward.</span>