# Four-week execution plan — C01

**Sprint window:** W01, W02, W03, W04 · **Case tag:** `c01`

From `WEEKLY_PLAN.md` §3. The planning repository keeps the full 52-week table.

| Week | Sprint | Concrete deliverable | Refs | Evidence |
|---|---|---|---|---|
| W01 | Reproducibility audit setup | Folder structure, case-driven `README.md` with `## Journal references`, `LICENSE`, `CITATION.cff`, `justfile`, `data/SOURCES.md` | R07, R08 | A |
| W02 | Locked environment | `pixi.toml` / `environment.yml`, `Dockerfile`, CI (Python + Fortran build) on Ubuntu + Windows | R31 | A |
| W03 | Baseline reproduction attempt | Reproduce one published steel-property score from D01/D04; document what fails and why | R07, Y2R12 | A |
| W04 | Case report + `metalkit` | `metalkit` CLI + pytest, provenance manifest, `c01` tag, 1-page reproducibility audit with reproduced vs external numbers | R08, R31, D01 | A |

## Weekly Definition of Done

1 merged PR · green tests · 1 new artefact · 1 README paragraph · 1 sprint note `docs/sprints/wNN.md` · tag `wNN`.

Review weeks W13, W26, W39 and W52 are slip buffers, not feature time. Tag `cNN` only after all six README sections are complete.
