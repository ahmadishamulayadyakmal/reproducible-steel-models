# Open Data Sources — Case 01

All datasets used in this repository are **publicly available open data**. No plant or proprietary data are stored or used. Raw files are downloaded into `data/raw/` (gitignored); only this manifest and derived deterministic JSON results are committed.

| ID | Local File (gitignored) | Upstream Source | SHA-256 | Bytes | Description |
|---|---|---|---|---:|---|
| UCI-Faults | `data/raw/steel_plates_faults.zip` | [UCI Steel Plates Faults](https://archive.ics.uci.edu/static/public/198/steel+plates+faults.zip) (DOI [10.24432/C5J88N](https://doi.org/10.24432/C5J88N)) | `cb8eb9859198b63f053e443513036b401746fa517ef58bd17c846c6741c93919` | 100,890 | 1,941 steel plates × 27 features + 7 binary fault labels (`Faults.NNA`, `Faults27x7_var`). Licence: CC BY 4.0. |
| MatBench-Steels | `data/raw/matbench_steels.json.gz` | [matbench_steels.json.gz](https://github.com/materialsproject/matbench/blob/main/benchmarks/matbench_v0.1_Atomic_Affine_QRF/inputs/matbench_steels.json.gz) | `473bc4957b2ea5e6465aef84bc29bb48ac34db27d69ea4ec5f508745c6fae252` | 8,836 | 312 steel compositions with experimental yield strength (MPa). |
| MatBench-Splits | `data/raw/steels_splits.json` | [steels_splits.json](https://github.com/materialsproject/matbench/blob/main/benchmarks/matbench_v0.1_Atomic_Affine_QRF/inputs/steels_splits.json) | `ef3bc6cf09ec08a23a8d0a6f1e04c0e2108296644d5e522abd8900f55e2b1a4f` | 42,676 | Official MatBench 5-fold CV splits (`random_state=18012019`, `shuffle=true`). |

## Integrity & Provenance Rules

- `metalkit reproduce` recomputes all three SHA-256 digests and aborts immediately on any mismatch.
- Verified hashes, Python source fingerprints, and package versions are written to `results/provenance.json`.
- Published literature benchmarks (MatBench leaderboard; Agrawal et al., 2014) are cited by DOI as external context and are never presented as locally reproduced metrics.
