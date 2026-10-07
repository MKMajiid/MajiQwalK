# Ordinary coined DTQW

For position space H_P and coin space H_C, MajiQwalK uses H = H_P tensor H_C. The implemented one-step convention is **coin then shift**,

U = S (I_P tensor C).

For spatial dimension n the structured Cartesian geometries use 2n directional ports ordered [-x,+x], [-x,+x,-y,+y], or [-x,+x,-y,+y,-z,+z].

The probability at site x is the sum of squared coin amplitudes. For a pure global state, the reduced coin density matrix is obtained by tracing over position; its von Neumann entropy is reported in bits when the coin-position entanglement observable is enabled.

Periodic and reflecting shifts are unitary permutations. An open boundary is treated as a finite computational window for an infinite-lattice walk: the engine raises an error rather than silently discarding amplitude that reaches the window edge.
