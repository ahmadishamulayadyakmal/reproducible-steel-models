# C01 predictive case results

**Short answer:** the predictive case now uses **nested hyperparameter search**.
An inner cross-validation selects `max_features` and `min_samples_leaf` using
only the outer training split; the untouched outer test split supplies the
reported score. The case-specific adoption gate still **passes**. This remains
a public-data screening model, not a plant-validated model and not a
reproduction of MODNet or the Y2R12 published R².

## Case verdict

| Item | Result |
|---|---|
| Headline model | `ExtraTreesClassifier` / `ExtraTreesRegressor`, `n_estimators=300`, `n_jobs=1`, fixed seeds |
| Search | D01: 3-fold inner CV, macro F1, 4 candidates; D04: 4-fold inner CV, negative MAE, 6 candidates |
| Leakage control | Inner CV and the composition vectorizer are fitted inside each outer training split only |
| Comparators kept | Fixed ExtraTrees (500 trees), RandomForest, Ridge and logistic payloads remain in `results/metrics.json` |
| Error bars | D01: 5 fixed seeds; D04: 5 official folds, mean ± population std |
| Adoption gate | **PASS** — MAE at least 50% below train-mean on every fold **and** mean R² ≥ 0.70 |
| D04 MAE | **77.6894 ± 7.2132 MPa** vs train-mean **229.7445 ± 9.6958 MPa** |
| D04 R² | **0.8581 ± 0.0398** |
| D01 accuracy | **0.7486 ± 0.0072** (macro F1 **0.8114 ± 0.0164**) |
| Gain vs fixed ExtraTrees | D01 accuracy **+5.50 pp**; D04 MAE **1.87% lower** |
| Claim boundary | Public data only. No plant data, no MODNet reproduction, no plant validation. |

![C01 predictive scorecard generated from results/metrics.json](figures/c01_scorecard.svg)

![C01 model comparison generated from results/metrics.json](figures/c01_model_comparison.svg)

Both figures are generated from [`../results/metrics.json`](../results/metrics.json)
by `python -m metalkit.cli report`; no plotting dependency was added. The
comparison chart shows the D01 accuracy progression, D04 fold-level MAE and R²,
and the five fold-wise MAE reductions against the 50% gate.

## Nested-search protocol

1. **Outer split** is untouched for tuning: five stratified 80/20 seeds for D01,
   five official MatBench folds for D04.
2. **Inner CV** runs on the outer training rows only: `KFold(shuffle=True)`,
   3 folds for D01 and 4 folds for D04, fixed `random_state`.
3. **Grid** is small and fixed: `max_features ∈ {0.5, 1.0}` and
   `min_samples_leaf ∈ {1, 2}` for D01; `max_features ∈ {0.5, 1.0}` and
   `min_samples_leaf ∈ {1, 2, 4}` for D04.
4. **Selection** uses macro F1 for multi-label D01 and MAE for D04.
5. **Refit** happens on the full outer training split, then one prediction is
   made on the outer test split. Every payload is executed twice and must match
   exactly.

For D04 the `CompositionVectorizer` is a pipeline step, so scikit-learn clones
and refits the element vocabulary on each inner training split. An inner
validation composition cannot change the feature space it is scored on. The
outer test composition never enters the vocabulary.

`results/metrics.json` records `selected_params` and the inner best score for
every seed/fold, so the search is auditable rather than a single opaque score.

## Predictive results — our numbers (evidence A)

### D01 · UCI Steel Plates Faults

Protocol: 27 features, 7 multi-hot fault labels, stratified 80/20 split,
five fixed seeds `(42, 7, 11, 19, 23)`, exact-match accuracy and macro F1.

| Model | Accuracy | Macro F1 | Note |
|---|---|---|---|
| Logistic baseline (seed 42) | 0.5013 | 0.6207 | historical reproducibility baseline |
| RandomForest (5 seeds) | 0.6766 ± 0.0075 | 0.7526 ± 0.0176 | first predictive model |
| Fixed ExtraTrees, 500 trees (5 seeds) | 0.6936 ± 0.0114 | 0.7755 ± 0.0219 | fixed-setting comparator |
| **Nested ExtraTrees, 300 trees** | **0.7486 ± 0.0072** | **0.8114 ± 0.0164** | current headline model |

The inner search selects `max_features=1.0` and `min_samples_leaf=1` on every
seed; the fixed ExtraTrees classifier uses scikit-learn's default
`max_features="sqrt"`. This selection, made without touching the test split,
explains most of the D01 gain. Inner best macro F1 values are
0.7814, 0.8017, 0.7946, 0.7915 and 0.7697.

### D04 · MatBench `matbench_steels`, official five folds

Target: yield strength in MPa. Features are atomic fractions over a vocabulary
fitted on training formulas only.

| Fold | Nested MAE (MPa) | RMSE (MPa) | R² | Train-mean MAE (MPa) | MAE reduction | Selected params |
|---|---:|---:|---:|---:|---:|---|
| 0 | 90.6403 | 130.7447 | 0.8000 | 241.4591 | 62.46% | `max_features=1.0, min_samples_leaf=1` |
| 1 | 69.8296 | 94.6921 | 0.8927 | 219.3770 | 68.17% | `max_features=1.0, min_samples_leaf=2` |
| 2 | 78.7737 | 111.6064 | 0.8526 | 225.7932 | 65.11% | `max_features=0.5, min_samples_leaf=1` |
| 3 | 76.8826 | 102.1649 | 0.9106 | 241.2035 | 68.13% | `max_features=1.0, min_samples_leaf=2` |
| 4 | 72.3206 | 116.1503 | 0.8344 | 220.8898 | 67.26% | `max_features=1.0, min_samples_leaf=1` |
| **Mean ± std** | **77.6894 ± 7.2132** | **111.0717 ± 12.3347** | **0.8581 ± 0.0398** | **229.7445 ± 9.6958** | — | — |

Comparators over the same official folds: fixed ExtraTrees MAE
**79.1707 ± 8.6980 MPa**, RandomForest **89.6300 ± 7.4424 MPa**, Ridge
**205.3600 ± 11.9359 MPa**. Nested search lowers MAE by **1.87%** versus fixed
ExtraTrees and **13.32%** versus RandomForest. Inner best MAE values are
78.9405, 89.6257, 86.8691, 89.8328 and 84.8205 MPa.

### Adoption gate

> Adopt only if the headline ensemble MAE is at least 50% lower than the
> train-mean predictor on **every** official fold, and mean R² is at least 0.70.

Observed reductions are 62.46%, 68.17%, 65.11%, 68.13% and 67.26%; mean R² is
0.8581. The gate therefore **passes**. It is a case-specific engineering rule,
not a published material standard, and is evaluated only on public data.

### D04 prediction intervals

The nested model now reports 90% cross-conformal intervals. Four-fold
out-of-fold absolute residuals are collected from the **outer training split**
with the selected hyperparameters, and the empirical quantile at
`ceil((n + 1) × 0.90) / n` sets the half-width. The outer test fold never
contributes to the width or the quantile.

| Quantity | Mean ± std over five official folds |
|---|---:|
| Empirical coverage (target 90%) | **0.9198 ± 0.0304** |
| Interval half-width | **194.5399 ± 15.4048 MPa** |
| Interval full width | **389.0798 ± 30.8096 MPa** |

Per-fold coverage is 0.8889, 0.9683, 0.9194, 0.9355 and 0.8871. Coverage meets
the 90% target on average, but the intervals are wide: out-of-fold residuals
on 249 training rows per fold are much larger than the held-out MAE. This is a
calibrated uncertainty statement for these public folds, **not** a release
decision threshold. Finite-sample coverage is not guaranteed for a new alloy.

## Published numbers that were **not** reproduced

| Source | Published number | Why it is not our result |
|---|---|---|
| [MatBench leaderboard](https://matbench.materialsproject.org/) · `matbench_steels` | MODNet v0.1.12, **87.7627 MPa MAE** | Different model and matminer featurization. Our 77.6894 MPa is numerically lower, but this is **not** a like-for-like reproduction and must not be advertised as beating a published model without a matched featurization/protocol audit. |
| Agrawal *et al.* 2014, DOI [10.1186/2193-9772-3-8](https://doi.org/10.1186/2193-9772-3-8) | **R² > 0.97** (~0.98 LOOCV) | The NIMS fatigue dataset (D05) is unavailable here, so the protocol cannot be recomputed. |

The earlier reproducibility audit, including the exact claim boundary, is in
[`reproducibility_audit.md`](reproducibility_audit.md).

## What is still missing

1. **MODNet / matminer featurization** (R07) is not installed, so the external
   benchmark is context only, not a like-for-like reproduction.
2. **No plant data.** The model cannot be claimed validated on industrial
   measurements; it is a public-data study only.
3. **Wide intervals.** Cross-conformal 90% intervals are calibrated on the
   public folds but average ~389 MPa wide; they do not support a material
   release decision.
4. **Small public dataset.** 312 steels and a composition-only descriptor limit
   extrapolation outside the observed composition range.
5. **No physics constraints.** The model is statistical, not CALPHAD- or
   thermodynamics-informed.
6. **No repeated nested search over a larger grid.** The current small grid is
   auditable and cheap; a broader search would need more compute and a fresh
   clean-state record.

## Regenerate the displayed result

```bash
python -m metalkit.cli reproduce --data-dir data/raw --output-dir results
python -m metalkit.cli report --metrics results/metrics.json
python -m pytest
```

Or with `just`:

```bash
just reproduce
just figures
just test-py
```

## Claim boundary

All reported results come from public datasets and our own computation. No
plant data was used. Every number in the "not reproduced" table is quoted from
external literature and is explicitly not our measured result.
