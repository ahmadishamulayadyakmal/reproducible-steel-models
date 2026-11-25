# Reproducibility of published steel-property models (C01)

> Workspace folder: `e01-infra-toolchain` · Suggested GitHub repository: `reproducible-steel-models`
> Epic: E01 · Weeks: W01–W04 · Evidence level: **A**
> Master specification: [`CASES.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/CASES.md) §4 · Download the papers: [`JOURNALS.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md)

## Case result (C01)

**Verdict:** reproducibility solved, predictive performance not claimed. Our own
pinned baselines regenerate exactly from public data: D01 accuracy **0.5013** /
macro F1 **0.6207**, and `matbench_steels` fold 0 MAE **220.0009 MPa** / RMSE
**273.1735 MPa** / R² **0.1271**. The published MatBench MODNet MAE
**87.7627 MPa** and Y2R12 R² **> 0.97** stay external literature, explicitly
**not reproduced** here. No plant data is used.

![C01 case scorecard](docs/figures/c01_scorecard.svg)

Full result, figure provenance and the list of what is still needed for a
stronger predictive case: [`docs/results.md`](docs/results.md).

## Industrial problem

Steel producers publish ML models for mechanical properties with strong R2 values, but downstream quality labs cannot reproduce them. A release decision may rest on an unreproducible number.

**Why it happens.** No locked environment, no provenance manifest, no official train/test split, no seed control, no cross-OS regression test.

## Data (no plant data)

Open data only: UCI Steel Plates Faults (D01, CC BY 4.0) and MatBench `matbench_steels` (R08/D04). No plant data. Evidence level A: we report our own numbers.

> The author cannot supply factory data. This project uses **only open datasets and
> credible peer-reviewed journals**. If this is a B-level case, the case report
> must contain the exact disclaimer from `CASES.md` §1 and must **never** claim
> plant validation.

## Tool chain

`pixi` / conda-forge + Docker, `metalkit`, scikit-learn, XGBoost, MLflow, GitHub Actions (Ubuntu + Windows), SHA-256 provenance manifest, `CITATION.cff`, Zenodo-ready metadata.

## Journal references

- **R07** — matminer featurization API and version pinning.
- **R08** — official MatBench splits and honest baseline comparator.
- **Y2R12** — the fatigue dataset whose published R2 is quoted as external, non-reproduced literature.
- **R31** — V&V and claim language for the reproducibility audit.
- **D01** — UCI Steel Plates Faults, provenance and checksum.
- **D04** — MatBench data/version pinning.

Each reference above is listed with its DOI or stable URL, access status and
manual download route in [`JOURNALS.md` §4](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md). The shared BibTeX library lives in
[`metallurgy-evidence-audit/papers/references.bib`](https://github.com/ahmadishamulayadyakmal/metallurgy-evidence-audit/blob/main/papers/references.bib).
Do not cite a paper you have not been able to obtain; if it is inaccessible, record
that in [`JOURNALS.md` §8](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md).

## Deliverables

`metalkit` CLI + pytest suite; `libthermo` Fortran kernel + first unit test; locked `pixi.toml`, `environment.yml`, `Dockerfile`; CI matrix; `docs/vv_template.md`; `docs/model_card.md`; sprint notes `w01`–`w04`; one-page reproducibility audit.

## Validation & claims

Our own pinned baselines are reproducible: on D01 (seed 42, stratified 80/20)
accuracy = **0.5013** and macro F1 = **0.6207**; on `matbench_steels` official
fold 0, MAE = **220.0009 MPa**, RMSE = **273.1735 MPa** and R² = **0.1271**.
Each experiment ran twice with identical metrics to four decimals; the full
suite passes locally (12 tests on `main`; the tagged `c01` release had 10).
Input checksums, the source fingerprint and the package versions
are recorded in `results/provenance.json`. The full one-page
[reproducibility audit](docs/reproducibility_audit.md) lists the published
numbers that could **not** be reproduced (MatBench MODNet MAE 87.7627 MPa and
the Y2R12 R² > 0.97 claim), each labelled external literature. Cross-OS
equality is verified in GitHub Actions on Ubuntu
and Windows (run `45545998166`); a clean `git archive 0d3d3f1` reproduction
gave identical metrics and 10 passing tests. The case tag `c01` is applied to
the release commit.

## Limitations

No plant data. Only two open datasets are used; a published R2 that we did not reproduce is labelled external literature, never our result.

## Definition of Done

1 merged PR · green tests · 1 new artefact · 1 README paragraph · 1 sprint note
`docs/sprints/wNN.md` · tag `wNN`. Before the case tag `c01` is created,
this README must contain all six sections: Industrial problem, Data (no plant
data), Tool chain, Journal references, Validation & claims, Limitations.

## Repository skeleton

Shared files: `CONTRIBUTING.md` (sprint contract), `.github/` (issue, PR and
CI templates), `docs/sprints/wNN.md`, `docs/vv_template.md` and
`docs/model_card.md`. `CASES.md`, `JOURNALS.md` and `REPOSITORIES.md` are in a
separate planning repository; their links above remain valid after this folder
is pushed as its own repository.

The real industrial case dossier is in `case/`: `README.md` (full case card),
`evidence.md`, `sources.md` and `week_plan.md`.

## Repository status and GitHub Desktop

This folder is already a Git repository on `main`, pushed to GitHub as
`reproducible-steel-models` with an SSH `origin`. In GitHub Desktop, choose **Add local
repository** and select this folder; do not clone into the same path.

```bash
git status --short --branch
git pull --rebase origin main
git push origin main
```

Weekly work follows `CONTRIBUTING.md`: one PR, green tests, one artefact, one
README paragraph, `docs/sprints/wNN.md`, tag `wNN`. Tag `c01` only after
all six README sections are complete.


## Language

All artefacts in this repository are written in **English**.
