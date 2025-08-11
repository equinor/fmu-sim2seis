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

<<< ../../tests/data/sim2seis/model/obs_data_config.yml{yml}
<span id="figure-2-example-yaml-file"><strong>Figure 2:</strong> Example YAML configuration file for observed data.</span>

### When to run Observed Data Processing from `ert`
If `sim2seis` is run with structural uncertainty, the depth conversion of observed seismic data should be repeated for 
each realisation, as it will vary. If not, cubes and attribute maps in depth domain will not be consistent between 
observed and modelled data. All required parameters are defined in [ert configuration](./ert-configuration.md).

```ert
-- Optional run of depth conversion of observed data:
FORWARD_MODEL OBSERVED_DATA(<START_DIR>=<JOB_STARTDIR>, <CONFIG_DIR>=<RELPATH_CONFIG_FILES>, <CONFIG_FILE>=<OBS_DATA_CONFIG>, <VERBOSE>=<VERBOSE_OUTPUT>)
```