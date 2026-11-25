"""Utilities for reproducible computational metallurgy workflows.

C01 adds pinned dataset provenance and two deterministic baselines. A full
schema-driven ingestion layer arrives in E02 (W05-W08).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("metalkit")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.2.0"

__all__ = ["__version__"]
