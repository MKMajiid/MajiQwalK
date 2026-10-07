"""HDF5 result access without keeping simulation history in memory."""
from pathlib import Path
import csv
import h5py


class Results:
    def __init__(self, path):
        self.path = Path(path).resolve()
        with h5py.File(self.path, "r") as file:
            if file["metadata"].attrs["output_schema_version"] != 1:
                raise ValueError("Unsupported output schema version")

    def read(self, dataset, selection=()):
        with h5py.File(self.path, "r") as file:
            return file[dataset][selection]

    @property
    def steps(self):
        return self.read("steps")

    @property
    def probability(self):
        """Load all sampled probabilities; use read(..., selection) for large runs."""
        return self.read("observables/probability")

    def summary(self):
        with h5py.File(self.path, "r") as file:
            datasets = {}
            file.visititems(lambda name, item: datasets.update({name: list(item.shape)}) if isinstance(item, h5py.Dataset) else None)
            return {"file": str(self.path), "version": file["metadata"].attrs["majiqwalk_version"],
                    "shape": file["geometry/shape"][()].tolist(), "datasets": datasets}

    def export_probability_csv(self, path, *, overwrite=False):
        """Long format: step, spatial coordinates, probability. Stream by sample."""
        mode = "w" if overwrite else "x"
        with h5py.File(self.path, "r") as file, Path(path).open(mode, newline="", encoding="utf-8") as stream:
            probability = file["observables/probability"]
            coords = file["geometry/coordinates"][()]
            writer = csv.writer(stream)
            writer.writerow(["step", *list("xyz"[:coords.shape[1]]), "probability"])
            for i, step in enumerate(file["steps"]):
                for coord, p in zip(coords, probability[i].reshape(-1)):
                    writer.writerow([int(step), *coord.tolist(), float(p)])
        return Path(path).resolve()
