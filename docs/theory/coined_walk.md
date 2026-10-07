# Ordinary coined DTQW

For position space H_P and coin space H_C, MajiQwalK uses H = H_P tensor H_C. The implemented one-step convention is **coin then shift**,

U = S (I_P tensor C).

For spatial dimension n the structured Cartesian geometries use 2n directional ports ordered [-x,+x], [-x,+x,-y,+y], or [-x,+x,-y,+y,-z,+z].

The probability at site x is the sum of squared coin amplitudes. For a pure global state, the reduced coin density matrix is obtained by tracing over position; its von Neumann entropy is reported in bits when the coin-position entanglement observable is enabled.

Periodic and reflecting shifts are unitary permutations. An open boundary is treated as a finite computational window for an infinite-lattice walk: the engine raises an error rather than silently discarding amplitude that reaches the window edge.


# Classical counterpart

The first classical baseline is a nearest-neighbour Markov random walk on the same Cartesian geometry. If (p_a) is the probability of taking directional port (a), the site probability evolves by a stochastic transfer operator rather than a unitary coin-and-shift operator. The default is isotropic, (p_a=1/(2d)).

This baseline is intentionally separate from the quantum coin space. It supports direct comparisons of spreading laws: a symmetric classical line walk has variance proportional to (t), while the standard coherent Hadamard walk is ballistic with variance proportional to (t^2).

For reflecting classical boundaries, an attempted step through the boundary remains at the boundary site. Open boundaries are computational windows and raise an error before probability would leave the represented domain.
