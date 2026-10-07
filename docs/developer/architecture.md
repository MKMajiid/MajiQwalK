# Architecture

MajiQwalK separates the C++20 numerical core from the Python configuration, I/O and plotting layers.

The core abstractions are organized around position/geometry, coin space, operation/evolution, state representation, backend and observables. Structured line/square/cubic geometries use direct kernels rather than dense global walk matrices.

The public architecture reserves both state-vector and density-matrix representations. The present milestone implements state-vector evolution. Density-matrix evolution, channels, CUDA, arbitrary graphs and additional walk families are later milestones and must not be presented as implemented until tests exist.

Python provides strict YAML validation, HDF5 streaming, the CLI and plotting. C++ owns the performance-sensitive coin/shift evolution and validates numerical invariants at the binding boundary.
