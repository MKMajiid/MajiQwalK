# Architecture

MajiQwalK separates the C++20 numerical core from the Python configuration, I/O and plotting layers.

The core abstractions are organized around position/geometry, coin space, operation/evolution, state representation, backend and observables. Structured line/square/cubic geometries use direct kernels rather than dense global walk matrices.

The public architecture reserves both state-vector and density-matrix representations. The present milestone implements state-vector evolution. Density-matrix evolution, channels, CUDA, arbitrary graphs and additional walk families are later milestones and must not be presented as implemented until tests exist.

Python provides strict YAML validation, HDF5 streaming, the CLI and plotting. C++ owns the performance-sensitive coin/shift evolution and validates numerical invariants at the binding boundary.


## Classical engine

Classical random walks are represented as a separate stochastic engine with a normalized site-probability vector. They reuse the Cartesian geometry and directional-port ordering but do not pass through the quantum coin/state abstractions. This separation prevents accidental interpretation of stochastic mixing as unitary dynamics while allowing common observables, HDF5 output and plotting.
