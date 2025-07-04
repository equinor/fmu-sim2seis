# Why `sim2seis`?

FMU `sim2seis` (**sim**ulator to **seis**mic) workflow calculates seismic parameters and synthetic seismic, based on 
reservoir simulation results. Typical use cases are:

* Feasibility studies for 4D seismic
* History matching to 4D seismic data
* Assist interpretation of 4D seismic data

The following steps are typically done when calculating synthetic seismic from reservoir simulation results:

1. A field specific [petro-elastic model (PEM)](static-and-dynamic-input.md) is used to calculate elastic parameters   
   in each grid cell. Static and dynamic parameters from the geomodel and simulation model are inputs to the PEM.
1. [Synthetic seismic cubes](seismic-forward.md) are generated based on the input from the two steps above and a seismic wavelet.
1. [Depth-to-time conversion](./time-depth-conversion.md) is performed on the synthetic seismic cube to prepare for relative seismic inversion.
1. Optional: [relative seismic inversion](./relative-seismic-inversion.md) is run on the time-converted synthetic seismic cubes.
1. Time shift estimation is made, based on the synthetic seismic differences.
1. We can then extract different results like:
   * [attribute maps](./attribute-maps.md) from the synthetic seismic and relative seismic inversion. The list of possible attributes
     are found in [xtgeo.cubes](https://xtgeo.readthedocs.io/en/stable/api-cubes.html#xtgeo.Cube.compute_attributes_in_window)
   * time shift change maps

`sim2seis` settings are read from a `YAML ` file. The section links above will discuss the part of the YAML file that
controls the matching part in the `sim2seis` workflow. Lines in the configuration YAML file which are commented, 
indicate that there is a default value which is the preferred value, such as file names, directory names etc.

There are two related commands which are optional to the `sim2seis` workflow:
1. Observed data processing
2. 