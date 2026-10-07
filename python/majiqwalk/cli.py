"""Command-line interface; simulation and plotting are separate actions."""
import argparse
import json
from pathlib import Path
import sys

from . import Config, Results, Simulation, __version__


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    commands = {"run", "validate", "inspect", "plot", "export", "schema"}
    if argv and not argv[0].startswith("-") and argv[0] not in commands:
        argv.insert(0, "run")
    parser = argparse.ArgumentParser(prog="majiqwalk", description="C++ discrete-time quantum walks with a Python interface")
    parser.add_argument("--version", action="version", version=f"MajiQwalK {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="validate and run a YAML configuration")
    run.add_argument("config")
    run.add_argument("--output")
    run.add_argument("--overwrite", action="store_true", default=None)
    validate = sub.add_parser("validate", help="validate configuration and physical input")
    validate.add_argument("config")
    inspect = sub.add_parser("inspect", help="describe an HDF5 result")
    inspect.add_argument("file")
    plot = sub.add_parser("plot", help="write APS-style figures")
    plot.add_argument("file")
    plot.add_argument("--directory", default="figures")
    plot.add_argument("--formats", nargs="+", choices=["pdf", "svg", "png"], default=None)
    export = sub.add_parser("export", help="export probability to long-format CSV")
    export.add_argument("file")
    export.add_argument("--output", required=True)
    export.add_argument("--overwrite", action="store_true")
    sub.add_parser("schema", help="print the configuration JSON schema")
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps(Config.model_json_schema(), indent=2))
        elif args.command in {"run", "validate"}:
            config = Config.from_yaml(args.config)
            if args.command == "validate":
                print("Configuration valid (schema v1).")
                if config.simulation.representation == "density_matrix":
                    print("Density-matrix execution is not implemented in this milestone.")
            else:
                output = args.output or Path(args.config).resolve().parent / config.output.file
                result = Simulation(config).run(output, overwrite=args.overwrite)
                print(f"Saved {result.path}")
        elif args.command == "inspect":
            print(json.dumps(Results(args.file).summary(), indent=2))
        elif args.command == "export":
            print(Results(args.file).export_probability_csv(args.output, overwrite=args.overwrite))
        else:
            from .plot import plot_results
            for path in plot_results(args.file, args.directory, args.formats):
                print(path)
    except (ValueError, OSError, RuntimeError, MemoryError, NotImplementedError, ImportError, KeyError) as exc:
        print(f"MajiQwalK error: {exc}", file=sys.stderr)
        return 2
    return 0
