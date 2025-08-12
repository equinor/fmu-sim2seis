# Relative seismic inversion

If seismic inversion data is available for the observed seismics, inversion should also be performed
on the generated synthetic seismic data. A method previously named `simpli` (now `si4ti`) is used. This is a relative 
seismic inversion method, meaning that there is no need for a low-frequency model.

Further documentation of the method can be found on the [GitHub homepage](https://github.com/equinor/si4ti/tree/main/doc) 
of `si4ti`.

## YAML file section
As shown in [Figure 1](#figure-1-seismic-inversion-in-yaml) below, all parameters controlling the relative
seismic inversion have default values. However, revisiting these parameters may be beneficial, as they influence the inversion 
results by controlling the smoothness of the results in both lateral and vertical directions, as well as between 
seismic vintages.

<<< ../../tests/data/sim2seis/model/sim2seis_config.yml#seismic_inversion{yml}
<span id="figure-1-seismic-inversion-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic inversion.</span>
