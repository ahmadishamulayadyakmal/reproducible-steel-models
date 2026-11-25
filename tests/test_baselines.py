"""Baseline tests; the integration test needs the gitignored raw datasets."""

from __future__ import annotations

from pathlib import Path

import pytest

from metalkit.baselines import composition_features, reproduce
from metalkit.datasets import DATA_FILES

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_READY = all((DATA_DIR / entry[0]).is_file() for entry in DATA_FILES.values())


def test_composition_features_are_scale_invariant():
    scaled, elements = composition_features(["Fe0.8C0.2", "Fe80C20"])

    assert elements == ["C", "Fe"]
    assert scaled[0].tolist() == pytest.approx(scaled[1].tolist())


@pytest.mark.skipif(not RAW_READY, reason="raw datasets not downloaded; see data/SOURCES.md")
def test_reproduce_is_deterministic_and_records_provenance():
    result = reproduce(DATA_DIR, seed=42, fold=0)

    assert result["determinism_check"]
    assert len(result["code_fingerprint"]) == 64
    assert set(result["data"]) == set(DATA_FILES)
    for entry in result["data"].values():
        assert len(entry["sha256"]) == 64
        assert entry["sha256"] == DATA_FILES[
            next(k for k, v in DATA_FILES.items() if v[0] == entry["file"])
        ][1]

    for experiment in result["experiments"].values():
        assert experiment["n_train"] > 0
        assert experiment["n_test"] > 0
        for metric in experiment["metrics"].values():
            assert round(metric, 4) == metric
