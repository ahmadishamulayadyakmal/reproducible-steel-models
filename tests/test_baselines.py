"""Baseline and predictive-model tests; integration test needs raw datasets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from metalkit.baselines import (
    CONFORMAL_TARGET_COVERAGE,
    CompositionVectorizer,
    NESTED_MATBENCH_PARAM_GRID,
    NESTED_UCI_PARAM_GRID,
    composition_features,
    composition_matrix,
    composition_vocabulary,
    conformal_half_width,
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


def test_composition_vectorizer_is_refitted_by_sklearn_cloning():
    vectorizer = CompositionVectorizer().fit(["Fe80C20"])
    first = vectorizer.transform(["Fe79C20Ni1"])

    assert first.shape == (1, 2)
    refitted = CompositionVectorizer().fit(["Fe70C20Ni10"])
    assert refitted.transform(["Fe69C20Ni10Cu1"]).shape == (1, 3)


def test_nested_grids_are_small_and_leakage_safe_keys():
    assert len(NESTED_UCI_PARAM_GRID) == 2
    assert len(NESTED_MATBENCH_PARAM_GRID) == 2
    for grid in (NESTED_UCI_PARAM_GRID, NESTED_MATBENCH_PARAM_GRID):
        assert all(key.startswith("model__") for key in grid)
        assert 1.0 in grid["model__max_features"]


def test_conformal_half_width_is_deterministic_and_alpha_responsive():
    compositions = np.asarray(
        [f"Fe{80 - index}C{index}Ni10" for index in range(40)], dtype=object
    )
    target = np.arange(40, dtype=float) * 2.0
    params = {"max_features": 1.0, "min_samples_leaf": 1}

    wide = conformal_half_width(compositions, target, params, alpha=0.10)
    narrow = conformal_half_width(compositions, target, params, alpha=0.50)
    again = conformal_half_width(compositions, target, params, alpha=0.10)

    assert wide > 0.0
    assert wide == again
    assert wide >= narrow


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
        "uci_faults_extra_trees",
        "matbench_steels_extra_trees",
        "uci_faults_nested_extra_trees",
        "matbench_steels_nested_extra_trees",
    }
    for experiment in result["experiments"].values():
        assert "n_samples" in experiment
        assert any(
            key in experiment for key in ("n_train", "n_runs", "n_folds")
        )
        json.dumps(experiment)
        for payload in experiment["metrics"].values():
            if isinstance(payload, dict):
                assert set(payload) == {"mean", "std", "values"}
            else:
                assert round(payload, 4) == payload

    nested_u = result["experiments"]["uci_faults_nested_extra_trees"]
    nested_d = result["experiments"]["matbench_steels_nested_extra_trees"]
    assert nested_u["candidate_count"] == 4
    assert nested_d["candidate_count"] == 6
    assert all(
        set(entry["selected_params"]) == {"max_features", "min_samples_leaf"}
        for entry in nested_u["per_seed"]
    )
    assert all(
        set(entry["selected_params"]) == {"max_features", "min_samples_leaf"}
        for entry in nested_d["per_fold"]
    )
    intervals = nested_d["interval_calibration"]
    assert intervals["target_coverage"] == CONFORMAL_TARGET_COVERAGE
    assert intervals["method"].startswith("cross-conformal")
    assert 0.0 <= intervals["empirical_coverage"]["mean"] <= 1.0
    assert intervals["half_width_mpa"]["mean"] > 0.0
    assert len(intervals["empirical_coverage"]["values"]) == 5
    assert all("interval_calibration" in row for row in nested_d["per_fold"])

    summary = result["summary"]
    assert summary["headline_model"].startswith("Nested-CV ExtraTrees")
    assert summary["decision_gate_passed"] is True
    assert summary["nested_search"]["d01_inner_cv"]["folds"] == 3
    assert summary["nested_search"]["d04_inner_cv"]["folds"] == 4
    assert summary["d04_nested_mae_mpa"] < 0.5 * summary["d04_naive_mae_mpa"]
    assert summary["d04_nested_r2"] >= 0.70
    assert summary["d04_mae_improvement_vs_fixed_extra_trees"] > 0.0
    assert summary["d04_mae_improvement_vs_random_forest"] > 0.0
    assert summary["d01_nested_accuracy"] > summary["d01_extra_trees_accuracy"]
    assert summary["d01_accuracy_gain_vs_fixed_extra_trees_pp"] > 0.0
    assert summary["d01_nested_accuracy_std"] >= 0.0
    assert summary["d04_interval_target_coverage"] == CONFORMAL_TARGET_COVERAGE
    assert 0.0 <= summary["d04_interval_empirical_coverage"] <= 1.0
    assert summary["d04_interval_half_width_mpa"] > 0.0
    assert summary["d04_interval_mean_width_mpa"] > 0.0
