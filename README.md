# MajiQwalK

**A modular discrete-time quantum-walk package with a C++20 numerical core and a Python API and command line.**

Author: **Majid Moradi Kelardeh**, Pavol Jozef Šafárik University in Košice.
[Academic page](https://mkmajiid.github.io) · [ORCID](https://orcid.org/0000-0001-9479-2042).

Version **0.1.0.dev3** prepares the first executable milestone for publication, with Windows OpenMP compatibility and reproducible archive timestamps. It is not a stable production release or a package already published on PyPI. The development source archive requires Python and a C++20 compiler. The self-contained Windows/Linux release workflow is provided separately and needs target-platform release validation.

## Implemented

- Ordinary coined evolution, **coin then shift**, on line, square and simple-cubic lattices.
- General custom unitary coins; Hadamard and parameterized U(2) for two-port walks, plus Grover, DFT/Fourier and identity coins for arbitrary port dimension.
- Localized, distributed product and arbitrary full pure initial states.
- Explicit open-window, periodic and reflecting boundaries.
- Complex double precision; CPU propagation and optional OpenMP coin processing.
- Strict, versioned YAML configuration with numerical physics checks and JSON schema.
- Streaming HDF5 output: probabilities, raw moments, variances, norm, reduced coin state, coin-position entropy, optional state snapshots and finite-time averaged probabilities.
- Python API, `majiqwalk` CLI, CSV probability export and a Physical Review figure profile.
- Independent small-system matrix references, exact short-time checks and a ballistic asymptotic benchmark.

Density-matrix execution, channels, CUDA, split-step, accelerating, memory, Möbius walks, arbitrary graphs, sphere meshes, FI/QFIM and Uhlmann curvature are **planned extensions**. They are not advertised as executable features. See [roadmap](docs/developer/roadmap.md).

## Install from this source

Linux: install Python 3.10 or later and a C++20 compiler (for example `g++` from your distribution). Use an isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[plot]"
```

Windows source builds require Visual Studio C++ Build Tools with C++20 support. Activate the virtual environment with `.venv\Scripts\activate`, then run the same pip install. Pip obtains CMake, pybind11 and other build dependencies automatically. OpenMP is enabled when the compiler provides it; otherwise the serial backend works.

## First run

From the repository directory:

```bash
majiqwalk validate examples/line/hadamard.yaml
majiqwalk run examples/line/hadamard.yaml
majiqwalk inspect examples/line/line_hadamard.h5
majiqwalk plot examples/line/line_hadamard.h5 --directory figures
majiqwalk export examples/line/line_hadamard.h5 --output probability.csv
```

`majiqwalk examples/line/hadamard.yaml` is also accepted. `python -m majiqwalk` provides the same commands. CLI output paths from YAML are relative to the configuration file; `--output` is relative to the current working directory. Existing HDF5 results are preserved unless `--overwrite` or `output.overwrite: true` is set.

Shipped examples include line Hadamard/custom walks and Grover, DFT/Fourier and identity coins for both square and cubic walks. Output files use `<geometry>_<coin>.h5` (for example `square_dft.h5` or `cubic_identity.h5`). These names are
explicitly configured in `output.file`; the engine does not choose a name from
the coin or geometry. The HDF5 extension is `.h5`.

Python:

```python
from majiqwalk import Config, Simulation

config = Config.from_yaml("examples/line/hadamard.yaml")
result = Simulation(config).run("my_run.h5")
final_probability = result.read("observables/probability", -1)
steps = result.steps
```

The Python API resolves its output path relative to the current working directory. Reading `result.probability` loads the full sampled distribution history; use `result.read(dataset, selection)` for large results. After changing YAML parameters such as `simulation.steps`, rerun the simulation with a new output filename or `--overwrite` before plotting; the plotter rejects stale/inconsistent HDF5 data.

## Manuals and conventions

- [User guide](docs/user-guide/manual.md): configuration, runs, outputs and plotting.
- [Theory](docs/theory/coined_walk.md): Hilbert space, coins, shift, entanglement and averaging.
- [Architecture](docs/developer/architecture.md): C++ contracts, Python responsibilities and extension points.
- [Roadmap](docs/developer/roadmap.md): implemented features and future milestones.
- [Scientific references](docs/references/references.md).
- [Validation](docs/developer/validation.md).

The amplitude index is `site * coin_dimension + port`. Ports are `[-x,+x]`, `[-x,+x,-y,+y]`, or `[-x,+x,-y,+y,-z,+z]`. Spatial coordinates use C ordering. All angles are in radians. Entropy is in **bits**.

## Development checks

```bash
python -m pip install ".[dev]"
python -m pytest -q
cmake -S . -B build/cpp -DMAJIQWALK_BUILD_PYTHON=OFF -DMAJIQWALK_BUILD_TESTS=ON
cmake --build build/cpp --config Release
ctest --test-dir build/cpp -C Release --output-on-failure
python -m build
```

Configuration schema regeneration:

```bash
majiqwalk schema > schemas/config-v1.json
```

## License and citation

MajiQwalK is licensed under **Apache-2.0**; see [LICENSE](LICENSE) and [NOTICE](NOTICE). Citation metadata is in [CITATION.cff](CITATION.cff). There is no MajiQwalK paper or Zenodo DOI yet; do not cite an invented DOI. For a scientific publication, record the exact software version and cite the literature defining the walk you use. A release DOI and associated methods paper can be added later.

## GitHub and academic page

The public source repository is [MKMajiid/MajiQwalK](https://github.com/MKMajiid/MajiQwalK). Version `0.1.0.dev3` is a development milestone; create the first tagged pre-release only after the Linux/Windows CI matrix and portable-build validation pass for the exact release commit. See the [publication steps](docs/developer/publishing.md).
