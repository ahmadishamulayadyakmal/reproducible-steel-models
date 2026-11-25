"""Utilities for reproducible computational metallurgy workflows.

C01 provides pinned dataset provenance, deterministic reproducibility baselines
and a predictive ExtraTrees case with nested hyperparameter search, five-seed /
five-fold error bars and an explicit adoption gate. A schema-driven ingestion
layer arrives in E02 (W05-W08).
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("metalkit")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.5.0"

__all__ = ["__version__"]
