# Model Card — Case 01 Nested-CV ExtraTrees Models

**Version:** 0.6.1 · **Evidence:** Public datasets only (no plant data)  
**Artefacts:** `results/metrics.json`, `results/provenance.json`, [`results.md`](results.md), [`figures/c01_scorecard.svg`](figures/c01_scorecard.svg), [`figures/c01_model_comparison.svg`](figures/c01_model_comparison.svg)

## Intended Use

- **UCI Steel Plates Faults:** Multi-label classification of 7 steel-plate fault indicators from 27 numeric inspection features. Intended as a reproducible QC screening benchmark, **not** as an automated plant release authority.
- **MatBench `matbench_steels`:** Screening estimate of steel yield strength (MPa) from alloy composition within the domain of the 312 public MatBench steels. Intended to prioritize candidate experiments, **not** to replace mechanical testing.

## Datasets

| Dataset | Source | Samples | Split Protocol | Licence |
|---|---|---:|---|---|
| UCI Steel Plates Faults | [UCI ML Repository](https://archive.ics.uci.edu/dataset/198/steel+plates+faults) | 1,941 | Stratified 80/20, seeds `(42, 7, 11, 19, 23)` | CC BY 4.0 |
| MatBench `matbench_steels` | [MatBench (Dunn et al., 2020)](https://matbench.materialsproject.org/) | 312 | Official 5-fold CV (`random_state=18012019`) | Public benchmark |

Exact SHA-256 digests and byte counts are pinned in [`../data/SOURCES.md`](../data/SOURCES.md).

## Features, Target & Search Space

- **UCI Faults features:** 27 numeric geometric and process indicators.
- **MatBench Steels features:** Atomic-fraction composition vectors fitted strictly on **training formulas only** via `CompositionVectorizer` inside each CV split.
- **MatBench Steels target:** Yield strength (MPa).
- **Headline estimator:** `ExtraTreesClassifier` / `ExtraTreesRegressor`, `n_estimators=300`, `n_jobs=1`, fixed `random_state`.
- **Inner CV search space:** `max_features ∈ {0.5, 1.0}`, `min_samples_leaf ∈ {1, 2}` (UCI, 3-fold macro F1); `max_features ∈ {0.5, 1.0}`, `min_samples_leaf ∈ {1, 2, 4}` (MatBench, 4-fold negative MAE).
- **Comparators retained:** Fixed ExtraTrees (500 trees), RandomForest (300 trees), Ridge, Logistic, and train-mean baselines remain in `results/metrics.json`.

## Reproducibility & Provenance

- Every experiment payload is executed twice consecutively and must match identically.
- `results/metrics.json` records `selected_params`, inner CV best scores, and per-fold interval calibration metrics.
- `results/provenance.json` records dataset SHA-256 hashes, Python source fingerprint, and pinned package versions.
- Commands: `python -m metalkit.cli reproduce`, `python -m metalkit.cli report`, `python -m pytest`.

## Summary Metrics

| Metric | Nested ExtraTrees | Fixed ExtraTrees | RandomForest | Linear Baseline | Uncertainty |
|---|---:|---:|---:|---:|---|
| UCI exact-match accuracy | **0.7486** | 0.6936 | 0.6766 | Logistic 0.5013 | ± 0.0072 (5 seeds) |
| UCI macro F1 | **0.8114** | 0.7755 | 0.7526 | Logistic 0.6207 | ± 0.0164 (5 seeds) |
| MatBench MAE | **77.6894 MPa** | 79.1707 MPa | 89.6300 MPa | Ridge 205.3600 MPa | ± 7.2132 MPa (5 folds) |
| MatBench RMSE | **111.0717 MPa** | 112.0894 MPa | 127.9791 MPa | Ridge 274.2509 MPa | ± 12.3347 MPa (5 folds) |
| MatBench $R^2$ | **0.8581** | 0.8566 | 0.8141 | Ridge 0.1624 | ± 0.0398 (5 folds) |

### Prediction Interval Calibration (`matbench_steels`)

- **Method:** 4-fold cross-conformal out-of-fold absolute residuals on each outer training split only.
- **Target coverage:** 90% ($\alpha = 0.10$).
- **Observed empirical coverage:** **0.9198 ± 0.0304** across the 5 official folds (`0.8889, 0.9683, 0.9194, 0.9355, 0.8871`).
- **Mean interval width:** Half-width **194.54 ± 15.40 MPa**; full width **389.08 ± 30.81 MPa**.

## Limitations

- **No plant validation:** External literature values (MODNet 87.7627 MPa MAE; Agrawal et al. 2014 $R^2 > 0.97$) are quoted for context and not independently reproduced.
- **No process/microstructure features:** Composition-only features cannot capture heat treatment, rolling schedules, or phase transformations.
- **Extrapolation risk:** Trained on 312 public steel compositions; finite-sample conformal coverage is not guaranteed under distribution shift to new alloy families.
- **Not a release criterion:** Must not be used to certify or reject industrial material without independent physical testing.
