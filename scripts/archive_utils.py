"""ZIP packaging with source dates that cannot be ahead of the user's clock."""
from pathlib import Path
import zipfile


def write_archive(destination: Path, root: Path, files) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo.from_file(path, path.relative_to(root).as_posix())
            info.date_time = (2000, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return destination
