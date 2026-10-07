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


## Classical random-walk counterparts

Set `model.type: classical_random_walk`. Classical runs use a position probability distribution rather than amplitudes or a coin space. The default transition rule is isotropic over the directional ports; specify `classical.step_probabilities` in port order for a biased walk. For example, on a line `[0.3, 0.7]` means left/right probabilities of 0.3 and 0.7.

Classical and quantum results share HDF5 probability, moment, variance, time-axis and plotting conventions. Quantum-only observables such as coin-position entanglement are rejected for classical models.

The current classical model is memoryless (Markovian) nearest-neighbour transport. Persistent/coin-memory classical walks are a later extension.


## Persistent classical walks

Use `classical.type: persistent` to retain a directional memory state. With `persistence: r`, the probability of keeping the same direction is (r); the remaining probability is distributed uniformly among the other directional ports. For full control, supply `classical.transition_matrix`, using rows for the next direction and columns for the previous direction. Every column must sum to one.

## Transport comparison

`majiqwalk compare first.h5 second.h5` requires identical geometry, origin, and sampled steps. It produces final probability (or x-marginal), total variance, and RMS-displacement comparisons. `majiqwalk transport result.h5` performs a log-log fit of total variance over the later fraction of available positive-time samples. The resulting exponent is a finite-time diagnostic; it should not be interpreted automatically as an asymptotic transport exponent.
