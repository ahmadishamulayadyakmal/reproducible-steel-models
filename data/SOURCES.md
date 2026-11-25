# Data sources — C01 / E01

All data in this repository is **open**. No plant data is used or stored.
Raw files are downloaded into `data/raw/` and are **gitignored**; only this
manifest and the derived, deterministic result JSON files are committed.

Retrieved on **2026-11-25** by `curl --ssl-no-revoke` (UCI) and the GitHub
Contents API / `raw.githubusercontent.com` (MatBench). SHA-256 values below
were computed on the exact bytes downloaded; re-download and compare before
running the reproducibility experiment.

| ID | Local file (gitignored) | Upstream URL | SHA-256 | Bytes | Purpose |
|---|---|---|---|---|---|
| D01 | `data/raw/steel_plates_faults.zip` | [UCI Steel Plates Faults](https://archive.ics.uci.edu/static/public/198/steel+plates+faults.zip), DOI [10.24432/C5J88N](https://doi.org/10.24432/C5J88N) | `cb8eb9859198b63f053e443513036b401746fa517ef58bd17c846c6741c93919` | 100890 | Deterministic fault-classification baseline; provenance demo. Contains `Faults.NNA` (1941 rows × 27 features + 7 binary fault labels) and `Faults27x7_var` (variable names). Licence: CC BY 4.0. |
| D04 | `data/raw/matbench_steels.json.gz` | [matbench_v0.1_Atomic_Affine_QRF/inputs/matbench_steels.json.gz](https://github.com/materialsproject/matbench/blob/main/benchmarks/matbench_v0.1_Atomic_Affine_QRF/inputs/matbench_steels.json.gz) | `473bc4957b2ea5e6465aef84bc29bb48ac34db27d69ea4ec5f508745c6fae252` | 8836 | `matbench_steels` yield-strength baseline: 312 compositions, target in MPa. Declared by R08 / D04. |
| D04-splits | `data/raw/steels_splits.json` | [matbench_v0.1_Atomic_Affine_QRF/inputs/steels_splits.json](https://github.com/materialsproject/matbench/blob/main/benchmarks/matbench_v0.1_Atomic_Affine_QRF/inputs/steels_splits.json) | `ef3bc6cf09ec08a23a8d0a6f1e04c0e2108296644d5e522abd8900f55e2b1a4f` | 42676 | Official MatBench five-fold split (`random_state=18012019`, `shuffle=true`). IDs `mb-steels-NNN` map to zero-based row `NNN-1`. |

## Integrity and claim rules

- `metalkit reproduce` recomputes all three SHA-256 values and refuses to run
  if a downloaded file differs from this table. It writes the verified hashes
  into `results/provenance.json`.
- Numbers produced from D01 and D04 are **our own** (evidence level A).
- Published scores quoted in `docs/reproducibility_audit.md` (MatBench
  leaderboard, Y2R12) are **external literature**, not our results. They were
  obtained with different models/featurization and are marked *not reproduced*.
- Publisher PDFs are never committed. See `JOURNALS.md` §1 in the planning
  repository for the full access and citation policy.
