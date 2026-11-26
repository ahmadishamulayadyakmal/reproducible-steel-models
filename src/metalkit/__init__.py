"""Utilities for reproducible computational metallurgy workflows.

C01 provides pinned dataset provenance, deterministic reproducibility baselines
and a predictive ExtraTrees case with nested hyperparameter search, five-seed /
five-fold error bars and an explicit adoption gate.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("metalkit")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.7.0"

__all__ = ["__version__"]
