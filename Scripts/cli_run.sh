#!/bin/sh
# Script to run all sim2seis-connected commands

# Stop script if error
set -e

## PEM
pem -c sim2seis/model -f pem_config.yml -g fmuconfig/output -o global_variables.yml -q HIST -m ./sim2seis/model/

## Seismic forward modelling and map attributes
sim2seis_seismic_forward -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -m HIST
sim2seis_map_attributes -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true -a amplitude

## Relative seismic inversion and map attributes
sim2seis_relative_ai -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true
sim2seis_map_attributes -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true -a relai

## Observed data - with and without attribute generation
sim2seis_observed_data -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true -o HIST
sim2seis_observed_data -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true -o HIST -n true

## Cleanup
sim2seis_cleanup -f sim2seis/model/sim2seis_config.yml
