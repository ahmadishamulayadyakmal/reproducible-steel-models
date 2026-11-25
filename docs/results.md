# C01 predictive case results

**Short answer:** C01 is now a predictive case, not only a reproducibility
audit. A deterministic RandomForest model passes an explicit, case-specific
adoption gate on public data across all five official MatBench folds. It is
**still** not a plant-validated model and **still** not a reproduction of
MODNet or the Y2R12 published R².

## Case verdict

| Item | Result |
|---|---|
| Predictive model | `RandomForestClassifier` (D01) and `RandomForestRegressor` (D04), `n_estimators=300`, `n_jobs=1`, fixed seeds |
| Error bars | D01: 5 fixed seeds; D04: 5 official folds, mean ± population std |
| Adoption gate | **PASS** — MAE at least 50% below the train-mean predictor on every fold **and** mean R² ≥ 0.70 |
| D04 MAE | **89.6300 ± 7.4424 MPa** vs train-mean **229.7445 ± 9.6958 MPa** |
| D04 R² | **0.8141 ± 0.0388** |
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
| **RandomForest (5 seeds)** | **0.6766 ± 0.0075** | **0.7526 ± 0.0176** | predictive model |

### D04 · MatBench `matbench_steels`, official five folds

Features: atomic fractions over an element vocabulary **fitted on the training
formulas only**. Unseen test elements are ignored, so the test split cannot
change the feature space. Target: yield strength in MPa.

| Fold | RF MAE (MPa) | RF RMSE (MPa) | RF R² | Train-mean MAE (MPa) | MAE reduction |
|---|---:|---:|---:|---:|---:|
| 0 | 98.7198 | 139.5679 | 0.7721 | 241.4591 | 59.12% |
| 1 | 85.2540 | 117.1999 | 0.8356 | 219.3770 | 61.14% |
| 2 | 77.5001 | 116.9214 | 0.8382 | 225.7932 | 65.68% |
| 3 | 93.8577 | 127.4795 | 0.8607 | 241.2035 | 61.09% |
| 4 | 92.8185 | 138.7267 | 0.7638 | 220.8898 | 57.98% |
| **Mean ± std** | **89.6300 ± 7.4424** | **127.9791 ± 9.8846** | **0.8141 ± 0.0388** | **229.7445 ± 9.6958** | — |

Historical Ridge baseline over the same folds: MAE **205.3600 ± 11.9359 MPa**,
R² **0.1624 ± 0.0196**. RandomForest reduces MAE by roughly **61%** relative to
that linear baseline as well.

### Adoption gate

The rule is a case-specific engineering gate, not a published material
standard:

> Adopt only if RandomForest MAE is at least 50% lower than the train-mean
> predictor on **every** official fold, and mean R² is at least 0.70.

Observed reductions are 59.12%, 61.14%, 65.68%, 61.09% and 57.98%; mean R²
is 0.8141. The gate therefore **passes**. It is evaluated only on public data.

## Published numbers that were **not** reproduced

| Source | Published number | Why it is not our result |
|---|---|---|
| [MatBench leaderboard](https://matbench.materialsproject.org/) · `matbench_steels` | MODNet v0.1.12, **87.7627 MPa MAE** | Different model and matminer featurization. Our 89.6300 MPa is close, but it is not a MODNet reproduction and must not be compared as one. |
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
