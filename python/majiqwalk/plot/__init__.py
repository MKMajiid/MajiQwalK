"""APS Physical Review figure profile; no plotting inside the engine."""
from pathlib import Path
import h5py
import numpy as np
import yaml

APS_PR = {
    "figure.figsize": (3.375, 2.5),
    "font.family": "serif", "font.size": 9, "mathtext.fontset": "dejavuserif",
    "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.linewidth": 0.7, "lines.linewidth": 1.0,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
    "savefig.dpi": 600,
}


def plot_results(path, directory="figures", formats=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    with h5py.File(path, "r") as file, plt.rc_context(APS_PR):
        config = yaml.safe_load(file["config/yaml"][()].decode())
        formats = formats or config["plot"]["formats"]
        if not formats or any(f not in {"pdf", "svg", "png"} for f in formats):
            raise ValueError("Plot formats must be pdf, svg, or png")
        shape = file["geometry/shape"][()].tolist()
        origin = file["geometry/origin"][()]
        steps = np.asarray(file["steps"][()], dtype=np.int64)

        if steps.ndim != 1 or steps.size == 0:
            raise ValueError("Invalid HDF5 result: steps must be a nonempty 1D dataset")
        if steps[0] != 0 or np.any(np.diff(steps) <= 0):
            raise ValueError("Invalid HDF5 result: steps must start at 0 and be strictly increasing")
        configured_steps = int(config["simulation"]["steps"])
        if int(steps[-1]) != configured_steps:
            raise ValueError(
                f"Inconsistent HDF5 result: configuration requests {configured_steps} steps "
                f"but stored samples end at {int(steps[-1])}. Rerun the simulation after "
                "changing YAML (use --overwrite or a new output filename)."
            )
        for dataset_name in (
            "observables/probability",
            "observables/variance",
            "observables/entanglement/coin_position_entropy",
        ):
            if dataset_name in file and file[dataset_name].shape[0] != steps.size:
                raise ValueError(
                    f"Inconsistent HDF5 result: {dataset_name} has "
                    f"{file[dataset_name].shape[0]} samples but steps has {steps.size}"
                )

        def set_time_axis(ax):
            if steps[-1] > steps[0]:
                ax.set_xlim(float(steps[0]), float(steps[-1]))

        def save(fig, name):
            fig.tight_layout(pad=0.4)
            for format in formats:
                target = directory / f"{name}.{format}"
                fig.savefig(target)  # preserve physical column width; no bbox crop
                paths.append(target)
            plt.close(fig)

        if "observables/probability" in file:
            probability = file["observables/probability"][-1]
            fig, ax = plt.subplots()
            if len(shape) == 1:
                x = np.arange(shape[0])-origin[0]
                ax.plot(x, probability, color="black")
                ax.set(xlabel="$x$", ylabel="$P(x,t)$")
            else:
                # In 3D the plot is explicitly a marginal, not a volume projection
                # mislabeled as the full distribution.
                p = probability if len(shape) == 2 else probability.sum(axis=2)
                extent = (-origin[0]-.5, shape[0]-origin[0]-.5,
                          -origin[1]-.5, shape[1]-origin[1]-.5)
                im = ax.imshow(p.T, origin="lower", extent=extent, interpolation="nearest", cmap="viridis")
                ax.set(xlabel="$x$", ylabel="$y$")
                fig.colorbar(im, ax=ax, label="$P(x,y,t)$" if len(shape) == 2 else r"$\sum_z P(x,y,z,t)$")
            save(fig, f"probability_t{steps[-1]}")
        if "observables/variance" in file:
            fig, ax = plt.subplots()
            values = file["observables/variance"][()]
            for axis, style in enumerate(["-", "--", ":"][:len(shape)]):
                ax.plot(steps, values[:,axis], style, color="black", label=f"${'xyz'[axis]}$")
            ax.set(xlabel="Step $t$", ylabel="Position variance")
            set_time_axis(ax)
            if len(shape)>1:
                ax.legend(frameon=False)
            save(fig, "variance")
        if "observables/entanglement/coin_position_entropy" in file:
            fig, ax = plt.subplots()
            ax.plot(steps, file["observables/entanglement/coin_position_entropy"][()], color="black")
            ax.set(xlabel="Step $t$", ylabel="$S_c$ (bits)")
            set_time_axis(ax)
            save(fig, "coin_position_entropy")
    return paths



def plot_comparison(first, second, directory="figures", formats=None):
    """Compare compatible runs: probability, variance, RMS displacement and scaling."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ..analysis import compare_transport

    result = compare_transport(first, second)
    formats = formats or ["pdf", "png"]
    if not formats or any(f not in {"pdf", "svg", "png"} for f in formats):
        raise ValueError("Plot formats must be pdf, svg, or png")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        fig.tight_layout(pad=0.4)
        for format in formats:
            target = directory / f"{name}.{format}"
            fig.savefig(target)
            paths.append(target)
        plt.close(fig)

    steps = result["steps"]
    first_var = result["variance_first"]
    second_var = result["variance_second"]
    d1 = result["diagnostics_first"]
    d2 = result["diagnostics_second"]

    with plt.rc_context(APS_PR):
        with h5py.File(first, "r") as first_file, h5py.File(second, "r") as second_file:
            if "observables/probability" in first_file and "observables/probability" in second_file:
                p1 = np.asarray(first_file["observables/probability"][-1])
                p2 = np.asarray(second_file["observables/probability"][-1])
                shape = first_file["geometry/shape"][()].tolist()
                origin = first_file["geometry/origin"][()]
                fig, ax = plt.subplots()
                x = np.arange(shape[0]) - origin[0]
                if len(shape) == 1:
                    m1, m2 = p1, p2
                    ylabel = "$P(x,t)$"
                else:
                    axes = tuple(range(1, p1.ndim))
                    m1, m2 = p1.sum(axis=axes), p2.sum(axis=axes)
                    ylabel = r"$\sum_{\perp x}P(\mathbf{x},t)$"
                ax.plot(x, m1, "-", color="black", label=result["model_first"])
                ax.plot(x, m2, "--", color="black", label=result["model_second"])
                ax.set(xlabel="$x$", ylabel=ylabel)
                ax.legend(frameon=False)
                save(fig, f"probability_comparison_t{int(steps[-1])}")

        fig, ax = plt.subplots()
        ax.plot(steps, first_var, "-", color="black",
                label=f"{result['model_first']}  α={d1['alpha']:.3f}")
        ax.plot(steps, second_var, "--", color="black",
                label=f"{result['model_second']}  α={d2['alpha']:.3f}")
        ax.set(xlabel="Step $t$", ylabel=r"Total variance $\sigma^2(t)$")
        if steps[-1] > steps[0]:
            ax.set_xlim(float(steps[0]), float(steps[-1]))
        ax.legend(frameon=False)
        save(fig, "transport_variance_comparison")

        fig, ax = plt.subplots()
        ax.plot(steps, np.sqrt(np.maximum(first_var, 0)), "-", color="black",
                label=result["model_first"])
        ax.plot(steps, np.sqrt(np.maximum(second_var, 0)), "--", color="black",
                label=result["model_second"])
        ax.set(xlabel="Step $t$", ylabel=r"RMS displacement $\sigma(t)$")
        if steps[-1] > steps[0]:
            ax.set_xlim(float(steps[0]), float(steps[-1]))
        ax.legend(frameon=False)
        save(fig, "transport_rms_comparison")
    return paths
