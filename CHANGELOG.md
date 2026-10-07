# Changelog

## 0.1.0.dev5 — transport comparison and persistent classical walks

Added quantum/classical comparison plots for final probability, total variance and RMS displacement; finite-time transport-scaling diagnostics; and persistent classical random walks with either scalar persistence or a user-defined column-stochastic directional transition matrix. Added repository-logo integration.

## 0.1.0.dev4 — classical baselines and multidimensional coins

Added a separate classical nearest-neighbour random-walk engine with isotropic or user-defined directional probabilities, shared HDF5 observables and plotting, and line/square/cubic examples. Added square tensor-Hadamard and multidimensional axis-Hadamard coins. Plotting now rejects stale HDF5 results whose stored sample axis disagrees with the embedded configuration.

## 0.1.0.dev3 — publication preparation

Use a signed OpenMP loop index for MSVC, with range validation. Add reusable
source and portable archive scripts that preserve executable permissions and
normalize ZIP dates. Portable builds now test all four examples and their
PDF/SVG/PNG plots, collect the Windows CPython license when present, and run
the Python scientific suite before packaging in CI. Prepare development release
notes and an academic-page software entry; publication is still pending.

## 0.1.0.dev2 — project name and example outputs

Renamed the public project to MajiQwalK, preserving the `majiqwalk` command,
Python module and distribution name. Standardized example HDF5 filenames as
`<geometry>_<coin>.h5`: line_hadamard, line_custom, square_grover and cubic_grover.
Updated installation/plotting instructions and both downloadable archives.
Source archive timestamps are normalized to avoid future-date Ninja loops.

## 0.1.0.dev1 — first executable milestone

Implemented the C++20 state-vector engine, modular operation sequence, Cartesian
port geometry, Python bindings, strict YAML schema, HDF5 observable pipeline,
CLI, CSV export, APS figure profile, examples, manuals and scientific tests.

Density-matrix storage and operation contracts exist at the C++ architecture
level; density-matrix evolution and CUDA are not implemented.
