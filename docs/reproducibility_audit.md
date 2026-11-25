# C01 reproducibility audit — 25 November 2026

**Scope.** Can a downstream lab reproduce a steel-property number from public
inputs, a pinned environment and a recorded split? This audit reports only
**our own** numbers as reproducible results. Published numbers are quoted as
**external literature** and are explicitly marked *not reproduced*. Evidence
level: **A** (public data, our own computation). No plant data was used.

## Artefacts and provenance

| Item | Value |
|---|---|
| Code fingerprint (SHA-256 of `src/metalkit/*.py`) | `66adf9742e8438d8c60239f84b8170c89016490e20c605abbb7b65d8cd810776` |
| Base commit when results were generated (`base_commit` in JSON) | `37f1b545bd4e4ebb335ce0dfc0198620cf28c82c` |
| Result files | `results/metrics.json`, `results/provenance.json` |
| D01 UCI Steel Plates Faults | `cb8eb9859198b63f053e443513036b401746fa517ef58bd17c846c6741c93919` · 100890 B |
| D04 MatBench steels | `473bc4957b2ea5e6465aef84bc29bb48ac34db27d69ea4ec5f508745c6fae252` · 8836 B |
| D04 official five folds | `ef3bc6cf09ec08a23a8d0a6f1e04c0e2108296644d5e522abd8900f55e2b1a4f` · 42676 B |
| Split metadata | `random_state=18012019`, `shuffle=true`; fold 0 fingerprint `24d9ae1e2baa71a3d359b3d1c5ef1addbebc1a593985aa1e61db60a5c854d744` |
| Environment | Python 3.12.10 (local), numpy 2.1.3, pandas 2.2.3, scipy 1.14.1, scikit-learn 1.5.2, joblib 1.4.2, threadpoolctl 3.5.0 |

`data/raw/` is gitignored: the datasets are re-downloaded from the URLs in
[`data/SOURCES.md`](../data/SOURCES.md) and checked against those hashes before
any number is produced.

## Reproduced numbers — our results (A)

| Experiment | Protocol | Our metric | Value |
|---|---|---|---|
| D01 fault classification | 27 features, 7 multi-hot labels, stratified 80/20 split, `seed=42`, StandardScaler + OneVsRestClassifier(LogisticRegression, `max_iter=2000`) | accuracy (exact multi-label match) | **0.5013** |
| D01 fault classification | as above, 1552 train / 389 test | macro F1 | **0.6207** |
| D04 yield strength | official fold 0, 249 train / 63 test, atomic-fraction composition vector (14 elements) + Ridge(`alpha=1.0`, Cholesky) | MAE | **220.0009 MPa** |
| D04 yield strength | as above | RMSE | **273.1735 MPa** |
| D04 yield strength | as above | R² | **0.1271** |

Each experiment was run twice in the same environment; all five metrics matched
to four decimal places. `pytest`: **10 passed**. These are deliberately simple
baselines: the point is that the number can be regenerated exactly, not that it
is competitive.

## Published numbers that were NOT reproduced

| Source | Published number (exact as quoted) | Why it is not our result |
|---|---|---|
| [MatBench leaderboard](https://matbench.materialsproject.org/) · `matbench_steels`, general-purpose best | **87.7627 MPa MAE**, MODNet (v0.1.12), 312 samples, five official folds (R08/D04) | No MODNet model or matminer featurization is present in this repository. Our composition-only Ridge score (220.0009 MPa) is a separate, weaker baseline and must not be compared as a reproduction of MODNet. |
| Y2R12 (Agrawal *et al.* 2014, DOI [10.1186/2193-9772-3-8](https://doi.org/10.1186/2193-9772-3-8)) | Abstract: "R² values over 0.97"; Results: "R² values ∼0.98, and error rate <4%" with LOOCV on 437 instances | The NIMS fatigue dataset (D05) is not available in this repository, so the LOOCV protocol and Table 2 values cannot be recomputed. These figures are external literature only and imply no plant validation. |

No per-model Table 2 numbers from Y2R12 are transcribed here because the
full-size table was not obtainable as machine-readable text; inventing them
would violate the provenance rule in `CASES.md` §1.

## Reproduce locally

```bash
# 1. Download the three files listed in data/SOURCES.md into data/raw/.
# 2. Create the pinned environment (or use pixi / Docker).
micromamba create -f environment.yml && micromamba activate metallurgy-portfolio
python -m pip install --no-deps -e .
python -m metalkit.cli reproduce --data-dir data/raw --output-dir results
python -m pytest
```

The command aborts on a checksum mismatch and rewrites `results/*.json` with
the verified hashes, the source fingerprint and the environment versions.

## Open verification items

- Cross-OS equality (Ubuntu + Windows) is configured in `.github/workflows/ci.yml`
  but has **not yet been observed**: CI has not run on the published repository.
- `git archive` reproduction from a clean tag is pending the case tag `c01`.
- `pixi`, Docker, `just`, `gfortran` and `fpm` are not installed on the
  development host; Python tests were run locally, Fortran tests only in CI.
