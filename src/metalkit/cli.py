"""Command-line entry point for metalkit.

``--help``, ``--version``, ``info``, ``hash`` and ``report`` use only the
standard library; ``reproduce`` loads the scientific stack when invoked.
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

    report_command = subcommands.add_parser(
        "report", help="render C01 SVG figures from results/metrics.json"
    )
    report_command.add_argument("--metrics", default="results/metrics.json")
    report_command.add_argument(
        "--output", default="docs/figures/c01_scorecard.svg"
    )
    report_command.add_argument(
        "--comparison-output",
        help="comparison chart path; defaults to c01_model_comparison.svg beside --output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        print(f"metalkit {__version__}")
        print(_DESCRIPTION)
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
                "summary": result["summary"],
            },
        )
        write_json(
            output_dir / "provenance.json",
            {"base_commit": commit, **result},
        )

        print(f"base commit {commit} · seed {args.seed} · fold {args.fold}")
        for name, experiment in result["experiments"].items():
            print(f"{name}: {experiment['metrics']}")
        print(f"case verdict: {result['summary']['case_verdict']}")
        print(f"wrote {output_dir / 'metrics.json'} and {output_dir / 'provenance.json'}")
    elif args.command == "report":
        from metalkit.report import write_comparison, write_scorecard

        output = Path(args.output)
        comparison_output = (
            Path(args.comparison_output)
            if args.comparison_output
            else output.with_name("c01_model_comparison.svg")
        )
        scorecard = write_scorecard(Path(args.metrics), output)
        comparison = write_comparison(Path(args.metrics), comparison_output)
        print(f"wrote {scorecard}")
        print(f"wrote {comparison}")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
