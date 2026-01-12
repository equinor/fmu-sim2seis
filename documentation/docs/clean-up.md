# Clean-up of Intermediate Files

During the `sim2seis` run, intermediate files are generated to provide subsequent steps with detailed information about
the results of earlier stages. These files are in Python's `pickle` format, where class objects are stored. As `pickle`
files can be quite large, they should be deleted when no longer required. This **can** also be incorporated into an
`ert` ensemble run, ensuring that the `pickle` files for each realisation are removed. The clean-up process can be
executed via the command line:

```shell
> sim2seis_cleanup -c <config_dir> -f <config_file>
```

To see all options:

```shell
> sim2seis_cleanup --help
```

To add this in an `ert` run, the following line must be added at the end of the `sim2seis` job file:

```ert
-- Define your variables:
FORWARD_MODEL CLEANUP(<CONFIG_DIR>=<RELPATH_CONFIG_FILES>, <CONFIG_FILE>=<SIM2SEIS_CONFIG_FILE_NAME>)
```

 All required parameters for an `ert` run are defined in [ert configuration](./ert-configuration.md).
