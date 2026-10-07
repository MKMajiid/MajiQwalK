"""Create a clean source ZIP; run from any directory with python3."""
from pathlib import Path
import runpy
from archive_utils import write_archive

ROOT = Path(__file__).resolve().parents[1]
VERSION = runpy.run_path(str(ROOT / "python/majiqwalk/_version.py"))["__version__"]
EXCLUDED = {".git", ".venv", "build", "dist", "__pycache__", ".pytest_cache", "figures"}
GENERATED_SUFFIXES = {".pyc", ".pyo", ".so", ".pyd", ".h5", ".csv"}
files = [path for path in ROOT.rglob("*") if path.is_file()
         and not EXCLUDED.intersection(path.relative_to(ROOT).parts)
         and not any(part.endswith(".egg-info") for part in path.relative_to(ROOT).parts)
         and path.suffix not in GENERATED_SUFFIXES]
name = f"MajiQwalK-v{VERSION.replace('.dev', '-dev')}-source.zip"
print(write_archive(ROOT / "dist" / name, ROOT.parent, files))
