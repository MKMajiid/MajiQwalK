"""Transport diagnostics and quantum/classical result comparisons."""
from pathlib import Path
import h5py
import numpy as np


def _variance_series(path):
    with h5py.File(path, "r") as file:
        if "observables/variance" not in file:
            raise ValueError(f"{path}: observables/variance is required")
        steps = np.asarray(file["steps"][()], dtype=float)
        variance = np.asarray(file["observables/variance"][()], dtype=float)
        if variance.ndim != 2 or variance.shape[0] != steps.size:
            raise ValueError(f"{path}: invalid variance dataset")
        total = variance.sum(axis=1)
        model = file["metadata"].attrs.get("model_type", "unknown")
        shape = tuple(int(x) for x in file["geometry/shape"][()])
        origin = tuple(float(x) for x in file["geometry/origin"][()])
    return steps, total, model, shape, origin


def transport_diagnostics(path, *, fit_start_fraction=0.5):
    """Fit sigma^2(t) ~ A t^alpha over the late finite-time window.

    This is a diagnostic fit, not an asymptotic proof.
    """
    if not 0 <= fit_start_fraction < 1:
        raise ValueError("fit_start_fraction must be in [0, 1)")
    steps, total, model, shape, origin = _variance_series(path)
    positive = (steps > 0) & np.isfinite(total) & (total > 0)
    indices = np.flatnonzero(positive)
    if indices.size < 3:
        raise ValueError("At least three positive finite variance samples are required")
    start = indices[min(int(np.floor(indices.size * fit_start_fraction)), indices.size - 3)]
    mask = positive & (np.arange(steps.size) >= start)
    x = np.log(steps[mask])
    y = np.log(total[mask])
    alpha, log_a = np.polyfit(x, y, 1)
    fitted = log_a + alpha * x
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 if ss_tot == 0 and ss_res == 0 else 1.0 - ss_res / ss_tot
    return {
        "file": str(Path(path).resolve()),
        "model_type": str(model),
        "shape": list(shape),
        "origin": list(origin),
        "fit_step_min": int(steps[mask][0]),
        "fit_step_max": int(steps[mask][-1]),
        "samples": int(mask.sum()),
        "alpha": float(alpha),
        "prefactor": float(np.exp(log_a)),
        "r_squared": float(r2),
        "classification": (
            "diffusive-like" if 0.8 <= alpha <= 1.2 else
            "ballistic-like" if 1.8 <= alpha <= 2.2 else
            "subdiffusive-like" if alpha < 0.8 else
            "superdiffusive-like"
        ),
        "interpretation": "finite-time fit; not an asymptotic critical exponent",
    }


def compare_transport(first, second):
    a_steps, a_var, a_model, a_shape, a_origin = _variance_series(first)
    b_steps, b_var, b_model, b_shape, b_origin = _variance_series(second)
    if a_shape != b_shape:
        raise ValueError("Comparison requires identical geometry.shape")
    if not np.allclose(a_origin, b_origin, atol=0, rtol=0):
        raise ValueError("Comparison requires identical geometry.origin")
    if not np.array_equal(a_steps, b_steps):
        raise ValueError("Comparison requires identical sampled steps")
    return {
        "steps": a_steps,
        "variance_first": a_var,
        "variance_second": b_var,
        "model_first": str(a_model),
        "model_second": str(b_model),
        "diagnostics_first": transport_diagnostics(first),
        "diagnostics_second": transport_diagnostics(second),
    }
