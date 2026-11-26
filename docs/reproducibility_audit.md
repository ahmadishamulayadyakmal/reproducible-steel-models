# Case 01 — Baseline Reproducibility Audit

**Scope:** Verify whether a downstream laboratory can regenerate baseline steel-property metrics identically from pinned public inputs, a locked software environment, and recorded benchmark splits. This audit reports **only our own computed numbers** as reproduced results; published literature numbers are explicitly marked *not reproduced*. **No plant or proprietary data were used.**

> **Historical record:** This audit documents the initial pinned linear baselines (`LogisticRegression` and `Ridge`) established for tag `c01`. The subsequent predictive models (RandomForest, fixed ExtraTrees, nested-CV ExtraTrees, and cross-conformal intervals) are documented in [`results.md`](results.md).

## Provenance & Pinned Inputs

| Item | Value |
|---|---|
| Result artefacts | `results/metrics.json`, `results/provenance.json` |
| UCI Steel Plates Faults (`steel_plates_faults.zip`) | SHA-256 `cb8eb9859198b63f053e443513036b401746fa517ef58bd17c846c6741c93919` · 100,890 B |
| MatBench Steels (`matbench_steels.json.gz`) | SHA-256 `473bc4957b2ea5e6465aef84bc29bb48ac34db27d69ea4ec5f508745c6fae252` · 8,836 B |
| Official 5-Fold Splits (`steels_splits.json`) | SHA-256 `ef3bc6cf09ec08a23a8d0a6f1e04c0e2108296644d5e522abd8900f55e2b1a4f` · 42,676 B |
| Split metadata | `random_state=18012019`, `shuffle=true`; fold 0 fingerprint `24d9ae1e2baa71a3d359b3d1c5ef1addbebc1a593985aa1e61db60a5c854d744` |
| Pinned core stack | Python 3.12, `numpy 2.1.3`, `pandas 2.2.3`, `scipy 1.14.1`, `scikit-learn 1.5.2`, `joblib 1.4.2`, `threadpoolctl 3.5.0` |

`data/raw/` is gitignored: datasets are downloaded from the upstream URLs in [`../data/SOURCES.md`](../data/SOURCES.md) and checked against their SHA-256 digests before any metric is computed.

## Reproduced Baseline Numbers (Our Computation)

| Experiment | Protocol | Metric | Value |
|---|---|---|---:|
| UCI Steel Plates Faults | 27 features, 7 multi-hot labels, stratified 80/20 split, `seed=42`, `StandardScaler + OneVsRest(LogisticRegression, max_iter=2000)` | Exact-match accuracy | **0.5013** |
| UCI Steel Plates Faults | Same protocol (1,552 train / 389 test) | Macro F1 | **0.6207** |
| MatBench `matbench_steels` | Official fold 0 (249 train / 63 test), atomic-fraction composition vector (14 elements) + `Ridge(alpha=1.0, solver="cholesky")` | MAE | **220.0009 MPa** |
| MatBench `matbench_steels` | Same protocol | RMSE | **273.1735 MPa** |
| MatBench `matbench_steels` | Same protocol | $R^2$ | **0.1271** |

Each experiment was executed twice consecutively in the same environment and matched to four decimal places. These intentionally simple baselines establish an exact deterministic floor prior to ensemble modeling.

## Published Numbers That Were NOT Reproduced

| Source | Published Number (As Quoted) | Why It Is Not Our Result |
|---|---|---|
| [MatBench Leaderboard](https://matbench.materialsproject.org/) (Dunn et al., 2020, DOI [10.1038/s41524-020-00406-3](https://doi.org/10.1038/s41524-020-00406-3)) | **87.7627 MPa MAE**, MODNet v0.1.12, 312 samples, 5 official folds | No MODNet model or `matminer` featurization is installed here. Our composition-only Ridge baseline (220.0009 MPa) is a distinct, simpler baseline. |
| Agrawal et al. (2014), DOI [10.1186/2193-9772-3-8](https://doi.org/10.1186/2193-9772-3-8) | Abstract: "$R^2$ values over 0.97"; Results: "$R^2$ values ~0.98, error rate <4%" (LOOCV, $n = 437$) | The NIMS fatigue dataset is not stored in this repository, so the LOOCV protocol cannot be recomputed. Quoted strictly as external literature. |

## Verification Status

- **Cross-OS CI verification:** GitHub Actions executes both Python (`pytest`) and Fortran (`fpm test`) suites on `ubuntu-latest` and `windows-latest` using the pinned `environment.yml`.
- **Clean-checkout verification:** Exporting a clean archive, re-downloading the pinned datasets from `data/SOURCES.md`, and running `metalkit reproduce` + `pytest` regenerated identical metrics across all baselines.
