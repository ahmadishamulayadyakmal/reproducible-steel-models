# Reproducibility of published steel-property models (C01)

> Workspace folder: `e01-infra-toolchain` · Suggested GitHub repository: `metallurgy-infra-toolchain`
> Epic: E01 · Weeks: W01–W04 · Evidence level: **A**
> Master specification: [`CASES.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/CASES.md) §4 · Download the papers: [`JOURNALS.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md)

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
manual download route in [`JOURNALS.md`](https://github.com/ahmadishamulayadyakmal/metallurgy-project/blob/main/JOURNALS.md) §4, and in the shared
BibTeX library `papers/references.bib`. Do not cite a paper you have not been
able to obtain; if it is inaccessible, record that in `JOURNALS.md` §8.

## Deliverables

`metalkit` CLI + pytest suite; `libthermo` Fortran kernel + first unit test; locked `pixi.toml`, `environment.yml`, `Dockerfile`; CI matrix; `docs/vv_template.md`; `docs/model_card.md`; sprint notes `w01`–`w04`; one-page reproducibility audit.

## Validation & claims

Same commit, two operating systems, identical metrics to 4 decimal places; `git archive w04` clean-state reproduction; explicit list of published numbers that could NOT be reproduced.

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

## Push this folder to GitHub

This folder is prepared but is **not** a Git repository yet:

```bash
cd e01-infra-toolchain
git init
git branch -M main
git remote add origin https://github.com/<your-user>/metallurgy-infra-toolchain.git
git add .
git commit -m "Initial import: C01 · W01–W04"
git push -u origin main
```

Use weekly tags `wNN` and one case tag `c01` inside this repository.
Never commit API keys, raw downloaded datasets or publisher PDFs.

## Language

All artefacts in this repository are written in **English**.
