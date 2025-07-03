# Static and dynamic input

`sim2seis` is one step in a multi-disciplinary workflow, and the intention is to tie it together with the models
used for static and dynamic properties, i.e. the geo-model and the reservoir simulator. Static and dynamic parameters
are input to the `pem`, i.e. the petro-elastic model. All of this is documented in detail in 
[fmu-pem](https://equinor.github.io/fmu-pem/).

## Yaml-file
There is no section for the `pem` in the yaml-file for `sim2seis`, as there is a dedicated yaml-file for the `pem`. 
