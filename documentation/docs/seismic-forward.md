# Seismic forward modelling

The seismic forward modelling is based on a method developed by the Norwegian Computing Centre, sponsored by Equinor.
Full documentation is found here: [Seismic Forward - User manual](https://github.com/equinor/seismic-forward/blob/main/doc/Seismic_Forward_usermanual_ver_4.3.pdf)

`seismic-forward` runs are controlled by `XML` files. Multiple versions of synthetic seismic can be generated, e.g.
different angle stacks (`full`, `near`, `mid`, `far`), or angle gathers, both in time and depth. The most common 
use in `sim2seis` is to produce one or more angle stacks, commonly `full`, `near` and `far`. 

The resulting angle stacks will be compared to observed/acquired seismic data, and for this reason the parameters
in the `XML` files should be set to match the seismic acquisition and processing. 

## Yaml-file section
Default settings are normally sufficient for seismic forward modelling. [Figure 1](#figure-1-seismic-fwd-in-yaml) shows the `seismic-forward`-part
of the `sim2seis` configuration file.

```yaml
## Section for seismic forward 4D
#______________________________________________________________________________________________________________________#
seismic_fwd:
  # Comment out lines with full/near/far models if you don't want those stacks modelled
  # At least one line must be present
  stack_models:
    full: model_file.xml
#    near: model_file_near.xml
#    far: model_file_far.xml
#  stack_model_path: ../../sim2seis/model/seismic_forward/
#  attribute: &seismic_attribute amplitude
#  pem_output_dir: ../../sim2seis/output/pem
#  seismic_output_dir: ../../share/results/cubes
#  twt_model: ../../sim2seis/model/seismic_forward/model_file_twt.xml
#  segy_depth: syntseis_temp_seismic_depth_stack.segy
#  segy_time: syntseis_temp_seismic_timeshift_stack.segy  # <= not used anymore
#  pickle_file_prefix: seis_4d
```
<span id="figure-1-seismic-fwd-in-yaml"><strong>Figure 2:</strong> Parameters in the sim2seis configuration file related to seismic forward.</span>

## XML model files
An example `XML` file is shown in [Figure 2](#figure-2-example-xml-file) below. In the following paragraphs, some
of the most common XML tags are discussed. These are the ones that are likely to be edited to match the case. Sections
in the XML file that are commented out show alternatives that are normally not used.

```xml
<seismic-forward>
   <elastic-param>
     #grid with exported PEM parameters:
     <eclipse-file>../../sim2seis/output/pem/pem.grdecl</eclipse-file>

     # parameters in overburden (top), underburden (bot) and inactive cells (mid):
     <default-values>
       <vp-top>2000</vp-top>
       <vp-mid>2240</vp-mid>
       <vp-bot>3000</vp-bot>
       <vs-top>1100</vs-top>
       <vs-mid>890</vs-mid>
       <vs-bot>890</vs-bot>
       <rho-top>2300</rho-top>
       <rho-mid>2240</rho-mid>
       <rho-bot>2240</rho-bot>
     </default-values>

     # names of parameters to use from .grdecl file:
     <parameter-names>
       <vp>VP</vp>
       <vs>VS</vs>
       <rho>DENS</rho>
     </parameter-names>

     # type of interpolation to use ++:
     <cornerpt-interpolation-in-depth>no</cornerpt-interpolation-in-depth>
     <zero-thickness-limit>0.1</zero-thickness-limit>
     <remove-negative-delta-z>yes</remove-negative-delta-z>
     <vertical-interpolation-of-undefined-cells>yes</vertical-interpolation-of-undefined-cells>
     <fixed-triangularization-of-eclipse-grid>no</fixed-triangularization-of-eclipse-grid>
   </elastic-param>

   # incident angle that are modelled. Here modelled 0 offset:
   #<angle>
   #  <theta-0>0</theta-0>
   #  <dtheta>0</dtheta>
   #  <theta-max>0</theta-max>
   #</angle>

   # modeling gather with nmo stretch:
   <nmo-stretch>
     <seafloor-depth>150</seafloor-depth>
     <velocity-water>1500</velocity-water>
     <offset>
       <offset-0>0</offset-0>
       <doffset>200</doffset>
       <offset-max>1000</offset-max>
     </offset>
   </nmo-stretch>

   # Wavelet used for modelling (here a Ricker is used)
   # A wavelet ca be used, see user manual
   <wavelet>
     <ricker>
       <peak-frequency>30</peak-frequency>
     </ricker>
     <scale>1</scale>
   </wavelet>

   # Add white noise to the seismic data
   <white-noise>
        <standard-deviation>0.0015</standard-deviation>
   </white-noise>

   # Definition of output grid.
   # A timesurface for top of the grid is needed to create seismic in time. Else, use a constant
   # A segy cube can be used as areal layout.
   <output-grid>
     <top-time>
       #<top-time-constant>0</top-time-constant>
       <top-time-surface>../../sim2seis/input/seismic_forward/TopVolantis.txt</top-time-surface>
     </top-time>
     <area-from-segy>
      <filename>../../sim2seis/input/seismic_forward/seismiclayout.segy</filename>
     </area-from-segy>
     <cell-size>
       #<dx>50</dx>
       #<dy>50</dy>
       <dz>4</dz>
       <dt>4</dt>
     </cell-size>
     <depth-window>
       <top>1500</top>
       <bot>2000</bot>
     </depth-window>
     <time-window>
       <top>1500</top>
       <bot>2000</bot>
     </time-window>
     <utm-precision>0.01</utm-precision>
   </output-grid>

   # Specification of output data
   <output-parameters>
     <prefix>../../share/results/cubes/syntseis_temp</prefix>
     <seismic-time-segy>no</seismic-time-segy>  # gathers
     <seismic-depth-segy>no</seismic-depth-segy> # gathers
     <twt>no</twt>
     <seismic-timeshift-segy>no</seismic-timeshift-segy> # timeshifted gathers
     <seismic-stack>
       <timeshift-segy>yes</timeshift-segy> # timeshifted stacked seismic to timeshift-twt
       <depth-segy>yes</depth-segy>      # stacked seismic
     </seismic-stack>
     <elastic-parameters-depth-segy>no</elastic-parameters-depth-segy>
     <elastic-parameters-time-segy>no</elastic-parameters-time-segy>
   </output-parameters>
   # This will import twt from base survey, and use this as twt also for monitor
   <timeshift-twt>../../share/results/cubes/syntseis_base_twt.storm</timeshift-twt>

   <project-settings>
      # number of threads/cpu. Set to 1 when running in batch
      <max-threads>1</max-threads>
   </project-settings>
</seismic-forward>
```
<span id="figure-2-example-xml-file"><strong>Figure 2:</strong> Example XML file for full stack synthetic seismic in depth domain.</span>

### 1. Default values
As the geomodel and reservoir simulator model are likely to cover the reservoir section only, we need to define 
background values for Vp, Vs and density (&rho). *Top* means above the reservoir, *mid* within the reservoir and *bot* 
below the reservoir. To estimate the seismic response, we need to know the contrast in the elastic properties, and it 
is not correct to assume that they are zero outside the reservoir, hence the need for background/default values.

To estimate the correct set of default values, Vp, Vs and &rho logs from available wells should be studied, and average
values to the top, mid and bottom intervals calculated.

### Angle / nmo-stretch
Normal moveout (*nmo*) stretch compensates for the fact that seismic travel time increases offset between seismic
source and receiver. We wish to have this compensated both in angle gather displays and for stacked seismic cubes. To
generate cubes without estimation and correction of nmo-stretch, *angle* option is used instead. Nmo-stretch option will
have priority over angle option.

In the **Drogon** case, we have used nmo-stretch for full stack and angle for near and far partial stacks.

### Wavelet
Wavelet can either be a Ricker wavelet with a given peak frequency, or else an estimated wavelet, which is read from
a file. Only Landmark ASCII wavelet format is supported for file input. `<scale>` should be used to match the dynamic
range in the observed seismic data. In the case that a Ricker wavelet is used, the peak frequency should be set to
match the frequency content of the observed seismic data.

### Noise
There are two options for modelling noise in the synthetic seismic data: white noise added to the seismic data, or 
white noise added to the reflection coefficients. In both cases a standard deviation of the noise distribution must
be set. Option `<white-noise>` adds the noise to the seismic data, `<add-noise-to-refl-coef>` adds the noise to the 
reflection coefficients. It is recommended to use the `<white-noise>` option.

### Output grid
Much of the settings for the output grid is possible to read from the simulation grid and a template `segy`file. Other
settings should be fairly self-explanatory.

### Output parameters
Most of the parameters for this section should be kept at default values, as that is expected by the `sim2seis` 
workflow.

### Timeshift TWT
There is a separate run of `seismic-forward` which estimates the TWT of the base grid as a function of depth. This run
is controlled by the XML-file *model_file_twt.xml*. The parameter setting in this file should be harmonized with the
ones that are used to generate the angle stacks.