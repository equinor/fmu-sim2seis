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

A set-up file for an `ert` job is shown in [`ert` configuration](./ert-configuration.md).

## Incremental Configuration Setup

It is possible to build the `sim2seis_config.yml` one section at a time, running and validating each workflow step
before moving on to the next. This makes it easier to isolate configuration or data issues to the specific step you
are working on.

The table below shows which sections of `sim2seis_config.yml` are required for each forward model step. Sections not
needed for the step you are currently setting up can simply be left out of the file.

| Config section | `SEISMIC_FORWARD` | `RELATIVE_INVERSION` | `MAP_ATTRIBUTES` | `OBSERVED_DATA` |
|---|:---:|:---:|:---:|:---:|
| `seismic_fwd` | ✅ required | — | — | — |
| `depth_conversion` | ✅ required | —¹ | — | ✅ required |
| `attribute_map_definition_file` | — | — | ✅ required | ✅ required |
| `webviz_map` | — | — | ✅ required | ✅ required |
| `seismic_inversion` | — | optional² | — | — |

¹ `depth_conversion` is an integral part of `SEISMIC_FORWARD` and must be present in the config when running that
step. Since `RELATIVE_INVERSION` always runs after `SEISMIC_FORWARD` using the same config file, `depth_conversion`
will already be present.

² `seismic_inversion` has sensible defaults for all its parameters and does not need to be set explicitly. It can
be added to the config to tune the inversion parameters for a specific field.

A typical incremental workflow would be:

1. Add `seismic_fwd` and `depth_conversion` and run `SEISMIC_FORWARD` until it produces correct results.
2. Optionally add `seismic_inversion` to tune inversion parameters, then run `RELATIVE_INVERSION`.
3. Add `attribute_map_definition_file` and `webviz_map` and run `MAP_ATTRIBUTES`.
4. Run `OBSERVED_DATA`, which additionally requires `depth_conversion` (already present from step 1).

If a required section is missing when a forward model step is executed, a clear error message will indicate which
section must be added.
