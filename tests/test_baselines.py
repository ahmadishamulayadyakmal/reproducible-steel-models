"""Baseline and predictive-model tests; integration test needs raw datasets."""

from __future__ import annotations

from pathlib import Path

import pytest

from metalkit.baselines import (
    composition_features,
    composition_matrix,
    composition_vocabulary,
    evaluate_decision_gate,
    reproduce,
)
from metalkit.datasets import DATA_FILES

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW_READY = all((DATA_DIR / entry[0]).is_file() for entry in DATA_FILES.values())


def test_composition_features_are_scale_invariant():
    scaled, elements = composition_features(["Fe0.8C0.2", "Fe80C20"])

    assert elements == ["C", "Fe"]
    assert scaled[0].tolist() == pytest.approx(scaled[1].tolist())


def test_composition_matrix_ignores_unseen_test_elements():
    vocabulary = composition_vocabulary(["Fe80C20"])
    matrix = composition_matrix(["Fe79C20Ni1"], vocabulary)

    assert vocabulary == ["C", "Fe"]
    assert matrix.shape == (1, 2)
    assert matrix[0].tolist() == pytest.approx([0.20, 0.79])


def test_decision_gate_requires_every_fold_and_mean_r2():
    passed = evaluate_decision_gate([200.0, 200.0], [90.0, 95.0], [0.80, 0.75])
    failed_fold = evaluate_decision_gate([200.0, 200.0], [90.0, 140.0], [0.80, 0.75])
    failed_r2 = evaluate_decision_gate([200.0, 200.0], [90.0, 95.0], [0.65, 0.55])

    assert passed["passed"] is True
    assert failed_fold["passed"] is False
    assert failed_r2["passed"] is False


@pytest.mark.skipif(not RAW_READY, reason="raw datasets not downloaded; see data/SOURCES.md")
def test_reproduce_is_deterministic_and_records_predictive_summary():
    result = reproduce(DATA_DIR, seed=42, fold=0)

    assert result["determinism_check"]
    assert len(result["code_fingerprint"]) == 64
    assert set(result["data"]) == set(DATA_FILES)
    for entry in result["data"].values():
        assert len(entry["sha256"]) == 64
        assert entry["sha256"] == DATA_FILES[
            next(k for k, v in DATA_FILES.items() if v[0] == entry["file"])
        ][1]

    assert set(result["experiments"]) == {
        "uci_faults",
        "matbench_steels",
        "uci_faults_random_forest",
        "matbench_steels_ridge_folds",
        "matbench_steels_random_forest",
    }
    for experiment in result["experiments"].values():
        assert "n_samples" in experiment
        assert any(
            key in experiment for key in ("n_train", "n_runs", "n_folds")
        )
        for payload in experiment["metrics"].values():
            if isinstance(payload, dict):
                assert set(payload) == {"mean", "std", "values"}
            else:
                assert round(payload, 4) == payload

    summary = result["summary"]
    assert summary["decision_gate_passed"] is True
    assert summary["d04_random_forest_mae_mpa"] < 0.5 * summary["d04_naive_mae_mpa"]
    assert summary["d04_random_forest_r2"] >= 0.70
    assert summary["d01_random_forest_accuracy_std"] >= 0.0
