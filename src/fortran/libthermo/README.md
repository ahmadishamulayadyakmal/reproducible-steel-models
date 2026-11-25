# libthermo

Modern Fortran kernel library for the computational metallurgy portfolio.
The repository-level `fpm.toml` points to `src/` and `test/` in this directory.

## Current content (W03)

- `dp`: double-precision kind used by all kernels.
- `version`: package version string.
- `kelvin_from_celsius`, `celsius_from_kelvin`: pure unit-conversion helpers.

No physics kernel is implemented yet. The enthalpy–porosity solver is planned
for W09–W13 and will be benchmarked against Voller & Prakash (1987), R16.

## Test

```bash
fpm test
```

The first test is self-contained (no `test-drive`/`pFUnit` dependency) so that
a compiler problem is not confused with a package-download problem. A test
framework will be added together with the solver tests in W09.

## Limitations

- Unit conversion only; no thermodynamic database, phase diagram, or CFD
  capability is present.
- `fpm test` is exercised in CI; it could not be run on the Windows development
  host because `gfortran`/`fpm` are not installed there (see `docs/sprints/w03.md`).
