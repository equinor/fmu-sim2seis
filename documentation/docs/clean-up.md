# Clean-up of Intermediate Files

During the `sim2seis` run, intermediate files are generated to provide subsequent steps with detailed information about
the results of earlier stages. These files are in Python's `pickle` format, where class objects are stored. As `pickle`
files can be quite large, they should be deleted when no longer required. This **can** also be incorporated into an
`ert` ensemble run, ensuring that the `pickle` files for each realisation are removed. All pickle files are removed
unless the `-l` option of given, with which it is possible to select one or more of the pickle files.

Another group of intermediate files are seismic cubes for single dates, from which difference seismic are calculated.
As these files are not required after a `sim2seis`run, this is the default behaviour. To keep the files, give the
option `-s` or `--include-seismic` `false` to `sim2seis_cleanup`.

For removal of pickle files seismic cubes, the present directory must be set to the top of the FMU directory structure.
The subdirectory for cleanup of pickle files is set in the configuration files that `sim2seis_cleanup` reads.  Seismic
cubes are placed in sub-directories `./share/results/cubes`, `./share/preprocessed/cubes` or
`./share/observations/cubes`. See examples below.

`sim2seis_cleanup` can be used to delete intermediate files in an entire ensemble run if it is called from command line.
In that case  `-i` or `--is_ensemble` must be set to `true`. Note that this option is not possible to give in `ert` runs.

## Command line examples

```shell
> # Print help 
> sim2seis_cleanup --help
usage: /private/hfle/sandbox/fmu-sim2seis/src/fmu/sim2seis/utilities/argument_parser.py [-h] -f CONFIG_FILE [-l PREFIX_LIST [PREFIX_LIST ...]] [-s INCLUDE_SEISMIC] [-i IS_ENSEMBLE]

options:
  -h, --help            show this help message and exit
  -f CONFIG_FILE, --config-file CONFIG_FILE
                        Configuration yaml path name
  -s INCLUDE_SEISMIC, --include-seismic INCLUDE_SEISMIC
                        (Optional) Remove single date seismic cubes, default=True
  -i IS_ENSEMBLE, --is_ensemble IS_ENSEMBLE
                        (Optional) Remove intermediate files for all realizations, default=False
```

```shell
> # Remove `relai` pickle files only, let seismic cubes remain.  
> cd /project/<myproject>/resmod/ff/users/26.0.0
> sim2seis_cleanup -f ./sim2seis/model/sim2seis_combined_config.yml -l relai -s false
```

```shell
> # Cleanup of all pickle files and and single date seismic cubes
> cd /project/<myproject>/resmod/ff/users/26.0.0
> sim2seis_cleanup -f ./sim2seis/model/sim2seis_combined_config.yml 
```

```shell
> # Go to top of ensemble structure to remove all intermediate files
> cd /scratch/fmu/<user>/<case>
> sim2seis_cleanup -f ./realization-0/iteration-0/sim2seis/model/sim2seis_combined_config.yml -i true
```

With the settings above, all pickle files are deleted. It is also possible to specify that only the pickle files from
a certain part of the `seim2seis`workflow are deleted. To see all options:

To add this in an `ert` run, the following line must be added at the end of the `sim2seis` job file:

```ert
-- Define your variables:
FORWARD_MODEL CLEANUP(<CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE>)
```

 All required parameters for an `ert` run are defined in [ert configuration](./ert-configuration.md).
