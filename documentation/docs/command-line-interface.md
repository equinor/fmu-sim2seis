# Command-line runs

All parts of `sim2seis` can be run from command-line. The calls vary slightly, depending on what information is required
in addition to the parameters in the configuration file. Below, all command-line calls are listed with some additional
comments. In this example, we run `sim2seis` on a copy of the Drogon test data set.

```shell
> # Go to top of the project structure
> cd /project/fmu/tutorial/drogon/resmod/ff/users/hfle/dev
> # The PEM is the first required step. It has its own YAML parameter file. Note that the path to the global config 
> # directory is given as a relative path from the FMU top directory
> pem --help
> pem -c ./sim2seis/model -f new_pem_config.yml -g fmuconfig/output -o global_variables.yml -q HIST
> 
> # Processing observed data is done once, unless there is structural uncertainty in the model, see section on 
> # observed data. Optional -v argument for 'verbose'
> sim2seis_observed_data --help
> sim2seis_observed_data -c ./sim2seis/model -f sim2seis_combined_config.yml -g fmuconfig/output -o global_variables.yml -p HIST
>
> # Seismic forward model part also includes depth-to-time conversion, used when seismic inversion is included in the
> # workflow
> sim2seis_seismic_forward --help
> sim2seis_seismic_forward -c ./sim2seis/model -f sim2seis_combined_config.yml -g fmuconfig/output -o global_variables.yml -q HIST -v True
>
> # Optionally run seismic inversion
> sim2seis_relative_ai --help
> sim2seis_relative_ai -c ./sim2seis/model -f sim2seis_combined_config.yml -g fmuconfig/output -o global_variables.yml -v True
>
> # Generate attribute maps from modelled seismic data
> sim2seis_map_attributes --help
> sim2seis_map_attributes -c ./sim2seis/model -f sim2seis_combined_config.yml -g fmuconfig/output -o global_variables.yml -a amplitude
>
> # In case seismic inversion is run
> sim2seis_map_attributes -c ./sim2seis/model -f sim2seis_combined_config.yml -g fmuconfig/output -o global_variables.yml -a relai
>
> # As one step in the sim2seis workflow requires the previous ones to be run, data I/O are handled by intermediate
> # files, which can have significant size. When everything is complete, the intermediate files can be removed by a 
> # clean-up
> sim2seis_cleanup --help
> sim2seis_cleanup -c ./sim2seis/model -f sim2seis_combined_config.yml -l relai
```
