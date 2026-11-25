# Model card — C01 nested-CV ExtraTrees models

**Version:** 0.5.0 · **Date:** 2026-11-25 · **Evidence:** A (public data only)
**Artefacts:** `results/metrics.json`, `results/provenance.json`,
[`results.md`](results.md), [`figures/c01_scorecard.svg`](figures/c01_scorecard.svg)

## Intended use

- **D01:** multi-label classification of steel-plate fault indicators from the
  27 UCI process/quality features. Use as a reproducible QC screening model,
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

## Features, target and search space

- **D01 features:** 27 numeric process/quality features.
- **D04 features:** atomic fractions over an element vocabulary fitted on the
  **training formulas only**. As a pipeline step, the vocabulary is refitted by
  scikit-learn inside each inner training split.
- **D04 target:** yield strength in MPa.
- **Headline estimator:** `ExtraTreesClassifier` / `ExtraTreesRegressor`,
  `n_estimators=300`, `n_jobs=1`, fixed `random_state`.
- **Search space:** `max_features ∈ {0.5, 1.0}` and
  `min_samples_leaf ∈ {1, 2}` for D01; `max_features ∈ {0.5, 1.0}` and
  `min_samples_leaf ∈ {1, 2, 4}` for D04.
- **Inner CV:** 3 folds on D01 training rows (macro F1), 4 folds on D04 training
  rows (MAE). The outer test split is never used to select parameters.
- **Comparators:** fixed ExtraTrees (500 trees), RandomForest (300 trees),
  Ridge, logistic and train-mean payloads remain in `results/metrics.json`.

## Reproducibility

- Nested search records `selected_params` and inner best score for every seed
  and every official fold.
- Every experiment payload is run twice and must be exactly identical.
- Commands: `python -m metalkit.cli reproduce` and `python -m pytest`.
- Package versions, Python version, code fingerprint and dataset hashes are in
  `results/provenance.json`.

## Metrics

| Metric | Nested ExtraTrees | Fixed ExtraTrees | RandomForest | Historical baseline | Uncertainty |
|---|---:|---:|---:|---:|---|
| D01 exact-match accuracy | **0.7486** | 0.6936 | 0.6766 | logistic 0.5013 | ± 0.0072 (5 seeds) |
| D01 macro F1 | **0.8114** | 0.7755 | 0.7526 | logistic 0.6207 | ± 0.0164 (5 seeds) |
| D04 MAE | **77.6894 MPa** | 79.1707 MPa | 89.6300 MPa | Ridge 205.3600 MPa; train-mean 229.7445 MPa | ± 7.2132 MPa (5 folds) |
| D04 RMSE | **111.0717 MPa** | 112.0894 MPa | 127.9791 MPa | Ridge 274.2509 MPa | ± 12.3347 MPa (5 folds) |
| D04 R² | **0.8581** | 0.8566 | 0.8141 | Ridge 0.1624 | ± 0.0398 (5 folds) |

Nested search raises D01 accuracy by **5.50 percentage points** and lowers D04
MAE by **1.87%** versus fixed ExtraTrees. The case-specific adoption gate
passes: MAE is ≥50% below the train-mean predictor on every official fold and
mean R² ≥ 0.70. The D04 selected parameters vary by fold
(`max_features=0.5` on fold 2, `min_samples_leaf=2` on folds 1 and 3), while D01
selects `max_features=1.0, min_samples_leaf=1` for all five seeds.

## Limitations

- No plant data and no plant validation. The external MODNet MAE of 87.7627 MPa
  and Y2R12 R² > 0.97 are cited literature, **not reproduced** here. Our lower
  numerical MAE is not a like-for-like benchmark win: model and featurization
  differ.
- The mean ± std values describe split variability, not calibrated prediction
  intervals for an individual alloy.
- Composition-only descriptors do not encode processing, heat treatment,
  microstructure or thermodynamics.
- The public dataset is small (312 steels); extrapolation outside the observed
  composition range is unsupported.
- The inner grid is deliberately small and cheap; it is an auditable nested
  search, not a guarantee of a global optimum.
- Must **not** be used to release or reject industrial material without
  independent measurements and a validated decision threshold.
