# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-11-24 · tag `w04`

### Added

- Repository skeleton for the 52-sprint computational metallurgy portfolio.
- `metalkit` Python package with a minimal CLI (`--version`, `--help`, `info`) and pytest suite.
- `libthermo` Fortran library with a unit test runnable through `fpm test`.
- Reproducible environment files (`pixi.toml`, `environment.yml`, `Dockerfile`).
- CI matrix for Ubuntu and Windows (Python + Fortran tests).
- `data/SOURCES.md`, `data/catalog.yml`, `papers/references.bib`, two paper notes,
  and sprint notes `w01`–`w04`.

### Notes

- No datasets, models, or physics results yet. First data ingestion is W05–W06;
  first verified solver is W09–W13.
- Local validation was Python-only because `gfortran`/`fpm` are not installed on the
  development host; Fortran tests are exercised in CI.
