# Reproducibility of published steel-property models (C01)

## Case result (C01)

**Verdict:** predictive case — adoption gate **PASS** with nested hyperparameter
search. Inner CV selects the ExtraTrees settings using training data only;
D01 accuracy is **0.7486 ± 0.0072** over five seeds (macro F1 **0.8114 ±
0.0164**), and `matbench_steels` MAE is **77.6894 ± 7.2132 MPa** with R²
**0.8581 ± 0.0398** over the five official folds. That is **5.50 pp more D01
accuracy** and **1.87% lower D04 MAE** than fixed ExtraTrees, and 62–68% below
the train-mean predictor (229.7445 ± 9.6958 MPa) on every fold, passing the
case-specific rule "≥50% MAE reduction every fold and mean R² ≥ 0.70".
MODNet **87.7627 MPa** and Y2R12 R² **> 0.97** remain external literature,
**not reproduced**. The D04 model also reports 90% cross-conformal prediction
intervals calibrated only on training folds: **0.9198 ± 0.0304** empirical
coverage and **389.0798 ± 30.8096 MPa** mean full width. They are deliberately
conservative and are not a material release threshold. No plant data is used.

![C01 predictive scorecard](docs/figures/c01_scorecard.svg)

![C01 model comparison: D01 accuracy progression, D04 fold MAE, R² and gate](docs/figures/c01_model_comparison.svg)

Full tables, leakage control, claim boundary and remaining gaps:
[`docs/results.md`](docs/results.md). The original reproducibility audit is
still in [`docs/reproducibility_audit.md`](docs/reproducibility_audit.md).

## Industrial problem

Steel producers publish ML models for mechanical properties with strong R2 values, but downstream quality labs cannot reproduce them. A release decision may rest on an unreproducible number.

**Why it happens.** No locked environment, no provenance manifest, no official train/test split, no seed control, no cross-OS regression test.

## Data (no plant data)

Open data only: UCI Steel Plates Faults (D01, CC BY 4.0) and MatBench `matbench_steels` (R08/D04). No plant data.

> Only open datasets and published literature are used. No plant or proprietary data are held here; plant numbers quoted from papers are external literature, not independently reproduced results.

## Tool chain

`pixi` / conda-forge + Docker, `metalkit`, scikit-learn, XGBoost, MLflow, GitHub Actions (Ubuntu + Windows), SHA-256 provenance manifest, `CITATION.cff`, Zenodo-ready metadata.

## Journal references

- **R07** ([DOI](https://doi.org/10.1016/j.commatsci.2018.05.018)) — matminer featurization API and version pinning.
- **R08** ([DOI](https://doi.org/10.1038/s41524-020-00406-3)) — official MatBench splits and honest baseline comparator.
- **Y2R12** ([DOI](https://doi.org/10.1186/2193-9772-3-8)) — the fatigue dataset whose published R2 is quoted as external, non-reproduced literature.
- **R31** — V&V and claim language for the reproducibility audit.
- **D01** ([source](https://archive.ics.uci.edu/dataset/198/steel+plates+faults)) — UCI Steel Plates Faults, provenance and checksum.
- **D04** ([source](https://matbench.materialsproject.org/)) — MatBench data/version pinning.

## Deliverables

`metalkit` CLI + pytest suite; `libthermo` Fortran kernel + first unit test; locked `pixi.toml`, `environment.yml`, `Dockerfile`; CI matrix; `docs/vv_template.md`; `docs/model_card.md`; one-page reproducibility audit.

## Validation & claims

The historical pinned baselines still reproduce exactly: D01 seed 42 accuracy
**0.5013** / macro F1 **0.6207**, and `matbench_steels` fold 0 MAE
**220.0009 MPa** / RMSE **273.1735 MPa** / R² **0.1271**. The predictive
extension adds RandomForest results over five seeds and all five official
folds (D01 accuracy **0.6766 ± 0.0075**, D04 MAE **89.6300 ± 7.4424 MPa**),
then fixed ExtraTrees (D01 **0.6936 ± 0.0114**, D04 **79.1707 ± 8.6980 MPa**),
and now nested-CV ExtraTrees: D01 accuracy **0.7486 ± 0.0072**, D04 MAE
**77.6894 ± 7.2132 MPa**, R² **0.8581 ± 0.0398**. Each stage passes the
adoption gate; nested search is 1.87% below fixed ExtraTrees and 13.32% below
RandomForest on D04 MAE. Inner folds select `max_features` and
`min_samples_leaf` without touching the outer split. Every experiment payload
is executed twice and must match exactly; the suite has 18 passing tests on
`main`. Cross-conformal interval calibration reuses the same inner folds on the
outer training split and never touches the outer test split.
Input checksums, the source fingerprint and package versions are recorded in
`results/provenance.json`. The one-page
[reproducibility audit](docs/reproducibility_audit.md) remains the historical
record and lists the published numbers that were **not** reproduced
(MatBench MODNet MAE 87.7627 MPa and the Y2R12 R² > 0.97 claim). Cross-OS and clean-checkout verification details are recorded in [`docs/reproducibility_audit.md`](docs/reproducibility_audit.md).

## Limitations

No plant data. Only two open datasets are used; a published R2 that we did not
reproduce is labelled external literature, never our result. The RandomForest
and nested / fixed ExtraTrees models are statistical, composition-only, and not
calibrated prediction intervals; they must not be used for plant release
decisions without independent data. MODNet / matminer featurization is not
reproduced here, so the numerically lower nested MAE is not a like-for-like
benchmark win. The nested grid is deliberately small and auditable, not an
exhaustive optimizer run.

## Repository layout

- `README.md` — case summary, data policy, method, results and limitations.
- `CONTRIBUTING.md` — how to propose changes.
- `docs/index.md` — documentation map.
- `docs/model_card.md` and `docs/vv_template.md` — reporting templates.
- `.github/workflows/ci.yml` — automated checks.

Only open data and published literature are used. No plant or proprietary data
are included. All artefacts are written in English.
