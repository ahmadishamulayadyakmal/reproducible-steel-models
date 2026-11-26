# Task runner: https://github.com/casey/just
# Equivalent make-style targets are intentionally not duplicated.

default:
    @just --list

test:
    python -m pytest
    fpm test

test-py:
    python -m pytest

test-fortran:
    fpm test

info:
    python -m metalkit.cli info

# Regenerate results/metrics.json and results/provenance.json from data/raw/.
reproduce:
    python -m metalkit.cli reproduce --data-dir data/raw --output-dir results

# Render the C01 Springer-style scorecard, comparison, and diagnostics figures.
figures:
    python -m metalkit.cli report --metrics results/metrics.json --output docs/figures/c01_scorecard.svg --comparison-output docs/figures/c01_model_comparison.svg --diagnostics-output docs/figures/c01_diagnostics.svg

# "make all" is an alias for the full test target below.
all: test
    @echo "All checks passed."
