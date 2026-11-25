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

# Render the C01 case scorecard from the committed metrics.
figures:
    python -m metalkit.cli report --metrics results/metrics.json --output docs/figures/c01_scorecard.svg

# Alias used in GRAND_PLAN.md: "make all" == "just all"
all: test
    @echo "All checks passed."
