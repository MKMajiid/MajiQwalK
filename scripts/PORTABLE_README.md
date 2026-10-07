# MajiQwalK portable development candidate

This archive includes Python and the compiled engine. It needs no separate
Python installation. It is a development candidate, not a stable release.

Extract the entire archive, keeping the `_internal` directory next to the
executable. Open a terminal in the extracted `majiqwalk` directory.

Linux:

```bash
chmod +x majiqwalk
./majiqwalk --version
./majiqwalk run examples/line/hadamard.yaml
./majiqwalk plot examples/line/line_hadamard.h5 --directory figures
```

Windows PowerShell:

```powershell
.\majiqwalk.exe --version
.\majiqwalk.exe run examples/line/hadamard.yaml
.\majiqwalk.exe plot examples/line/line_hadamard.h5 --directory figures
```

The Linux archive is for x86_64 and was tested in the build environment;
independent clean-machine compatibility remains to be established. The Windows
workflow is provided in the source repository and needs separate verification.
See `docs/user-guide/manual.md` for configuration and data conventions.

Retain `LICENSE`, `NOTICE` and `THIRD_PARTY_LICENSES` when redistributing.
