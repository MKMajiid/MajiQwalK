# MajiQwalK user guide

MajiQwalK is configured with YAML and writes scientific results primarily to HDF5.

## Basic workflow

```bash
majiqwalk validate examples/line/hadamard.yaml
majiqwalk run examples/line/hadamard.yaml
majiqwalk inspect examples/line/line_hadamard.h5
majiqwalk plot examples/line/line_hadamard.h5 --directory figures
```

The implemented geometries are line, square and simple cubic. Boundaries are open-window, periodic and reflecting. Current executable evolution uses pure state vectors; density-matrix execution is reserved by the architecture but is not yet implemented.

Output paths declared in YAML are resolved relative to the configuration file. Existing HDF5 output is preserved unless overwrite is explicitly enabled.
