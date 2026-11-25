"""Command-line entry point for metalkit.

``--help``, ``--version``, ``info`` and ``hash`` use only the standard library;
``reproduce`` loads the scientific stack when it is actually invoked.
"""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

from metalkit import __version__
from metalkit.baselines import reproduce as reproduce_baselines
from metalkit.provenance import sha256_file, write_json

_DESCRIPTION = "Reproducible data and modelling utilities for metallurgy."


def _git_commit(root: Path) -> str:
    """Return the current commit hash, or 'unknown' outside a Git work tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="metalkit", description=_DESCRIPTION)
    parser.add_argument(
        "--version", action="version", version=f"metalkit {__version__}"
    )

    subcommands = parser.add_subparsers(dest="command", metavar="COMMAND")
    subcommands.add_parser("info", help="print package and portfolio information")

    hash_command = subcommands.add_parser("hash", help="print SHA-256 digests")
    hash_command.add_argument("files", nargs="+", help="files to hash")

    reproduce_command = subcommands.add_parser(
        "reproduce", help="run the pinned C01 baselines twice and write results"
    )
    reproduce_command.add_argument("--data-dir", default="data/raw")
    reproduce_command.add_argument("--output-dir", default="results")
    reproduce_command.add_argument("--seed", type=int, default=42)
    reproduce_command.add_argument("--fold", type=int, default=0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        print(f"metalkit {__version__}")
        print(_DESCRIPTION)
        print("Schedule: 52 weekly sprints, 12 epics. See WEEKLY_PLAN.md.")
    elif args.command == "hash":
        for filename in args.files:
            print(f"{sha256_file(filename)}  {filename}")
    elif args.command == "reproduce":
        data_dir = Path(args.data_dir)
        output_dir = Path(args.output_dir)
        result = reproduce_baselines(data_dir, seed=args.seed, fold=args.fold)
        commit = _git_commit(Path.cwd())

        write_json(
            output_dir / "metrics.json",
            {
                "base_commit": commit,
                "seed": args.seed,
                "experiments": result["experiments"],
            },
        )
        write_json(
            output_dir / "provenance.json",
            {"base_commit": commit, **result},
        )

        print(f"base commit {commit} · seed {args.seed} · fold {args.fold}")
        for name, experiment in result["experiments"].items():
            print(f"{name}: {experiment['metrics']}")
        print(f"wrote {output_dir / 'metrics.json'} and {output_dir / 'provenance.json'}")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
