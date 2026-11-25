# C01 · Reproducibility of published steel-property models — W01–W04

> **Real industrial case dossier.** Copied from the authoritative case card in
> `CASES.md` §4 so this repository stays self-contained after it is pushed to
> GitHub. Planning links: [`CASES.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/CASES.md) ·
> [`JOURNALS.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md) ·
> [`WEEKLY_PLAN.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/WEEKLY_PLAN.md).
> **Evidence level: A** · No plant data is held in this repository.

**Repository:** `e01-infra-toolchain` · **Evidence: A** ·
**References:** R07, R08, R31, Y2R12, D01.

**Industrial problem.** Steel producers and research groups publish ML models for
mechanical properties with strong R² values, but downstream teams cannot
reproduce them: different splits, undocumented preprocessing, unpinned library
versions, and no seed control. A quality lab that adopts such a model risks
making release decisions on an unreproducible number.

**Why it happens.** No locked environment, no provenance manifest, no official
split, and no environment-independent regression test.

**Data (open, no plant data).** UCI Steel Plates Faults (D01) and MatBench
`matbench_steels` (R08). Both public, with fixed versions and checksums.

**Tool chain.** `pixi` / conda-forge + Docker → `metalkit` ingestion → pinned
scikit-learn / XGBoost baseline → MLflow run tracking → GitHub Actions on Ubuntu
and Windows → SHA-256 provenance manifest → `CITATION.cff`.

**What each reference validates.**
- R07 (Ward 2018, matminer) — featurization API and version pinning.
- R08 (Dunn 2020, MatBench) — official splits and the honest baseline comparator.
- Y2R12 (Agrawal 2014) — the fatigue dataset whose published R² is used as the
  external, non-reproduced literature number.
- R31 (Oberkampf & Roy 2010) — the V&V language used in the audit report.
- D01 — UCI Steel Plates Faults, the open regression/QC dataset.

**Deliverables.** `metalkit` CLI + pytest suite; `libthermo` Fortran kernel with
its first unit test; locked `pixi.toml`, `environment.yml`, `Dockerfile`; CI
matrix; `docs/vv_template.md`; `docs/model_card.md`; sprint notes `w01`–`w04`;
a one-page reproducibility audit showing which published numbers reproduce.

**Validation.** Same commit, two operating systems, identical metrics to 4
decimal places; `git archive w04` clean-state reproduction; explicit list of
published numbers that could **not** be reproduced. The predictive extension
adds five-seed / five-fold ExtraTrees error bars, a RandomForest comparator and
a data-derived adoption gate; see `../docs/results.md` for the measured results
and claim boundary.

**Acceptance.** `pixi run test` green; provenance manifest lists dataset checksums;
audit report distinguishes reproduced vs external numbers.

## Claim boundary

See [`evidence.md`](evidence.md) for the evidence level and the exact wording
that must be used when quoting literature numbers. All datasets and references
are listed in [`sources.md`](sources.md); the four-week execution plan is in
[`week_plan.md`](week_plan.md).
