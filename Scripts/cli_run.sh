#!/bin/sh
# Script to run all sim2seis-connected commands

# Stop script if error
set -e

## PEM
pem -f sim2seis/model/pem_config.yml -g fmuconfig/output/global_variables.yml -m HIST -v true

## Seismic forward modelling and map attributes
sim2seis_seismic_forward -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -m HIST -v true
sim2seis_map_attributes -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -a amplitude -v true

## Relative seismic inversion and map attributes
sim2seis_relative_ai -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -v true
sim2seis_map_attributes -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -a relai -v true

## Observed data - with and without attribute generation
sim2seis_observed_data -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -o HIST -v true
sim2seis_observed_data -f sim2seis/model/sim2seis_config.yml -g fmuconfig/output/global_variables.yml -o HIST -n true -v true

## Cleanup
sim2seis_cleanup -f sim2seis/model/sim2seis_config.yml
