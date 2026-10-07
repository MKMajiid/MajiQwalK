"""Execute the validated specification and stream sampled observables to HDF5."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import os
from pathlib import Path
import platform
import tempfile

import h5py
import numpy as np

from .config import Config
from .io import Results
from . import _core
from ._version import __version__


def coin_entropy(rho):
    """Pure global-state coin-position von Neumann entropy, in bits."""
    eigenvalues = np.linalg.eigvalsh(rho)
    if np.min(eigenvalues) < -1e-10:
        raise RuntimeError("Reduced coin state is not positive semidefinite")
    eigenvalues = np.clip(eigenvalues, 0, 1)
    positive = eigenvalues[eigenvalues > 0]
    return float(-np.sum(positive * np.log2(positive)))


class Simulation:
    def __init__(self, config: Config):
        self.config = Config.model_validate(config.model_dump())

    def run(self, output=None, *, overwrite=None):
        config = self.config
        if config.simulation.representation != "state_vector":
            raise NotImplementedError("Density matrices are reserved in schema v1; execution is planned for a later milestone")
        shape = config.geometry.shape
        sites, d = math.prod(shape), 2*len(shape)
        # Conservative peak-working-memory estimate, including conversion copies,
        # both shift maps, coordinate/moment buffers and single-sample HDF5 chunks.
        estimate = 128*sites*d + 64*sites*len(shape) + 16*d*d
        if estimate > config.simulation.max_memory_mib * 2**20:
            raise MemoryError(f"Estimated working memory {estimate/2**20:.1f} MiB exceeds simulation.max_memory_mib")
        path = Path(output or config.output.file).resolve()
        replace = config.output.overwrite if overwrite is None else overwrite
        if path.exists() and not replace:
            raise FileExistsError(f"Output already exists: {path}; set output.overwrite or use --overwrite")
        path.parent.mkdir(parents=True, exist_ok=True)
        requested_threads = config.backend.threads
        threads = _core.max_threads() if requested_threads == "auto" else requested_threads
        engine = _core.Engine(shape, config.geometry.boundary, config.coin.array(d),
                              config.initial_state.array(shape, d), threads)
        fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            with h5py.File(temporary, "w") as file:
                self._write(file, engine, threads, path)
            # Atomic no-clobber publication where possible, including competing
            # writers; overwrite is explicit and also atomically replaces.
            if replace:
                os.replace(temporary, path)
            else:
                os.link(temporary, path)
                temporary.unlink()
        finally:
            temporary.unlink(missing_ok=True)
        return Results(path)

    def _write(self, file, engine, threads, output_path):
        config = self.config
        shape = tuple(config.geometry.shape)
        d = 2*len(shape)
        kinds = {o.type for o in config.observables}
        stride, final = config.simulation.save_every, config.simulation.steps
        sample_steps = list(range(0, final+1, stride))
        if sample_steps[-1] != final:
            sample_steps.append(final)
        n = len(sample_steps)
        metadata = file.create_group("metadata")
        metadata.attrs.update(majiqwalk_version=__version__, schema_version=1, output_schema_version=1,
                              timestamp=datetime.now(timezone.utc).isoformat(), backend="cpu",
                              threads=threads, openmp_enabled=_core.openmp_enabled(),
                              python_version=platform.python_version(), numpy_version=np.__version__,
                              h5py_version=h5py.__version__, representation="state_vector",
                              actual_output_path=str(output_path),
                              git_commit=os.environ.get("MAJIQWALK_GIT_COMMIT", "unknown"))
        file.create_dataset("config/yaml", data=config.to_yaml(), dtype=h5py.string_dtype())
        file.create_dataset("steps", data=sample_steps, dtype="i8")
        geometry = file.create_group("geometry")
        geometry.attrs.update(type=config.geometry.type, boundary=config.geometry.boundary,
                              port_order=",".join(p for axis in "xyz"[:len(shape)] for p in (f"-{axis}", f"+{axis}")),
                              flattening="C: last spatial axis fastest; coin index fastest overall")
        geometry.create_dataset("shape", data=shape)
        geometry.create_dataset("origin", data=config.geometry.origin)
        coordinates = np.indices(shape, dtype=float).reshape(len(shape), -1).T
        coordinates -= np.asarray(config.geometry.origin)
        geometry.create_dataset("coordinates", data=coordinates)
        datasets = {}

        def dataset(name, trailing, dtype="f8"):
            datasets[name] = file.create_dataset(name, shape=(n, *trailing), dtype=dtype,
                                                 compression="gzip", compression_opts=4, chunks=True)
            return datasets[name]

        dataset("observables/norm", ())
        if "probability" in kinds:
            dataset("observables/probability", shape)
        if "time_average_probability" in kinds:
            ds = dataset("observables/time_average_probability", shape)
            ds.attrs["definition"] = "(1/(t+1)) sum_{s=0}^t P(x,s); finite-time Cesaro average, not a proven limiting distribution"
        orders = next((o.orders for o in config.observables if o.type == "moments"), None)
        if orders:
            ds = dataset("observables/moments", (len(shape), len(orders)))
            ds.attrs.update(orders=orders, definition="raw Cartesian moments about geometry.origin")
            dataset("observables/variance", (len(shape),))
        if "coin_position_entanglement" in kinds:
            ds = dataset("observables/entanglement/coin_position_entropy", ())
            ds.attrs.update(units="bits", definition="von Neumann entropy of the coin reduction of the pure global state")
            dataset("observables/entanglement/linear_entropy", ())
            dataset("observables/entanglement/reduced_coin_density_matrix", (d,d), "c16")
        if config.output.save_state:
            dataset("states/snapshots", (*shape, d), "c16")
        average_sum = np.zeros(math.prod(shape)) if "time_average_probability" in kinds else None
        previous_step = -1
        for row, step in enumerate(sample_steps):
            if average_sum is not None:
                for current in range(previous_step+1, step+1):
                    if current > 0:
                        engine.advance(1)
                    average_sum += engine.probability()
            else:
                engine.advance(step-engine.step)
            previous_step = step
            norm = engine.norm()
            if not np.isfinite(norm) or abs(norm-1) > 1e-9:
                raise RuntimeError(f"Normalization failed at step {step}: {norm}")
            datasets["observables/norm"][row] = norm
            if "probability" in kinds or orders:
                probability = engine.probability()
            if "probability" in kinds:
                datasets["observables/probability"][row] = probability.reshape(shape)
            if average_sum is not None:
                datasets["observables/time_average_probability"][row] = (average_sum/(step+1)).reshape(shape)
            if orders:
                moments = np.stack([probability @ (coordinates**order) for order in orders], axis=-1)
                mean = probability @ coordinates
                variance = probability @ (coordinates**2) - mean**2
                datasets["observables/moments"][row] = moments
                datasets["observables/variance"][row] = np.maximum(variance, 0)
            if "coin_position_entanglement" in kinds:
                rho = engine.reduced_coin()
                datasets["observables/entanglement/coin_position_entropy"][row] = coin_entropy(rho)
                datasets["observables/entanglement/linear_entropy"][row] = max(0.0, float(1-np.trace(rho@rho).real))
                datasets["observables/entanglement/reduced_coin_density_matrix"][row] = rho
            if config.output.save_state:
                datasets["states/snapshots"][row] = engine.state().reshape(*shape, d)
