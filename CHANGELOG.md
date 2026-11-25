# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Deterministic `c01_model_comparison.svg` chart generated from
  `results/metrics.json`: D01 accuracy progression, D04 fold-level MAE and R²,
  and the five fold-wise MAE reductions against the 50% gate.
- `metalkit report --comparison-output` writes the comparison chart beside the
  scorecard by default; `just figures` renders both.

## [0.5.0] — 2026-11-25 · Nested hyperparameter search

### Added

- Leakage-safe nested hyperparameter search for both predictive datasets. Inner
  CV selects `max_features` and `min_samples_leaf` on the outer training split
  only; every seed/fold stores its selected parameters and inner best score.
- `CompositionVectorizer` pipeline step so the D04 element vocabulary is cloned
  and refitted inside each inner training split.
- Two new experiment payloads, `uci_faults_nested_extra_trees` and
  `matbench_steels_nested_extra_trees`, with fixed ExtraTrees retained as a
  comparator.
- Updated scorecard, results page and model card showing nested-search metrics.

### Changed

- Headline D01 accuracy improved from 0.6936 to **0.7486**; macro F1 from 0.7755
  to **0.8114**.
- Headline D04 MAE improved from 79.1707 to **77.6894 MPa** (1.87% lower);
  RMSE from 112.0894 to **111.0717 MPa**; R² from 0.8566 to **0.8581**.
- Adoption gate still passes on all five official folds. Previous tags are not
  moved; this release is tagged `c01-nested-search`.

## [0.4.0] — 2026-11-25 · Improved predictive case

### Added

- Deterministic ExtraTrees models for D01 and D04 as the new headline
  predictors; RandomForest is retained as a comparator payload.
- `summary.headline_model`, ExtraTrees metrics and the MAE gain over
  RandomForest in `results/metrics.json`.
- Updated scorecard, model card and results page showing the improved numbers.

### Changed

- D04 MAE improved from 89.6300 to **79.1707 MPa** (11.67% lower); D01 accuracy
  improved from 0.6766 to **0.6936**. R² improved from 0.8141 to **0.8566**.
- The adoption gate description now refers to the headline ensemble rather than
  a specific model.

## [0.3.0] — 2026-11-25 · C01 predictive case

### Added

- Deterministic RandomForest predictive models for D01 and D04, with five fixed
  seeds and all five official MatBench folds; mean ± std error bars are written
  to `results/metrics.json`.
- Leakage-safe composition encoding: the element vocabulary is fitted on
  training formulas only and unseen test elements are ignored.
- An explicit, case-specific adoption gate: ≥50% MAE reduction versus the
  train-mean predictor on every fold and mean R² ≥ 0.70. The gate passes.
- An actual [`docs/model_card.md`](docs/model_card.md) for the RandomForest
  models; predictive tables and claim boundary in `docs/results.md`.
- `metalkit report`, `docs/figures/c01_scorecard.svg` and the README
  `## Case result (C01)` section make the result visible in the repository.

### Changed

- `metalkit reproduce` now writes a `summary` block and five experiment
  payloads while retaining the historical logistic/Ridge baselines.
- README documentation link points to the shared BibTeX library in
  `metallurgy-evidence-audit`, not to a non-existent local path.
- Current Python suite has 14 tests; the tagged `c01` clean-state release had 10.

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

- Post-merge verification (2026-11-25): CI passed on Ubuntu and Windows
  (run `45545998166`); `git archive 0d3d3f1` reproduced all five metrics and
  10 tests from a clean checkout. Case tag `c01` follows this release commit.
- `pixi`, Docker, `just` and the Fortran toolchain are not available on the
  development host; local container builds and local Fortran runs remain open.

## [0.1.0] — 2026-11-24

### Added

- Initial repository skeleton for the computational metallurgy portfolio.
- `metalkit` Python package with a minimal CLI (`--version`, `--help`, `info`) and pytest suite.
- `libthermo` Fortran library with a unit test runnable through `fpm test`.
- Reproducible environment files (`pixi.toml`, `environment.yml`, `Dockerfile`).
- CI matrix for Ubuntu and Windows (Python + Fortran tests).
- `data/SOURCES.md` dataset provenance template.

### Notes

- No datasets, models, or physics results in this initial release.
- Local validation was Python-only because `gfortran`/`fpm` are not installed on the
  development host; Fortran tests are exercised in CI.
