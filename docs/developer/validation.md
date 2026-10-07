# Validation

The validation strategy combines independent small-system matrix references with exact short-time identities, normalization/unitarity checks, boundary tests and a long-time ballistic benchmark for the symmetric Hadamard walk.

C++ smoke tests exercise exact Hadamard steps, invalid coins and long bounded evolution. Python tests compare structured kernels against independently assembled dense unitaries on small line, square and cubic systems.

GitHub CI is configured for Ubuntu and Windows. A configured workflow is not itself evidence that a platform has passed; release status should be based on the workflow result for the exact commit.
