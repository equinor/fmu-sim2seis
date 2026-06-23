# ERT configuration file

You can include `sim2seis` in your ERT set-up by including the following snippet:

```ert
-- Define your variables:
DEFINE <CONFIGDIR> <RUNPATH>/sim2seis/model
DEFINE <PEM_CONFIG_FILE_NAME> <CONFIGDIR>/pem_config_condensate.yml
DEFINE <SIM2SEIS_CONFIG_FILE_NAME> <CONFIGDIR>/sim2seis_combined_config.yml
DEFINE <GLOBAL_PATH> fmuconfig/output
DEFINE <GLOBAL_CONFIG_FILE> <GLOBAL_PATH>/global_variables.yml
DEFINE <VERBOSE_OUTPUT> False
DEFINE <OBS_PREFIX> HIST
DEFINE <MOD_PREFIX> HIST 

-- Optional run of depth conversion of observed data:
FORWARD_MODEL OBSERVED_DATA(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <OBS_DATE_PREFIX>=<OBS_PREFIX>, <VERBOSE>=<VERBOSE_OUTPUT>)

-- Run the PEM
FORWARD_MODEL PEM(<CONFIG_FILE>=<PEM_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <MOD_DATE_PREFIX>=<MOD_PREFIX>, <VERBOSE>=<VERBOSE_OUTPUT>)

-- All forward models in sim2seis, except cleanup
FORWARD_MODEL SEISMIC_FORWARD(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <MOD_DATE_PREFIX>=<MOD_PREFIX>, <VERBOSE>=<VERBOSE_OUTPUT>)

FORWARD_MODEL RELATIVE_INVERSION(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <VERBOSE>=<VERBOSE_OUTPUT>)

FORWARD_MODEL MAP_ATTRIBUTES(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <ATTRIBUTE>=amplitude)

FORWARD_MODEL MAP_ATTRIBUTES(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <GLOBAL_FILE>=<GLOBAL_CONFIG_FILE>, <ATTRIBUTE>=relai)

-- Optional run of data cleanup, all `pickle` files are removed:
FORWARD_MODEL CLEANUP(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>)

-- Optional run of data cleanup limited to removing attribute map `pickle`-files:
FORWARD_MODEL CLEANUP(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>, <PREFIX_LIST>=<CLEANUP_PREFIX>)
```

On the next page you will get help setting up your `sim2seis_combined_config.yml`.

For details on how to configure your `pem_config.yml`, see corresponding [FMU PEM](https://equinor.github.io/fmu-pem/) documentation.
