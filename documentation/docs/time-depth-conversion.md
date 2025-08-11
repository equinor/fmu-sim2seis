# Domain Conversion Between Time and Depth

Domain conversion between time and depth is essential for comparing observed seismic data (typically in time) with
synthetic seismic data (which can be in time or depth) and geomodels or simulation models (in depth). The time-to-depth
or depth-to-time conversion is performed using a simplified approach, with a velocity model calculated from matching
pairs of time and depth surfaces.

It is generally unnecessary for a `sim2seis` user to modify any code for domain conversion, as it is integrated into the
scripts. Examples of code usage are provided in
the [fmu-tools documentation](https://equinor.github.io/fmu-tools/domain_conversion.html).

## YAML File Section

Several parameters are required to control the domain conversion. [Figure 1](#figure-1-domain-conversion-in-yaml)
illustrates the domain conversion section of the `sim2seis` configuration file. Horizon names and limits for the
generated cubes in time and depth must be specified. Horizon file names are expected to be lowercase versions of the
horizon names, with a postfix of `--time.gri` or `--depth.gri`, depending on the domain.

Depth parameters are specified in units of `m`, while time parameters are in units of `ms`.

<<< ../../tests/data/sim2seis/model/sim2seis_config.yml#depth_conversion{yml}
<span id="figure-1-domain-conversion-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic forward.</span>
