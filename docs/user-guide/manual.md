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


## Coins

For line walks, the built-in two-port coins are Hadamard and parameterized U(2). Grover, DFT/Fourier and identity coins work for any supported port dimension, so they can be used directly on square (4-port) and cubic (6-port) walks. Arbitrary unitary matrices remain available through `coin.type: custom`.

Examples are provided for Grover, DFT and identity coins in both `examples/square/` and `examples/cubic/`.

## Changing simulation parameters

Plots are generated from the HDF5 result, not directly from the current YAML file. If you change `simulation.steps`, `save_every`, the coin, the initial state, or another simulation parameter, rerun the simulation and write a new HDF5 file or use `--overwrite`. The plotter validates that the stored time axis ends at the step count recorded in the HDF5 configuration and rejects inconsistent/stale results.
