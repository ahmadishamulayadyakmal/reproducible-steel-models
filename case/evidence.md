# Evidence and claim boundary — C01

**Level from the authoritative case card:** A

| Level | What may be claimed |
|---|---|
| A | Our own numbers on public data, with our own error bars and checksums |
| B | Method reproduced on an open surrogate; journal plant numbers quoted as external literature only |
| C | Not used anywhere in this portfolio |

This case is **Level A**. Every reported performance number must be computed
here from a public dataset, public benchmark or public code+data, with an error
estimate and dataset checksum.

Journal numbers may be quoted only as external context and must be labelled as
such. No sentence may imply plant validation; the author cannot supply factory
data. Synthetic or surrogate data must be labelled in `data/SOURCES.md` and in
every figure caption.

Source policy: `CASES.md` §1 (link above). Before any figure is generated,
record the dataset and licence in `data/SOURCES.md` in this repository.

## Implemented audit (25 November 2026)

The executed claim boundary is in [`docs/reproducibility_audit.md`](../docs/reproducibility_audit.md):
five metrics computed here from D01/D04 (evidence A) are in
[`results/metrics.json`](../results/metrics.json), while the MatBench MODNet
MAE and the Y2R12 R² claims are listed there as external literature, explicitly
**not reproduced**.
