"""Utilities for reproducible computational metallurgy workflows.

This package is intentionally minimal in W01-W04. Data ingestion and
validation arrive in E02 (W05-W08).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("metalkit")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.1.0"

__all__ = ["__version__"]
