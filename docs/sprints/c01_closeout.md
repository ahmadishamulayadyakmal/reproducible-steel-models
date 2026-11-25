# C01 closeout · reproducibility audit (W01–W04 completion)

**Epic:** E01 · **Case:** C01 · **Date:** 2026-11-25
**References:** R07, R08, R31, D01, D04; Y2R12 quoted as external literature only.

## Promised scope

- [x] Pinned raw-data manifest with SHA-256 checks (`data/SOURCES.md`)
- [x] Locked scientific package versions (numpy, pandas, scipy, scikit-learn, joblib, threadpoolctl)
- [x] Reproducible baselines on D01 and D04 with a fixed seed / official split
- [x] `results/metrics.json`, `results/provenance.json` with source fingerprint
- [x] One-page audit distinguishing reproduced vs external numbers
- [x] Python test suite green locally (10 tests)
- [x] Cross-OS CI evidence on Ubuntu + Windows (run `45545998166`, PR #1)
- [x] Clean-state reproduction from `git archive 0d3d3f1` (metrics identical, 10 tests)

## What was actually completed

- Downloaded the three open files (100890 B, 8836 B, 42676 B) from UCI and the
  MatBench GitHub repository into gitignored `data/raw/`; verified their hashes.
- Added `metalkit hash` and `metalkit reproduce`. The latter verifies checksums,
  runs each baseline twice and refuses to write results if metrics differ at
  four decimals.
- Reproduced our own numbers: D01 accuracy 0.5013 / macro F1 0.6207; D04 fold 0
  MAE 220.0009 MPa / RMSE 273.1735 MPa / R² 0.1271.
- Wrote `docs/reproducibility_audit.md`, including the published numbers that
  were **not** reproduced: MatBench MODNet 87.7627 MPa MAE and the Y2R12 R² > 0.97
  claim, both labelled external literature.
- Updated README, docs index and changelog; pinned the environment files.

## Numbers

| Quantity | Value | Reference | Difference |
|---|---|---|---|
| Python tests | 10 passed | `python -m pytest` | 0 |
| Reproduced metrics | 5 | `results/metrics.json` | 0 |
| Input files hash-verified | 3 | `data/SOURCES.md` | 0 |
| External published numbers not reproduced | 2 | audit §"Published numbers" | 0 |

## What failed / was not completed

- No MODNet / matminer reproduction: the published MatBench leaderboard MAE
  remains an external comparator, not a reproduced result.
- Y2R12 Table 2 values were not machine-readable; only the text-level claims
  (R² > 0.97, ∼0.98, error <4%) are quoted, with no invented per-model figures.
- `pixi`, Docker, `just`, `gfortran` and `fpm` are absent locally; the
  container build and local Fortran runs remain unverified. Cross-OS CI and
  Fortran tests **did** pass in GitHub Actions on both operating systems.
- The repository's Vercel deployment check fails (no web app to deploy); it is
  not part of the portfolio CI matrix.

## Technical decisions

- A source fingerprint is recorded alongside the Git commit: results can be
  tied to exact code even before the case tag exists.
- Multi-label fault classification uses OneVsRestClassifier rather than
  collapsing fault indicators, so the accuracy metric keeps its exact-match
  meaning.
- MatBench uses the repository's official five-fold split file and IDs, not a
  locally regenerated random split.

## Next week

- W05 begins E02 (`steel-data-quality-gate`): UCI loader with a `pandera`
  schema and five validation tests.
