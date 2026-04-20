#!/bin/sh
# Script to run all simseis-connected commands

## PEM
pem -c sim2seis/model -f pem_config.yml -g fmuconfig/output -o global_variables.yml -q HIST -m ./sim2seis/model/

## Seismic forward modelling and map attributes
sim2seis_seismic_forward -c sim2seis/model -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -q HIST -m ./sim2seis/model
sim2seis_map_attributes -c sim2seis/model/ -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -v true -a amplitude

## Relative seismic inversion and map attributes
sim2seis_relative_ai -c sim2seis/model -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -v true
sim2seis_map_attributes -c sim2seis/model/ -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -v true -a relai

## Observed data - with and without attribute generation
sim2seis_observed_data -c sim2seis/model/ -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -v true -p HIST
sim2seis_observed_data -c sim2seis/model/ -f sim2seis_config.yml -g fmuconfig/output -o global_variables.yml -v true -p HIST -n true

## Cleanup
sim2seis_cleanup -c sim2seis/model/ -f sim2seis_config.yml