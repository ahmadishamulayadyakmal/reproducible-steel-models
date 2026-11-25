# C01 predictive case results

**Short answer:** yes, the first RandomForest model was decent; it is now
improved. The current headline model is a deterministic **ExtraTrees** ensemble
that passes the explicit adoption gate with a larger margin on public data.
It is **still** not a plant-validated model and **still** not a reproduction of
MODNet or the Y2R12 published R².

## Case verdict

| Item | Result |
|---|---|
| Headline model | `ExtraTreesClassifier` / `ExtraTreesRegressor`, `n_estimators=500`, `n_jobs=1`, fixed seeds |
| Comparator kept | `RandomForest` (`n_estimators=300`) remains in `results/metrics.json` |
| Error bars | D01: 5 fixed seeds; D04: 5 official folds, mean ± population std |
| Adoption gate | **PASS** — MAE at least 50% below the train-mean predictor on every fold **and** mean R² ≥ 0.70 |
| D04 MAE | **79.1707 ± 8.6980 MPa** vs train-mean **229.7445 ± 9.6958 MPa** |
| D04 R² | **0.8566 ± 0.0374** |
| Gain over RandomForest | **11.67% lower MAE** (79.1707 vs 89.6300 MPa) |
| Claim boundary | Public data only. No plant data, no MODNet reproduction, no plant validation. |

![C01 predictive scorecard generated from results/metrics.json](figures/c01_scorecard.svg)

The figure is generated from [`../results/metrics.json`](../results/metrics.json)
by `python -m metalkit.cli report`; no plotting dependency was added.

## Predictive results — our numbers (evidence A)

### D01 · UCI Steel Plates Faults

Protocol: 27 features, 7 multi-hot fault labels, stratified 80/20 split,
five fixed seeds `(42, 7, 11, 19, 23)`, exact-match accuracy and macro F1.

| Model | Accuracy | Macro F1 | Note |
|---|---|---|---|
| Logistic baseline (seed 42) | 0.5013 | 0.6207 | historical reproducibility baseline |
| RandomForest (5 seeds) | 0.6766 ± 0.0075 | 0.7526 ± 0.0176 | first predictive model |
| **ExtraTrees (5 seeds)** | **0.6936 ± 0.0114** | **0.7755 ± 0.0219** | current headline model |

### D04 · MatBench `matbench_steels`, official five folds

Features: atomic fractions over an element vocabulary **fitted on the training
formulas only**. Unseen test elements are ignored, so the test split cannot
change the feature space. Target: yield strength in MPa.

| Fold | ExtraTrees MAE (MPa) | RMSE (MPa) | R² | Train-mean MAE (MPa) | MAE reduction |
|---|---:|---:|---:|---:|---:|
| 0 | 90.9130 | 131.0813 | 0.7990 | 241.4591 | 62.35% |
| 1 | 67.7081 | 91.8266 | 0.8991 | 219.3770 | 69.14% |
| 2 | 77.9893 | 110.0521 | 0.8567 | 225.7932 | 65.46% |
| 3 | 86.9427 | 111.3278 | 0.8938 | 241.2035 | 63.95% |
| 4 | 72.3003 | 116.1594 | 0.8344 | 220.8898 | 67.27% |
| **Mean ± std** | **79.1707 ± 8.6980** | **112.0894 ± 12.5902** | **0.8566 ± 0.0374** | **229.7445 ± 9.6958** | — |

Comparators over the same folds: RandomForest MAE **89.6300 ± 7.4424 MPa**,
R² **0.8141 ± 0.0388**; Ridge MAE **205.3600 ± 11.9359 MPa**, R²
**0.1624 ± 0.0196**. ExtraTrees reduces MAE by **11.67%** relative to the
RandomForest model and about **65%** relative to the train-mean predictor.

### Adoption gate

The rule is a case-specific engineering gate, not a published material
standard:

> Adopt only if the headline ensemble MAE is at least 50% lower than the
> train-mean predictor on **every** official fold, and mean R² is at least 0.70.

Observed reductions are 62.35%, 69.14%, 65.46%, 63.95% and 67.27%; mean R²
is 0.8566. The gate therefore **passes**. It is evaluated only on public data.

## Published numbers that were **not** reproduced

| Source | Published number | Why it is not our result |
|---|---|---|
| [MatBench leaderboard](https://matbench.materialsproject.org/) · `matbench_steels` | MODNet v0.1.12, **87.7627 MPa MAE** | Different model and matminer featurization. Our 79.1707 MPa is numerically lower, but this is **not** a like-for-like reproduction and must not be advertised as beating a published model without a matched featurization/protocol audit. |
| Agrawal *et al.* 2014, DOI [10.1186/2193-9772-3-8](https://doi.org/10.1186/2193-9772-3-8) | **R² > 0.97** (~0.98 LOOCV) | The NIMS fatigue dataset (D05) is unavailable here, so the protocol cannot be recomputed. |

The earlier reproducibility audit, including the exact claim boundary, is in
[`reproducibility_audit.md`](reproducibility_audit.md).

## What is still missing

1. **MODNet / matminer featurization** (R07) is not installed, so the external
   benchmark is context only, not a like-for-like reproduction.
2. **No plant data.** The model cannot be claimed validated on industrial
   measurements; see [`evidence.md`](../case/evidence.md).
3. **No calibrated intervals.** Mean ± std describes split variability, not a
   prediction interval for a new alloy.
4. **Small public dataset.** 312 steels and a composition-only descriptor limit
   extrapolation outside the observed composition range.
5. **No physics constraints.** The model is statistical, not CALPHAD- or
   thermodynamics-informed.
6. **No nested hyperparameter search.** The ExtraTrees setting was selected from
   a small deterministic comparison on the official folds; a nested CV study
   would be needed before calling it tuned.

## Regenerate the displayed result

```bash
python -m metalkit.cli reproduce --data-dir data/raw --output-dir results
python -m metalkit.cli report --metrics results/metrics.json \
    --output docs/figures/c01_scorecard.svg
python -m pytest
```

Or with `just`:

```bash
just reproduce
just figures
just test-py
```

## Claim boundary

Evidence level **A**: public datasets and our own computation. No plant data
was used. Every number in the "not reproduced" table is quoted from external
literature and is explicitly not our measured result.
