# Relative seismic inversion

If seismic inversion data is available for the observed seismics, inversion should also be performed
on the generated synthetic seismic data. A method previously named `simpli` (now `si4ti`) is used. This is a relative
seismic inversion method, meaning that there is no need for a low-frequency model.

Further documentation of the method can be found on the [GitHub homepage](https://github.com/equinor/si4ti/tree/main/doc)
of `si4ti`.

## YAML file section

As shown in [Figure 1](#figure-1-seismic-inversion-in-yaml) below, all parameters controlling the relative
seismic inversion have default values. However, revisiting these parameters may be beneficial, as they influence the
inversion results by controlling the smoothness of the results in both lateral and vertical directions, as well as
between seismic vintages.

```yaml
########################################################################################################################
#
# Seismic inversion settings
#
# It is possible to run seismic inversion by using the default values, but for better match to observed data inversion,
# the inversion parameter settings should be modified
#
########################################################################################################################
# seismic_inversion:
#  attribute: relai
#  domain: time
#  d_syn_0: ../../sim2seis/output/seismic_forward/seismic--d_syn0.sgy
#  rel_ai_0: ../../sim2seis/output/seismic_forward/seismic--relai_0.sgy
#  d_syn_1: ../../sim2seis/output/seismic_forward/seismic--d_syn1.sgy
#  rel_ai_1: ../../sim2seis/output/seismic_forward/seismic--relai_1.sgy
#  inversion_params:
#      lateral_smoothing_4d: 0.05
#      damping_3d: 0.001
#      damping_4d: 0.001
#      lateral_smoothing_3d:  0.01
#      max_iter: 100
#      segments: 1
```

<span id="figure-1-seismic-inversion-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic inversion.</span>
