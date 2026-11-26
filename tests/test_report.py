"""Tests for the deterministic Case 01 publication-style SVG figures."""

import json

from metalkit.cli import main
from metalkit.report import (
    build_comparison_svg,
    build_diagnostics_svg,
    build_scorecard_svg,
)


def _sample_metrics() -> dict:
    return {
        "base_commit": "0123456789abcdef",
        "seed": 42,
        "experiments": {
            "uci_faults": {"metrics": {"accuracy": 0.5013, "macro_f1": 0.6207}},
            "matbench_steels": {
                "fold": 0,
                "metrics": {
                    "mae_mpa": 220.0009,
                    "rmse_mpa": 273.1735,
                    "r2": 0.1271,
                },
            },
            "uci_faults_random_forest": {
                "metrics": {
                    "accuracy": {"mean": 0.6766, "std": 0.0075},
                    "macro_f1": {"mean": 0.7526, "std": 0.0176},
                }
            },
            "matbench_steels_random_forest": {
                "metrics": {
                    "mae_mpa": {"mean": 89.6300, "std": 7.4424},
                    "rmse_mpa": {"mean": 127.9791, "std": 9.8846},
                    "r2": {"mean": 0.8141, "std": 0.0388},
                    "naive_mae_mpa": {"mean": 229.7445, "std": 9.6958},
                },
                "decision_gate": {
                    "passed": True,
                    "mean_r2": 0.8141,
                    "mae_reductions": [0.59, 0.61, 0.66, 0.61, 0.58],
                },
            },
            "uci_faults_extra_trees": {
                "metrics": {
                    "accuracy": {"mean": 0.6936, "std": 0.0114},
                    "macro_f1": {"mean": 0.7755, "std": 0.0219},
                }
            },
            "matbench_steels_extra_trees": {
                "metrics": {
                    "mae_mpa": {"mean": 79.1707, "std": 8.6980},
                    "rmse_mpa": {"mean": 112.0894, "std": 12.5902},
                    "r2": {"mean": 0.8566, "std": 0.0374},
                    "naive_mae_mpa": {"mean": 229.7445, "std": 9.6958},
                },
                "decision_gate": {
                    "passed": True,
                    "mean_r2": 0.8566,
                    "mae_reductions": [0.62, 0.69, 0.65, 0.64, 0.67],
                },
                "per_fold": [
                    {"fold": 0, "metrics": {"mae_mpa": 90.9130, "r2": 0.7990}},
                    {"fold": 1, "metrics": {"mae_mpa": 67.7081, "r2": 0.8991}},
                    {"fold": 2, "metrics": {"mae_mpa": 77.9893, "r2": 0.8567}},
                    {"fold": 3, "metrics": {"mae_mpa": 86.9427, "r2": 0.8938}},
                    {"fold": 4, "metrics": {"mae_mpa": 72.3003, "r2": 0.8344}},
                ],
            },
            "uci_faults_nested_extra_trees": {
                "metrics": {
                    "accuracy": {"mean": 0.7486, "std": 0.0072},
                    "macro_f1": {"mean": 0.8114, "std": 0.0164},
                }
            },
            "uci_faults_multiclass_ensemble": {
                "class_names": [
                    "Pastry",
                    "Z_Scratch",
                    "K_Scatch",
                    "Stains",
                    "Dirtiness",
                    "Bumps",
                    "Other_Faults",
                ],
                "metrics": {
                    "accuracy": {"mean": 0.8185, "std": 0.0066},
                    "macro_f1": {"mean": 0.8319, "std": 0.0118},
                },
                "confusion_matrix_normalized": [
                    [0.80, 0.02, 0.01, 0.00, 0.00, 0.07, 0.10],
                    [0.01, 0.88, 0.01, 0.00, 0.00, 0.02, 0.08],
                    [0.00, 0.00, 0.94, 0.00, 0.00, 0.01, 0.05],
                    [0.00, 0.00, 0.00, 0.92, 0.00, 0.02, 0.06],
                    [0.00, 0.00, 0.00, 0.00, 0.85, 0.05, 0.10],
                    [0.04, 0.01, 0.01, 0.00, 0.01, 0.78, 0.15],
                    [0.05, 0.02, 0.02, 0.01, 0.01, 0.12, 0.77],
                ],
            },
            "matbench_steels_nested_extra_trees": {
                "metrics": {
                    "mae_mpa": {"mean": 77.6894, "std": 7.2132},
                    "rmse_mpa": {"mean": 111.0717, "std": 12.3347},
                    "r2": {"mean": 0.8581, "std": 0.0398},
                    "naive_mae_mpa": {"mean": 229.7445, "std": 9.6958},
                },
                "decision_gate": {
                    "passed": True,
                    "mean_r2": 0.8581,
                    "mae_reductions": [0.6246, 0.6817, 0.6511, 0.6813, 0.6726],
                },
                "interval_calibration": {
                    "method": "cross-conformal out-of-fold residuals on the outer training split",
                    "target_coverage": 0.90,
                    "empirical_coverage": {"mean": 0.9198, "std": 0.0304},
                    "mean_width_mpa": {"mean": 389.0798, "std": 30.8096},
                },
                "per_fold": [
                    {"fold": 0, "metrics": {"mae_mpa": 90.6403, "naive_mae_mpa": 241.4591, "r2": 0.8000}},
                    {"fold": 1, "metrics": {"mae_mpa": 69.8296, "naive_mae_mpa": 219.3770, "r2": 0.8927}},
                    {"fold": 2, "metrics": {"mae_mpa": 78.7737, "naive_mae_mpa": 225.7932, "r2": 0.8526}},
                    {"fold": 3, "metrics": {"mae_mpa": 76.8826, "naive_mae_mpa": 241.2035, "r2": 0.9106}},
                    {"fold": 4, "metrics": {"mae_mpa": 72.3206, "naive_mae_mpa": 220.8898, "r2": 0.8344}},
                ],
            },
            "matbench_steels_physics_hybrid": {
                "metrics": {
                    "mae_mpa": {"mean": 76.9500, "std": 7.1000},
                    "rmse_mpa": {"mean": 110.2000, "std": 12.1000},
                    "r2": {"mean": 0.8610, "std": 0.0380},
                    "naive_mae_mpa": {"mean": 229.7445, "std": 9.6958},
                },
                "decision_gate": {
                    "passed": True,
                    "mean_r2": 0.8610,
                    "mae_reductions": [0.6300, 0.6850, 0.6550, 0.6840, 0.6760],
                },
                "adaptive_interval": {
                    "target_coverage": 0.90,
                    "empirical_coverage": {"mean": 0.9010, "std": 0.0410},
                    "mean_width_mpa": {"mean": 339.7000, "std": 45.4000},
                    "median_width_mpa": {"mean": 282.0000, "std": 28.0000},
                },
                "parity_points": [
                    {"fold": 0, "observed_mpa": 1200.0, "predicted_mpa": 1245.0, "half_width_mpa": 140.0},
                    {"fold": 1, "observed_mpa": 1850.0, "predicted_mpa": 1810.0, "half_width_mpa": 160.0},
                ],
                "per_fold": [
                    {"fold": 0, "metrics": {"mae_mpa": 89.3000, "naive_mae_mpa": 241.4591, "r2": 0.8050}},
                    {"fold": 1, "metrics": {"mae_mpa": 69.1000, "naive_mae_mpa": 219.3770, "r2": 0.8950}},
                    {"fold": 2, "metrics": {"mae_mpa": 77.9000, "naive_mae_mpa": 225.7932, "r2": 0.8560}},
                    {"fold": 3, "metrics": {"mae_mpa": 76.2000, "naive_mae_mpa": 241.2035, "r2": 0.9120}},
                    {"fold": 4, "metrics": {"mae_mpa": 71.5000, "naive_mae_mpa": 220.8898, "r2": 0.8370}},
                ],
            },
        },
        "summary": {
            "headline_model": "UCI 7-class Ensemble + MatBench Hybrid Physics-ET",
            "case_verdict": "predictive gate passed",
            "decision_gate_passed": True,
            "d01_accuracy_gain_vs_fixed_extra_trees_pp": 5.50,
            "d01_multiclass_gain_vs_nested_pp": 6.99,
            "d04_mae_improvement_vs_fixed_extra_trees": 0.0187,
            "d04_mae_improvement_vs_random_forest": 0.1332,
            "external_comparator_mae_mpa": 87.7627,
            "external_comparator_note": "external literature, not reproduced",
        },
    }


def test_scorecard_is_deterministic_and_shows_headline_metrics():
    first = build_scorecard_svg(_sample_metrics())
    second = build_scorecard_svg(_sample_metrics())

    assert first == second
    assert "Table 1" in first
    assert "0.8185 ± 0.0066" in first
    assert "0.8319 ± 0.0118" in first
    assert "76.9500 ± 7.1000" in first
    assert "Adoption Gate: PASS" in first
    assert "Adaptive 90% PI" in first
    assert "282.0 MPa" in first
    assert "87.7627 MPa MAE" in first
    assert "Not Independently Reproduced" in first


def test_comparison_chart_is_deterministic_and_fixes_logistic_bar():
    first = build_comparison_svg(_sample_metrics())
    second = build_comparison_svg(_sample_metrics())

    assert first == second
    assert "Fig. 1" in first
    assert "0.5013" in first
    assert "7-Class ET + GBC" in first
    assert "0.8185 ± 0.0066" in first
    assert "Hybrid Physics-ET" in first
    assert "50% requirement" in first
    assert "MODNet" not in first


def test_diagnostics_chart_is_deterministic_and_renders_all_three_panels():
    first = build_diagnostics_svg(_sample_metrics())
    second = build_diagnostics_svg(_sample_metrics())

    assert first == second
    assert "Fig. 2" in first
    assert "Yield-strength parity" in first
    assert "Residuals &amp; adaptive 90% PI bounds" in first
    assert "UCI 7-class confusion matrix" in first
    assert "Median 90% width = 282.0 MPa" in first


def test_report_command_writes_all_three_svgs(tmp_path, capsys):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_sample_metrics()), encoding="utf-8")
    output_path = tmp_path / "figures" / "scorecard.svg"

    assert main(["report", "--metrics", str(metrics_path), "--output", str(output_path)]) == 0
    assert output_path.exists()
    assert output_path.with_name("c01_model_comparison.svg").exists()
    assert output_path.with_name("c01_diagnostics.svg").exists()
    assert "wrote" in capsys.readouterr().out
