# QC of `sim2seis` modelling

QC should include:
- Value range of results. If there are grids, cubes, or attribute maps with unreasonable values, this may indicate
  that an input has been provided with an unexpected unit (it is generally assumed that all inputs use SI units).
- `pem` can be configured to save intermediate results, such as effective mineral and fluid properties. These represent
  the initial step in the process and can serve as the first point of verification.
- Inputs should also be validated, i.e., the `eclipse` `.INIT` and `.UNRST` files, as well as volume fraction grids
  from the geomodel. For example, low-pressure outliers in `eclipse` runs can lead to errors in fluid property
  estimation.
- Comparison between the primary influencing factors of 4D response, i.e., changes in pressure and saturation, correlated
  to the seismic amplitude or relative acoustic impedance response.

The documentation for `pem` provides more detailed information on the process of calibrating rock physics models. Much of the workflow
in `sim2seis` is less dependent on parameter settings, except for the Seismic Forward modelling component. It is important
to understand the settings in the XML model files and conduct tests to optimise parameters.

There are several options available for QC of results from `sim2seis`, and the workflow is not restricted to any
specific application. Earlier versions of `sim2seis` were an integrated part of `RMS` &copy; Aspen Tech.