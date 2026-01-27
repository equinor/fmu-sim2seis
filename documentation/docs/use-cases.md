# Why `sim2seis`?

The FMU `sim2seis` (**sim**ulator to **seis**mic) workflow calculates seismic parameters and synthetic seismic based on
reservoir simulation results. Typical use cases include:

* Feasibility studies for 4D seismic
* History matching to 4D seismic data
* Assisting the interpretation of 4D seismic data

The following steps are typically undertaken when calculating synthetic seismic from reservoir simulation results:

1. A field-specific [petro-elastic model (PEM)](static-and-dynamic-input.md) is used to calculate elastic parameters in
   each grid cell. Static and dynamic parameters from the geomodel and simulation model serve as inputs to the PEM.
2. [Synthetic seismic cubes](seismic-forward.md) are generated based on the input from the steps above and a seismic
   wavelet.
3. [Depth-to-time conversion](./time-depth-conversion.md) is performed on the synthetic seismic cube to prepare for
   relative seismic inversion.
4. Optional: [relative seismic inversion](./relative-seismic-inversion.md) is applied to the time-converted synthetic
   seismic cubes.
5. Time shift estimation is conducted based on the synthetic seismic differences.
6. Various results can then be extracted, such as:
    * [attribute maps](./attribute-maps.md) from the synthetic seismic and relative seismic inversion. The list of
      possible attributes can be found
      in [xtgeo.cubes](https://xtgeo.readthedocs.io/en/stable/api-cubes.html#xtgeo.Cube.compute_attributes_in_window).
    * time shift change maps

`sim2seis` settings are read from a `YAML` file. The section links above discuss the parts of the YAML file that control
the matching aspect of the `sim2seis` workflow. Lines in the configuration YAML file that are commented indicate default
values, which are typically preferred, such as file names, directory names, etc.

There are two related commands that are optional within the `sim2seis` workflow:

1. [Observed data processing](./observed-data.md)
2. [Clean-up of intermediate files](clean-up.md)

Neither of these commands is usually included when `sim2seis` is run from `ert`, but they can be in certain cases. Both
have command-line interfaces, which are explained in the links above.

## `ERT` Run

The steps from `PEM` to `attribute_maps` are based on results from previous steps in the `sim2seis` workflow, so they
must be run in a fixed sequence in `ert`. The minimum mandatory sequence is:

1. PEM
2. Seismic forward modelling
3. Amplitude maps

If relative acoustic impedance is also included, the sequence becomes:

1. PEM
2. Seismic forward modelling
3. Relative acoustic impedance
4. Amplitude maps
5. Relai maps

A setup file for an `ert` job is shown in [`ert` configuration](./ert-configuration.md).

## Command-line runs

All parts of `sim2seis` can be run from command-line. The calls vary slightly, depending on what information is required
in addition to the parameters in the configuration file. Below, all command-line calls are listed with some additional
comments. In this example, we run `sim2seis` on a copy of the Drogon test data set.

```shell
> # Go to top of the project structure
> cd /project/fmu/tutorial/drogon/resmod/ff/users/hfle/dev
> # The PEM is the first required step. It has its own YAML parameter file. Note that the path to the global config 
> # directory is given as a relative path from the config directory
> pem --help
> pem -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml -m ./sim2seis/model
> 
> # Processing observed data is done once, unless there is structural uncertainty in the model, see section on 
> # observed data
> sim2seis_observed_data --help
> sim2seis_observed_data -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml
>
> # Seismic forward model part also includes depth-to-time conversion, used when seismic inversion is included in the
> # workflow
> sim2seis_seismic_forward --help
> sim2seis_seismic_forward -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml -m ./sim2seis/model
>
> # Optionally run seismic inversion
> sim2seis_relative_ai --help
> sim2seis_relative_ai -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml
>
> # Generate attribute maps from modelled seismic data
> sim2seis_map_attributes --help
> sim2seis_map_attributes -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml -a amplitude
>
> # In case seismic inversion is run
> sim2seis_map_attributes -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml 
>
> # As one step in the sim2seis workflow requires the previous ones to be run, data I/O are handled by intermediate
> # files, which can have significant size. When everything is complete, the intermediate files can be removed by a 
> # clean-up
> sim2seis_cleanup --help
> sim2seis_cleanup -c ./sim2seis/model -f new_pem_config.yml -g ../../fmuconfig/output -o global_variables.yml 
```
