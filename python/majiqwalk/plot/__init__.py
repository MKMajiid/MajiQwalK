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
        steps = file["steps"][()]

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
            if len(shape)>1:
                ax.legend(frameon=False)
            save(fig, "variance")
        if "observables/entanglement/coin_position_entropy" in file:
            fig, ax = plt.subplots()
            ax.plot(steps, file["observables/entanglement/coin_position_entropy"][()], color="black")
            ax.set(xlabel="Step $t$", ylabel="$S_c$ (bits)")
            save(fig, "coin_position_entropy")
    return paths
