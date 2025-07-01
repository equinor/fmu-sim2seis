> [!WARNING]
> `fmu-sim2seis` is not yet qualified technology, and as of today only applicable for selected pilot test fields.

**[📚 User documentation](https://equinor.github.io/fmu-sim2seis/)**

## What is fmu-sim2seis?

Calculates synthetic seismic from reservoir simulation model, together with a petro-elastic model.

`fmu-sim2seis` can be run either from command line, or from ERT, the latter being the
preferred option.

### Installation

To install `fmu-sim2seis`, run
```bash
pip install fmu-sim2seis
```

### ERT jobs

`fmu-sim2seis` is divided into a series of separate jobs:

* sim2seis_seismic_forward
* sim2seis_relative_ai
* sim2seis_observed_data
* sim2seis_map_attributes

There exists also a forward model for running petro-elastic modelling, defined in [**fmu-pem**](https://github.com/equinor/fmu-pem).

In the ERT-file for running fmu-sim2seis, necessary arguments are shown in [this example ERT setup](./ERT/run_sim2seis.ert).

Beware of hardcoded directory names - they should be replaced by **your** project path/name.

```bash
cd ./ERT
ert gui run_sim2seis.ert
```

`fmu-sim2seis` (and `fmu-pem`) are controlled by a series of `.yaml`-files which you find in examples of [here](./tests/TestData/sim2seis/model/pem).

The files `modelled_data_intervals` and `observed_data_intervals.yml` are used to define zones/intervals 
for estimating seismic attributes. `sim2seis_config` contains all configuration parameters for all parts
of `fmu-sim2seis` workflow, except for observed seismic data, which has its own configuration file - 
`obs_data_config.yml`.

### Tests

`fmu-sim2seis` has tests that use the `tests/TestData` structure, which contains the necessary input data
files.
```bash
pytest tests/test_run_sim2seis
```

### User interface

Users can visit https://equinor.github.io/fmu-sim2seis/ in order to get help configuring the `fmu-sim2seis` input data.

Developing the user interface can be done by:
```bash
cd ./documentation
npm ci  # Install dependencies
npm run create-json-schema  # Extract JSON schema from Python code
npm run docs:dev  # Start local development server
```
The JSON schema itself (type, title, description etc.) comes from the corresponding Pydantic models in the Python code.
