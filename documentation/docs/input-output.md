# Input & output overview

This page gives an overview of relevant input and output files, for the different steps in the `sim2seis` workflow.

## Observed data

### Input

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml` / `global_variables_pred.yml` |
| Observed data, time domain * | `./share/preprocessed/cubes` | `seismic--<attribute>_<stack>_time--<date/date pair>.segy` |
| Depth and time surfaces * | `./share/preprocessed/maps` | `<horizon>--depth.gri, <horizon>--time.gri` |
| Grid definition | `./sim2seis/input/pem` | `simgrid.roff` |
| Zone definition | `./sim2seis/input/pem` | `simgrid--zone.roff` |
| Region definition | `./sim2seis/input/pem` | `simgrid--region.roff` |
| Configuration file | `./sim2seis/model` | `sim2seis_config.yml` |
| Attribute interval definition file | `./sim2seis/model` | `observed_data_intervals_drogon.yml` |

'*': At project level, not realisation level. Note that in cases modelled with depth uncertainty, `preprocessed` is
changed to `observations`.

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Attribute maps for ERT | `./ert/input/preprocessed/seismic` | `<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.txt` |
| Attribute map with metadata (Webviz) | `./ert/input/preprocessed/seismic` | `meta--<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.txt` |
| Observed data, depth domain | `./share/preprocessed/cubes` | `seismic--<attribute>_<stack>_<time/depth>--<date/date pair>.segy` |
| Depth attribute maps | `./share/preprocessed/maps` | `<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.gri` |
| Saved class objects from the modules in fmu-sim2seis | `./share/results/pickle_files` | `observed_data*.pkl` |
| Attribute maps export from fmu-dataio | `./share/preprocessed/tables` | `<horizon>--<attribute>_<stack>_depth--<date pair>.csv` |

## Seismic forward modelling

### Input

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml / global_variables_pred.yml` |
| Depth and time surfaces | `./share/results/maps` | `<horizon>--depth.gri, <horizon>--time.gri` |
| Grid definition | `./sim2seis/input/pem` | `simgrid.roff` |
| Zone definition | `./sim2seis/input/pem` | `simgrid--zone.roff` |
| Region definition | `./sim2seis/input/pem` | `simgrid--region.roff` |
| Configuration file | `./sim2seis/model` | `sim2seis_config.yml` |
| Attribute interval definition file | `./sim2seis/model` | `modelled_data_intervals_drogon.yml` |
| Model file for seismicforward run | `./sim2seis/model` | `model_file_<stack>.xml` |
| `Vp`, `Vs`, density output from PEM | `./sim2seis/output/pem` | `pem--<date>.grdecl` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Output seismic cubes | `./share/results/cubes` | `seismic--amplitude_<stack>_<time/depth>--<date/date pair>.segy` |
| Depth attribute maps | `./share/results/maps` | `<horizon>--amplitude_<stack>_<calc>_depth--<date pair>.gri` |
| Saved class objects from the modules in `fmu-sim2seis` | `./share/results/pickle_files` | `seis_4d_*.pkl` |

## Relative acoustic impedance  calculation

### Input

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Global config | `./fmuconfig/output` | `global_variables.yml` / `global_variables_pred.yml` |
| Configuration file | `./sim2seis/model` | `sim2seis_config.yml` |
| Attribute interval definition file | `./sim2seis/model` | `modelled_data_intervals_drogon.yml` |
| Velocity model for depth conversion | `./share/results/pickle_files` | `seismic_fwd_velocity_model.pkl` |
| Input seismic time cubes | `./share/results/cubes` | `seismic--amplitude_<stack>_time--<date>.segy` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Output seismic cubes | `./share/results/cubes` | `seismic--relai_<stack>_depth--<date/date pair>.segy` |
| Depth attribute maps | `./share/results/maps` | `<horizon>--relai_<stack>_<calc>_depth--<date pair>.gri` |
| Saved class objects from the modules in fmu-sim2seis | `./share/results/pickle_files` | `relai_<time/depth>.pkl` |

## Map attributes

### Input

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Difference cubes | `./share/results/pickle_files` | `seis_4d_diff_.pkl` / `relai_diff_depth.pkl` |

### Output

| Description | Directory | File |
| ------------- | ----------- | ---- |
| Attribute maps from forward model or relative ai | `./share/results/pickle_files` | `amplitude_maps_depth_attributes.pkl` / `relai_maps_depth_attributes.pkl` |
| Attribute maps for ERT | `./share/results/tables` | `<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.txt` |
| Attribute map with metadata (Webviz) | `./share/results/tables` | `meta--<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.txt` |
| Attribute maps export from fmu-dataio | `./share/results/tables` | `<horizon>--<attribute>_<stack>_<calc>_depth--<date pair>.csv` |

## PEM

### Input

| Description | Directory | File |
| ------------- | ----------- | ---- |
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
