# Observed Data Processing

The steps in `sim2seis` are typically executed within an `ert`-controlled ensemble run, which includes multiple
realisations. Since the observed seismic data remains constant, only a single run is required, and this is performed
outside of `ert` via the command line:

```shell
# Normal run
> sim2seis_observed_data -c <config_dir> -f <config_file> -g <global_dir> -o <global_file>
>
# Run with verbose output
> sim2seis_observed_data -c <config_dir> -f <config_file> -g <global_dir> -o <global_file> -v true
>
# Run without generating attributes - depth conversion only
> sim2seis_observed_data -c <config_dir> -f <config_file> -g <global_dir> -o <global_file> -n true
```

<span id="figure-1-command-line-run"><strong>Figure 1:</strong> Command line interface to observed data processing.</span>

## Configuration file

As part of the `sim2seis` workflow, the processing of observed data is controlled by a YAML configuration files. There
is one common parameter file, shown in [Figure 2](#figure-2-example-yaml-file), and one common interval definition file
for generating attribute maps. The interval definition file follows the format described in [attribute maps](./attribute-maps.md).

<<< ../../tests/data/sim2seis/model/sim2seis_combined_config.yml{yml}
<span id="figure-2-example-yaml-file"><strong>Figure 2:</strong> Example YAML configuration file for observed data.</span>

## Symlink to observed seismic cubes

To save space, the observed data are not duplicated for each realization in an `ert` run. Instead, symbolic links are
generated from the seismic cube directory (`./share/preprocessed/cubes`) to the directory that contains the observed
seismic cubes. This directory is set in the global configuration file. Below the entire seismic settings are included.
For the symbolic links, it is the `real_4d_cropped_path` that is used.

```yaml
  seismic:
    real_3d_path: /scratch/fmu/share/drogon/modeldata/share/seismic/static/input
    real_3d_cropped_path: /scratch/fmu/share/drogon/modeldata/share/seismic/static/21_0_0/cropped
    3d_templatecube: /scratch/fmu/share/drogon/modeldata/share/seismic/static/21_0_0/template/seismic_layout_static.segy
    real_3d:
      18v:
        ecldate: '20180101'
        time:
          amplitude_near: owexport_ampl_near_time_2018.segy
          amplitude_far: owexport_ampl_far_time_2018.segy
          relai_near: owexport_rai_near_time_2018.segy
          relai_far: owexport_rai_far_time_2018.segy
    real_4d_path: /scratch/fmu/share/drogon/modeldata/share/seismic/4d/input
    real_4d_cropped_path: /scratch/fmu/share/drogon/modeldata/share/seismic/4d/21_0_0/cropped
    4d_templatecube: /scratch/fmu/share/drogon/modeldata/share/seismic/4d/21_0_0/template/seismic_layout_4d.segy
    real_4d:
      18h_18v:
        ecldate:
        - 2018-07-01
        - 2018-01-01
        time:
          amplitude: owexport_ampl_18h_18v.segy
          relai: owexport_relai_18h_18v.segy
      19h_18v:
        ecldate:
        - 2019-07-01
        - 2018-01-01
        time:
          amplitude: owexport_ampl_19h_18v.segy
          relai: owexport_relai_19h_18v.segy
      20h_18v:
        ecldate:
        - 2020-07-01
        - 2018-01-01
        time:
          amplitude: owexport_ampl_20h_18v.segy
          relai: owexport_relai_20h_18v.segy
    ATTRIBUTE_HORIZONS_4D:
    - TopVolantis
    - BaseVolantis
    ATTRIBUTE_HORIZONS_3D:
    - TopVolantis
    - TopTherys
    - TopVolon
    - BaseVolantis
    ZONES_4D:
      Valysar:
      - TopVolantis
      - TopTherys
      Therys:
      - TopTherys
      - TopVolon
      Volon:
      - TopVolon
      - BaseVolantis
    ZONES_3D:
      Valysar:
      - TopVolantis
      - TopTherys
```

<span id="figure-3-global-settings"><strong>Figure 3:</strong> Seismic settings in the global configuration file.</span>

## When to run Observed Data Processing from `ert`

If `sim2seis` is run with structural uncertainty, the depth conversion of observed seismic data should be repeated for
each realisation, as it will vary. If not, cubes and attribute maps in depth domain will not be consistent between
observed and modelled data. All required parameters are defined in [ert configuration](./ert-configuration.md).

```ert
-- Optional run of depth conversion of observed data:
FORWARD_MODEL OBSERVED_DATA(<CONFIG_DIR>=<JOB_CONFIG_DIR>, <CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_DIR>=<GLOBAL_PATH>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <VERBOSE>=<VERBOSE_OUTPUT>)
```

<strong>Note</strong> that there is a difference in cases where there is or is not structural uncertainty. In a case with
no structural uncertainty, the observed data are regarded as being `preprocessed`, and e.g. resulting attributes etc.
are stored in `./share/preprocessed/maps`. In a case with structural uncertainty, the observed data use the term
`observed`, and so do the output directories: `./share/observations/...`.
