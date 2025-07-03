# Relative seismic inversion

If seismic inversion data is available for the observed seismics, seismic inversion should also be performed
on the generated synthetic seismic data. A method earlier named `simpli` (now `si4ti` is used, this is a relative 
seismic inversion method, meaning that there is no need for a low-frequency model.

More documentation of the method is found on the [GitHub homepage](https://github.com/equinor/si4ti/tree/main/doc) 
of `si4ti`.

## Yaml-file section
As seen in [Figure 1](#figure-1-seismic-inversion-in-yaml) below, all of the parameters controlling the relative
seismic inversion have default values. However, the inversion parameters can be worth revisiting. They will affect 
the inversion results by controlling smoothness of the results, both in lateral and vertical direction, and also 
between seismic vintages. 

```yaml
## Section for relative seismic inversion
#______________________________________________________________________________________________________________________#
# seismic_inversion:
#  attribute: &inversion_attribute relai
#  path: &rel_ai_path ../../share/results/cubes
#  domain: [time]
#  d_syn_0: ../../sim2seis/output/seismic_forward/syntseis--d_syn0.sgy
#  rel_ai_0: ../../sim2seis/output/seismic_forward/syntseis--relai_0.sgy
#  d_syn_1: ../../sim2seis/output/seismic_forward/syntseis--d_syn1.sgy
#  rel_ai_1: ../../sim2seis/output/seismic_forward/syntseis--relai_1.sgy
#  remove_unused_files: True
#  inversion_params:
#      lateral_smoothing_4d: 0.05
#      damping_3d: 0.001
#      damping_4d: 0.001
#      lateral_smoothing_3d:  0.01
#      max_iter: 100
#      segments: 1
#  pickle_file_prefix: relai_diff
```
<span id="figure-1-seismic-inversion-in-yaml"><strong>Figure 1:</strong> Parameters in the sim2seis configuration file related to seismic inversion.</span>
