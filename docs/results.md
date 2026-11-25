# C01 case results — what was actually solved

**Short answer:** C01 is a completed **reproducibility case**, not a completed
high-accuracy steel-property prediction case. The formal `CASES.md` §7 case
gate is met and the tag `c01` exists, but the measured models here are
deliberately simple baselines. They show that a downstream lab can regenerate
our numbers exactly; they do **not** reproduce the strong published numbers
that motivated the case.

## Case verdict

A downstream lab can reproduce all five of our metrics from public inputs, a
pinned environment and a recorded split. The published high scores cited by
the case — MatBench MODNet MAE **87.7627 MPa** and Y2R12 fatigue R² **> 0.97**
— remain **external literature**: this repository does not reproduce them and
does not claim plant validation.

The industrial conclusion is therefore a **go/no-go decision on evidence**, not
a new predictive model:

> A published steel-property number should not be adopted for a release
> decision from the paper alone. In this case, public data plus a pinned
> environment were enough to reproduce our baseline numbers exactly, but not
> enough to reproduce the published high scores. Adoption requires the
> author's split, featurization and environment, or an independent dataset.

## Result at a glance

![C01 reproducibility scorecard generated from results/metrics.json](figures/c01_scorecard.svg)

The figure is generated from [`../results/metrics.json`](../results/metrics.json)
by `python -m metalkit.cli report`. No plotting dependency is added.

## Reproduced numbers — our results (evidence A)

| Experiment | Protocol | Metric | Our value |
|---|---|---|---|
| D01 fault classification | 27 features, 7 multi-hot labels, stratified 80/20 split, seed 42, 1552 train / 389 test | Exact-match accuracy | **0.5013** |
| D01 fault classification | as above | Macro F1 | **0.6207** |
| D04 `matbench_steels` | official fold 0, 249 train / 63 test, 14-element composition vector + Ridge(alpha=1.0) | MAE | **220.0009 MPa** |
| D04 `matbench_steels` | as above | RMSE | **273.1735 MPa** |
| D04 `matbench_steels` | as above | R² | **0.1271** |

Each experiment ran twice with metrics equal to four decimal places. Input
checksums, the source fingerprint and package versions are in
[`../results/provenance.json`](../results/provenance.json). Cross-OS equality
was verified in GitHub Actions run `45545998166` on Ubuntu and Windows.

## Published numbers that were **not** reproduced

| Source | Published number | Why it is not our result |
|---|---|---|
| [MatBench leaderboard](https://matbench.materialsproject.org/) · `matbench_steels` | MODNet v0.1.12, **87.7627 MPa MAE** | Different model and matminer featurization; no MODNet implementation is present here. |
| Agrawal *et al.* 2014, DOI [10.1186/2193-9772-3-8](https://doi.org/10.1186/2193-9772-3-8) | **R² > 0.97** (~0.98 LOOCV) | The NIMS fatigue dataset (D05) is unavailable here, so the protocol cannot be recomputed. |

Full detail, including claim boundaries, is in
[`reproducibility_audit.md`](reproducibility_audit.md).

## What is still needed for a stronger solved case

These items are **not** required by the current `c01` gate, but they are what
would turn this from a reproducibility demonstration into a convincing
predictive case:

1. **Error bars.** Run multiple seeds for D01 and all five official MatBench
   folds; report mean ± standard deviation, not only one split.
2. **A stronger comparator.** Add XGBoost / Random Forest and, if the R07
   matminer stack is installed, an honest MODNet-style featurized baseline.
3. **Feature provenance.** Pin the exact featurizer version rather than using
   only a raw composition vector, so the R07 validation role becomes measurable.
4. **Run tracking.** Record trials in MLflow or an equivalent immutable run
   table, linked to the same dataset checksums.
5. **A decision rule.** State an acceptance threshold (for example, "adopt only
   if fold-wise MAE ≤ X MPa") and report whether the case passes it.

Until then, the honest headline is: **reproducibility solved, predictive
performance not claimed**.

## Regenerate the displayed result

```bash
python -m metalkit.cli reproduce --data-dir data/raw --output-dir results
python -m metalkit.cli report --metrics results/metrics.json \
    --output docs/figures/c01_scorecard.svg
python -m pytest
```

Or with `just`:

```bash
just reproduce
just figures
just test-py
```

## Claim boundary

Evidence level **A**: public datasets and our own computation. No plant data
was used. Every number in the "not reproduced" table is quoted from external
literature and is explicitly not our measured result.
