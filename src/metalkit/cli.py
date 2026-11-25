"""Command-line entry point for metalkit.

Only the standard library is imported so that ``metalkit --help`` works before
the scientific dependency stack has been installed.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from metalkit import __version__

_DESCRIPTION = "Reproducible data and modelling utilities for metallurgy."


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="metalkit", description=_DESCRIPTION)
    parser.add_argument(
        "--version", action="version", version=f"metalkit {__version__}"
    )

    subcommands = parser.add_subparsers(dest="command", metavar="COMMAND")
    subcommands.add_parser("info", help="print package and portfolio information")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "info":
        print(f"metalkit {__version__}")
        print(_DESCRIPTION)
        print("Schedule: 52 weekly sprints, 12 epics. See WEEKLY_PLAN.md.")
    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
