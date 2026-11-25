# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-11-25 · C01 closeout

### Added

- `data/SOURCES.md` with the three pinned open-data files, upstream links and
  SHA-256 / byte checks for D01 and D04.
- `metalkit hash` and `metalkit reproduce` commands, with checksum gates,
  two-run determinism checks, source fingerprints and JSON result artefacts.
- Deterministic baselines for UCI Steel Plates Faults and `matbench_steels`
  official fold 0; `results/metrics.json` and `results/provenance.json`.
- One-page audit `docs/reproducibility_audit.md` separating reproduced numbers
  from external literature numbers.
- Tests for hashing, composition parsing, provenance and the two baselines
  (10 Python tests pass locally).

### Changed

- Exact pins for numpy, pandas, scipy, scikit-learn, joblib and threadpoolctl
  in `pyproject.toml`, `pixi.toml` and `environment.yml`.
- README validation section now reports the measured numbers and the remaining
  unverified cross-OS / clean-tag claims.

### Notes

- Cross-OS CI, `pixi`, Docker, `just` and the Fortran toolchain are not
  available on the development host; those checks remain open.

## [0.1.0] — 2026-11-24 · tag `w04`

### Added

- Repository skeleton for the 52-sprint computational metallurgy portfolio.
- `metalkit` Python package with a minimal CLI (`--version`, `--help`, `info`) and pytest suite.
- `libthermo` Fortran library with a unit test runnable through `fpm test`.
- Reproducible environment files (`pixi.toml`, `environment.yml`, `Dockerfile`).
- CI matrix for Ubuntu and Windows (Python + Fortran tests).
- `data/SOURCES.md` template and sprint notes `w01`–`w04`.

### Notes

- No datasets, models, or physics results yet. First data ingestion is W05–W06;
  first verified solver is W09–W13.
- Local validation was Python-only because `gfortran`/`fpm` are not installed on the
  development host; Fortran tests are exercised in CI.
