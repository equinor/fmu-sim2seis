# Input & output overview

This page gives an overview of relevant input and output files, for the different steps in the `sim2seis` workflow.

> [!WARNING] TODO:
> Some files are on project level, some are on realization level.

## Observed data

### Input

| Description | Directory | File |
| ------------- | -----------| ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml` / `global_variables_pred.yml` |
|  Observed data, time domain | `./share/observations/cubes` | `seismic--<amplitude/relai>_<stack>_time--<date pair>.segy` |
| Depth and time surfaces | `./share/observations/maps` | `<horizon>--depth.gri, <horizon>--time.gri` |
| Grid definition | `./sim2seis/input/pem` | `simgrid.roff` |
| Zone definition | `./sim2seis/input/pem` | `simgrid—zone.roff` |
| Region definition | `./sim2seis/input/pem` | `simgrid—region.roff` |
| Configuration file | `./sim2seis/model` | `obs_data_config.yml` |
| Attribute interval definition file | `./sim2seis/model` | `observed_data_intervals_drogon.yml` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Duplicate of attribute map from fmu-dataio – for Webviz | `./ert/input/observations/seismic` | `<horizon>--<attribute>_<stack>_depth--<date pair>.txt` |
| Attribute maps for ERT | `./ert/input/observations/seismic` | `meta--<horizon>--<attribute>_<stack>_depth--<date pair>.txt` |
| Observed data, depth domain | `./share/observations/cubes` | `seismic--<amplitude/relai>_<stack>_<time/depth>--<date pair>.segy` |
| Depth attribute maps | `./share/observations/maps` | `<horizon>--<attribute>_<stack>_depth--<date pair>.gri` |
| Saved class objects from the modules in fmu-sim2seis | `./share/observations/pickle_files` | `observed_data*.pkl` |
| Attribute maps export from fmu-dataio | `./share/observations/tables` | `<horizon>--<attribute>_<stack>_depth--<date pair>.csv` |

## Seismic forward modelling

### Input

| Description | Directory | File |
| ------------- | -----------| ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml / global_variables_pred.yml` |
| Depth and time surfaces | `./share/results/maps` | `<horizon>--depth.gri, <horizon>--time.gri` |
| Grid definition | `./sim2seis/input/pem` | `simgrid.roff` |
| Zone definition | `./sim2seis/input/pem` | `simgrid—zone.roff` |
| Region definition | `./sim2seis/input/pem` | `simgrid—region.roff` |
| Configuration file | `./sim2seis/model` | `sim2seis_config.yml` |
| Attribute interval definition file | `./sim2seis/model` | `modelled_data_intervals_drogon.yml` |
| Model file for seismicforward run | `./sim2seis/model` | `model_file_<stack>.xml` |
| `Vp`, `Vs`, density output from PEM | `./sim2seis/output/pem` | `pem--<date>.grdecl` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Output seismic cubes | `./share/results/cubes` | `syntseis—amplitude_<stack>_<time/depth>--<date/date pair>.segy` |
| Depth attribute maps | `./share/results/maps` | `<horizon>--amplitude_<attribute>_<stack>_depth--<date pair>.gri` |
| Saved class objects from the modules in `fmu-sim2seis` | `./share/results/pickle_files` | `seis_4d_*.pkl` |

## Relative acoustic impedance  calculation

### Input

| Description | Directory | File |
| ------------- | -----------| ---- |
| Configuration file | `./fmuconfig/output` | `global_variables.yml` / `global_variables_pred.yml` |
| Attribute interval definition file | `../sim2seis/model` | `sim2seis_config.yml` |
| Global config | `./sim2seis/model` | `modelled_data_intervals_drogon.yml` |
| Velocity model for depth conversion | `./share/results/pickle_files` | `seis_4d_velocity_model.pkl` |
| Input seismic time cubes | `./share/results/cubes` | `syntseis—amplitude_<stack>_time--<date>.segy` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Output seismic cubes | `./share/results/cubes` | `syntseis—relai_<stack>_depth--<date>.segy` |
| Depth attribute maps | `./share/results/maps` | `<horizon>--relai_<attribute>_<stack>_depth--<date pair>.gri` |
| Saved class objects from the modules in fmu-sim2seis | `./share/results/pickle_files` | `relai_<time/depth>.pkl` |

## Map attributes

### Input

| Description | Directory | File |
| ------------- | -----------| ---- |
| Difference cubes | `./share/results/pickle_files` | `seis_4d_diff_.pkl` / `relai_diff_depth.pkl` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Attribute maps from forward model or relative ai | `../../share/results/pickle_files` | `amplitude_maps_depth.pkl` / `relai_maps_depth.pkl` |
| Duplicate of attribute map from fmu-dataio – for Webviz | `../../ert/input/results/seismic` | `<horizon>--amplitude_<attribute>_<stack>_depth--<date pair>.txt` |
| Attribute maps for ERT | `../../ert/input/results/seismic` | `meta--<horizon>--amplitude_<attribute>_<stack>_depth--<date pair>.txt` |
| Attribute maps export from fmu-dataio | `../../share/results/tables` | `<horizon>--amplitude_<attribute>_<stack>_depth--<date pair>.csv` |

## PEM

### Input

| Description | Directory | File |
| ------------- | -----------| ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml` / `global_variables_pred.yml` |
| Configuration file | `./sim2seis/model` | `pem_config.yml` |
| Eclipse grid definition | `./sim2seis/input/pem` | `ECLIPSE.EGRID` |
| Eclipse init properties | `./sim2seis/input/pem` | `ECLIPSE.INIT` |
| Eclipse restart properties | `./sim2seis/input/pem` | `ECLIPSE.UNRST` |
| NTG property – optional | `./sim2seis/input/pem` | `grid--ntg_pem.roff` |
| Volume fraction grid definition | `./sim2seis/input/pem` | `export_grid.grdecl` |
| Volume fraction sets | `./sim2seis/input/pem` | `export_prop.grdecl` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Detailed results per restart date and differences | `../../share/results/grids` | `*.roff` |
| `Vp`, `Vs`, density | `./sim2seis/output/pem` | `pem--<date>.grdecl` |
| Elastic properties of fluids and minerals | `./share/results/grids` | `*.roff` |


<style>
table{
   overflow-x:scroll;
   width:700px;
   display:block;
   white-space: nowrap;
}
</style>

