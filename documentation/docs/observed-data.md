# Observed Data Processing

The steps in `sim2seis` are typically executed within an `ert`-controlled ensemble run, which includes multiple 
realisations. Since the observed seismic data remains constant, only a single run is required, and this is performed
outside of `ert` via the command line:

```shell
# Normal run
> sim2seis_observed_data -s <start_dir> -c <config_dir> -f <config_file>
>
# Run with verbose output
> sim2seis_observed_data -s <start_dir> -c <config_dir> -f <config_file> -v true
>
# Run without generating attributes - depth conversion only
> sim2seis_observed_data -s <start_dir> -c <config_dir> -f <config_file> -n true
```
<span id="figure-1-command-line-run"><strong>Figure 1:</strong> Command line interface to observed data processing.</span>

Similar to the `sim2seis` workflow, the processing of observed data is controlled by YAML configuration files. There is 
one parameter file, shown in [Figure 2](#figure-2-example-yaml-file), and one interval definition file for generating 
attribute maps. The interval definition file follows the format described in [attribute maps](./attribute-maps.md).

```yaml
########################################################################################################################
#
# Configuration file for observation data in connection with a sim2seis runs
#
# Lines that are commented out are parameters that users very seldom have to change, they will use validated
# default values. However, they can be changed at need, but please verify that the values entered are valid
# before running any of the parts in the sim2seis workflow
#
########################################################################################################################


## For the main class: relative path to the config file
#______________________________________________________________________________________________________________________#
attribute_definition_file: observed_data_intervals_drogon.yml
# pickle_file_output_path: ../../share/observations/pickle_files
# pickle_file_prefix: observed_data
# rel_path_global_config: ../../fmuconfig/output
# observed_data_path: ../../share/observations/cubes


## Section for depth maps - inputs only
#______________________________________________________________________________________________________________________#
observed_depth_surf:
  # paths and standard naming. Depth maps are read from horizon folder INPUT
  suffix_name: depth
  horizon_names: [MSL, TopVolantis, BaseVolantis, BaseVelmodel]
  # depth_dir: ../../share/observations/maps


## Section for depth conversion
#______________________________________________________________________________________________________________________#
depth_conversion:
  z_inc: 4.0
  min_depth: 1500.0
  max_depth: 2000.0


# Section for ert and webviz export
#______________________________________________________________________________________________________________________#
webviz_map:
#  grid_file: simgrid.roff
#  zone_file: simgrid--zone.roff
#  region_file: simgrid--region.roff
  attribute_error: 0.07
#  grid_path: ../../sim2seis/input/pem
#  output_path: ../../share/observations/tables


## Section for time data
#______________________________________________________________________________________________________________________#
#observed_time_data:
  # time_cube_dir: ../../share/observations/cubes
  # time_cube_prefix: seismic--
  # time_suffix: --time.gri
  # horizon_dir: ../../share/observations/maps


## End of config file
#______________________________________________________________________________________________________________________#
```
<span id="figure-2-example-yaml-file"><strong>Figure 2:</strong> Example YAML configuration file for observed data.</span>
