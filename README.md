# fmu-sim2seis

fmu-sim2seis is an "RMS-less" version of the `sim2seis` workflow in RMS. 
It is designed to be run either from command line, or from ERT, the latter being the
preferred option.

In the development phase, there will be multiple branches in the GitHub repository. *It can 
be assumed that the most recent branch is the one that should be used for testing*. To clone
the fmu-sim2seis:

    git clone git@github.com:equinor/fmu-sim2seis.git
    git checkout fixed-rebase-conflict
    git pull

Before fmu-sim2seis is installed as part of **komodo**, it is recommended to create a virtual environment.
The following steps are made to create and activate a virtual environment named _env_fmu_s2s_ in the present 
working directory:

    komodoenv env_fmu_s2s
    source env_fmu_s2s/bin/activate.csh

or just `activate` if bash shell.

You can verify that the virtual environment is activated by checking the command prompt. It should show the name of the
virtual environment. Also, the command `which python` should point to the python executable in the virtual environment.

    which python
    which pip

To install fmu-sim2seis, navigate to the root directory of the repository and run:

    cd fmu-sim2seis
    pip install .

You might get a warning that pip is outdated. If so, run:

    pip install --upgrade pip

If you wish to run the available tests, install the test dependencies:

    pip install .['tests']

fmu-sim2seis is divided into a series of separate jobs:

-> sim2seis_seismic_forward
-> sim2seis_relative_ai
-> sim2seis_observed_data
-> sim2seis_map_attributes

Forward model for running the PEM is also included, but that is defined in **fmu-pem** module

In the ERT-file for running fmu-sim2seis, necessary arguments are shown:

    more ./ERT/run_sim2seis.ert

Beware of hardcoded directory names - they should be replaced by **your** project path/name.

    cd ./ERT
    ert gui run_sim2seis.ert

*fmu-sim2seis* (and *fmu-pem*) are controlled by a series of *yaml-files*

    cd tests/TestData/sim2seis/model/pem
    ls -l *.yml

The files *modelled_data_intervals* and *observed_data_intervals.yml* are used to define zones/intervals 
for estimating seismic attributes. *sim2seis_config* contains all configuration parameters for all parts
of fmu-sim2seis workflow, except for observed seismic data, which has its own configuration file - 
obs_data_config.yml.

fmu-sim2seis has tests that use the `tests/TestData` structure, which contains the necessary input data
files.

    pytest tests/test_run_sim2seis

## User interface

Users can visit https://equinor.github.io/fmu-sim2seis/ in order to get help configuring the `fmu-sim2seis` input data.

Developing the user interface can be done by:
```bash
cd ./documentation
npm ci  # Install dependencies
npm run create-json-schema  # Extract JSON schema from Python code
npm run docs:dev  # Start local development server
```
The JSON schema itself (type, title, description etc.) comes from the corresponding Pydantic models in the Python code.
