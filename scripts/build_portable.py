"""Build on the target OS. Self-contained candidates require release validation."""
from pathlib import Path
import importlib.metadata
import platform
import shutil
import subprocess
import sys
import tempfile
from archive_utils import write_archive

ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,"-m","PyInstaller","--noconfirm","--clean","--onedir",
                "--name","majiqwalk","--collect-all","majiqwalk","--collect-all","h5py",
                "--collect-data","matplotlib","--hidden-import","matplotlib.backends.backend_agg",
                "--hidden-import","matplotlib.backends.backend_pdf",
                "--hidden-import","matplotlib.backends.backend_svg",
                str(ROOT/"scripts/portable_entry.py"),
                "--distpath",str(ROOT/"dist"),"--workpath",str(ROOT/"build/portable"),
                "--specpath",str(ROOT/"build")],check=True)
bundle=ROOT/"dist/majiqwalk"
shutil.copytree(ROOT/"examples",bundle/"examples",dirs_exist_ok=True)
shutil.copytree(ROOT/"docs",bundle/"docs",dirs_exist_ok=True)
for filename in ["LICENSE","NOTICE","README.md","CITATION.cff"]:
    shutil.copy2(ROOT/filename,bundle/filename)
shutil.copy2(ROOT/"scripts/PORTABLE_README.md",bundle/"PORTABLE_README.md")
license_root=bundle/"THIRD_PARTY_LICENSES"
license_root.mkdir(exist_ok=True)
versions=[]
for distribution in importlib.metadata.distributions():
    name=distribution.metadata.get("Name", "unknown")
    versions.append(f"{name}=={distribution.version}")
    for relative in distribution.files or []:
        if any(token in relative.name.lower() for token in ("license", "copying", "notice", "copyright")):
            source=Path(distribution.locate_file(relative))
            if source.is_file():
                target=license_root/name/str(relative).replace("..", "_")
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,target)
(license_root/"build-environment.txt").write_text("\n".join(sorted(versions))+"\n",encoding="utf-8")
for python_license in [Path(sys.base_prefix)/"LICENSE.txt",
                       Path(sys.base_prefix)/"lib"/f"python{sys.version_info.major}.{sys.version_info.minor}"/"LICENSE.txt"]:
    if python_license.is_file():
        shutil.copy2(python_license,license_root/"CPython-LICENSE.txt")
        break
if platform.system()=="Linux":
    for source in Path("/usr/share/doc").glob("gcc-*-base/copyright"):
        shutil.copy2(source,license_root/f"{source.parent.name}-copyright.txt")
executable=bundle/("majiqwalk.exe" if platform.system()=="Windows" else "majiqwalk")
with tempfile.TemporaryDirectory() as folder:
    subprocess.run([str(executable),"--version"],cwd=folder,check=True)
    for geometry, coin in [("line", "hadamard"), ("line", "custom"),
                           ("square", "grover"), ("cubic", "grover")]:
        output=Path(folder)/f"{geometry}_{coin}.h5"
        subprocess.run([str(executable),"run",str(bundle/f"examples/{geometry}/{coin}.yaml"),
                        "--output",str(output)],cwd=folder,check=True)
        subprocess.run([str(executable),"inspect",str(output)],cwd=folder,check=True)
        subprocess.run([str(executable),"plot",str(output),
                        "--directory",str(Path(folder)/f"figures_{geometry}_{coin}"),
                        "--formats","pdf","svg","png"],cwd=folder,check=True)
name=f"majiqwalk-{platform.system().lower()}-{platform.machine().lower()}-portable"
archive=write_archive(ROOT/"dist"/f"{name}.zip", ROOT/"dist",
                      (path for path in bundle.rglob("*") if path.is_file()))
print(archive)
