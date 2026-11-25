# Model card — C01 predictive RandomForest models

**Version:** 0.3.0 · **Date:** 2026-11-25 · **Evidence:** A (public data only)
**Artefacts:** `results/metrics.json`, `results/provenance.json`,
[`results.md`](results.md), [`figures/c01_scorecard.svg`](figures/c01_scorecard.svg)

## Intended use

- **D01:** multi-label classification of steel-plate fault indicators from the
  27 UCI process/quality features. Use as a reproducible QC screening baseline,
  not as a plant release authority.
- **D04:** screening estimate of steel yield strength (MPa) from composition
  only, inside the composition range represented by the 312 public MatBench
  steels. Use to prioritise experiments, not to replace them.

## Data

| Dataset | Source | Samples | Split protocol | License / access |
|---|---|---:|---|---|
| D01 | UCI Steel Plates Faults | 1,941 | stratified 80/20, seeds `(42, 7, 11, 19, 23)` | CC BY 4.0, public archive |
| D04 | MatBench `matbench_steels` (R08) | 312 | official five-fold split, `random_state=18012019` | public GitHub benchmark |

All files, SHA-256 hashes and byte counts are in
[`../data/SOURCES.md`](../data/SOURCES.md). No plant data was used.

## Features and target

- **D01 features:** 27 numeric features, standard scaling is unnecessary for
  trees but retained only in the historical logistic baseline.
- **D04 features:** atomic fractions over an element vocabulary fitted on the
  **training formulas only**. Unseen test elements are ignored, so the test
  split cannot change the feature space.
- **D04 target:** yield strength in MPa.

## Reproducibility

- Models: `RandomForestClassifier` / `RandomForestRegressor`,
  `n_estimators=300`, `n_jobs=1`, fixed `random_state`.
- Every experiment payload is run twice and must be exactly identical.
- Commands: `python -m metalkit.cli reproduce` and `python -m pytest`.
- Package versions, Python version, code fingerprint and dataset hashes are in
  `results/provenance.json`.

## Metrics

| Metric | Value | Baseline | Uncertainty |
|---|---:|---:|---|
| D01 exact-match accuracy | **0.6766** | logistic 0.5013 | ± 0.0075 (5 seeds) |
| D01 macro F1 | **0.7526** | logistic 0.6207 | ± 0.0176 (5 seeds) |
| D04 MAE | **89.6300 MPa** | train-mean 229.7445 MPa; Ridge 205.3600 MPa | ± 7.4424 MPa (5 folds) |
| D04 RMSE | **127.9791 MPa** | Ridge 274.2509 MPa | ± 9.8846 MPa (5 folds) |
| D04 R² | **0.8141** | Ridge 0.1624 | ± 0.0388 (5 folds) |

The case-specific adoption gate passes: MAE is ≥50% below the train-mean
predictor on every official fold and mean R² ≥ 0.70.

## Limitations

- No plant data and no plant validation. The external MODNet MAE of 87.7627 MPa
  and Y2R12 R² > 0.97 are cited literature, **not reproduced** here.
- The mean ± std values describe split variability, not calibrated prediction
  intervals for an individual alloy.
- Composition-only descriptors do not encode processing, heat treatment,
  microstructure or thermodynamics.
- The public dataset is small (312 steels); extrapolation outside the observed
  composition range is unsupported.
- Must **not** be used to release or reject industrial material without
  independent measurements and a validated decision threshold.
