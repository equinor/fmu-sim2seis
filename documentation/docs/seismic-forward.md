# Seismic Forward Modelling

The seismic forward modelling is based on a method developed by the Norwegian Computing Centre, sponsored by Equinor.
Full documentation can found here: [Seismic Forward - User manual](https://github.com/equinor/seismic-forward/blob/main/doc/Seismic_Forward_usermanual_ver_4.3.pdf)

`seismic-forward` runs are controlled by `XML` files. Multiple versions of synthetic seismic can be generated, such as
different angle stacks (`full`, `near`, `mid`, `far`), or angle gathers, both in time and depth domain. The most common 
use in `sim2seis` is to produce one or more angle stacks, commonly `full`, `near` and/or `far`. 

The resulting angle stacks are compared to observed/acquired seismic data, and for this reason the parameters
in the `XML` files should be set to match the seismic acquisition and processing. 

## Yaml File Section
Default settings are usually sufficient for seismic forward modelling. [Figure 1](#figure-1-seismic-fwd-in-yaml) shows the `seismic-forward`-part
of the `sim2seis` configuration file.

<<< ../../tests/data/sim2seis/model/sim2seis_config.yml#snip_seis_fwd{yml}
<span id="figure-1-seismic-fwd-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic forward.</span>

## XML Model Files
An example `XML` file is shown in [Figure 2](#figure-2-example-xml-file) below. The following paragraphs discuss, some
of the most common XML tags, which are likely to be edited to match the case. Sections
in the XML file that are commented out show alternatives that are normally not altered.

<<< ../../tests/data/sim2seis/model/model_file.xml{xml}
<span id="figure-2-example-xml-file"><strong>Figure 2:</strong> Example XML file for full stack synthetic seismic in depth domain.</span>

### Default Values
As the geomodel and reservoir simulator model are likely to cover the reservoir section only, background values 
for Vp, Vs and density (&rho) need to be defined. *Top* refers to the interval above the reservoir, *mid* within the 
reservoir and *bot* below the reservoir. To estimate the seismic response, it is required to know the contrast in 
elastic properties. It is not correct to assume that these values are zero outside the reservoir, hence the need for 
background/default values.

To estimate the correct set of default values, Vp, Vs and &rho logs from available wells should be studied, and average
values to the top, mid and bottom intervals calculated.

### Angle / NMO Stretch
Normal moveout (*nmo*) stretch compensates for the increase in seismic travel time with offset between seismic
source and receiver. This compensation is applied both in angle gather displays and for stacked seismic cubes. To
generate cubes without estimation and correction of nmo-stretch, *angle* option is used instead. The nmo-stretch option
takes precedence over the angle option.

In the **Drogon** case, *nmo-stretch* is used for the full stack and *angle* for near and far partial stacks.

### Wavelet
The wavelet can either be a Ricker wavelet with a specified peak frequency, or an estimated wavelet read from
a file. Only Landmark ASCII wavelet format is supported for file input. `<scale>` should be used to match the dynamic
range of the observed seismic data. If a Ricker wavelet is used, the peak frequency should be set to
match the frequency content of the observed seismic data.

### Noise
There are two options for modelling noise in the synthetic seismic data: white noise added to the seismic data or 
white noise added to the reflection coefficients. In both cases, the standard deviation of the noise distribution must
be specified. The `<white-noise>` option adds noise to the seismic data, while `<add-noise-to-refl-coef>` adds the 
noise to the reflection coefficients. It is recommended to use the `<white-noise>` option.

### Output Grid
Most settings for the output grid can be read from the simulation grid and a template segy file. Other settings should 
be fairly self-explanatory.

### Output Parameters
Most parameters in this section should remain at their default values, as these are expected by the sim2seis workflow.

### Timeshift TWT
A separate run of `seismic-forward` estimates the TWT of the base grid as a function of depth. This run
is controlled by the XML file *model_file_twt.xml*. The parameter setting in this file should be harmonised with those
used to generate the angle stacks.