# Why `sim2seis`?

FMU `sim2seis` (**sim**ulator to **seis**mic) workflow calculates seismic parameters and synthetic seismic, based on reservoir simulation results. Typical use cases are:

* Feasibility studies for 4D seismic
* History matching to 4D seismic data
* Assist interpretation of 4D seismic data

The following steps are typically done when calculating synthetic seismic from reservoir simulation results:

1. Static and dynamic parameters in each grid cell in the simulation model are read.
1. A field specific petro elastic model is used to calculate seismic parameters in each grid cell.
1. Synthetic seismic cubes are generated based on the input from the two steps above.
1. Time shift estimation is made, based on the synthetic seismic differences.
1. We can then extract different results like:
   * attribute maps from the synthetic seismic
   * average maps from the elastic parameters ($V_{\rm P}$, $\rho_{\rm B}$, acoustic impedance, time shift)
   * time shift change maps

