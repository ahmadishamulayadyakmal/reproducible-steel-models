"""Tests for the deterministic Case 01 publication-style SVG figures."""

import json

from metalkit.cli import main
from metalkit.report import build_comparison_svg, build_scorecard_svg


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
                    "empirical_coverage": {
                        "mean": 0.9198,
                        "std": 0.0304,
                        "values": [0.8889, 0.9683, 0.9194, 0.9355, 0.8871],
                    },
                    "mean_width_mpa": {
                        "mean": 389.0798,
                        "std": 30.8096,
                        "values": [369.0, 421.7, 406.9, 409.3, 338.5],
                    },
                },
                "per_fold": [
                    {
                        "fold": 0,
                        "metrics": {
                            "mae_mpa": 90.6403,
                            "naive_mae_mpa": 241.4591,
                            "r2": 0.8000,
                        },
                    },
                    {
                        "fold": 1,
                        "metrics": {
                            "mae_mpa": 69.8296,
                            "naive_mae_mpa": 219.3770,
                            "r2": 0.8927,
                        },
                    },
                    {
                        "fold": 2,
                        "metrics": {
                            "mae_mpa": 78.7737,
                            "naive_mae_mpa": 225.7932,
                            "r2": 0.8526,
                        },
                    },
                    {
                        "fold": 3,
                        "metrics": {
                            "mae_mpa": 76.8826,
                            "naive_mae_mpa": 241.2035,
                            "r2": 0.9106,
                        },
                    },
                    {
                        "fold": 4,
                        "metrics": {
                            "mae_mpa": 72.3206,
                            "naive_mae_mpa": 220.8898,
                            "r2": 0.8344,
                        },
                    },
                ],
            },
        },
        "summary": {
            "headline_model": "Nested-CV ExtraTrees (inner-selected hyperparameters)",
            "case_verdict": "predictive gate passed",
            "decision_gate_passed": True,
            "d01_extra_trees_accuracy": 0.6936,
            "d01_extra_trees_accuracy_std": 0.0114,
            "d01_extra_trees_macro_f1": 0.7755,
            "d01_extra_trees_macro_f1_std": 0.0219,
            "d01_random_forest_accuracy": 0.6766,
            "d01_nested_accuracy": 0.7486,
            "d01_nested_accuracy_std": 0.0072,
            "d01_nested_macro_f1": 0.8114,
            "d01_nested_macro_f1_std": 0.0164,
            "d01_accuracy_gain_vs_fixed_extra_trees_pp": 5.50,
            "d04_extra_trees_mae_mpa": 79.1707,
            "d04_extra_trees_mae_std_mpa": 8.6980,
            "d04_extra_trees_rmse_mpa": 112.0894,
            "d04_extra_trees_r2": 0.8566,
            "d04_extra_trees_r2_std": 0.0374,
            "d04_nested_mae_mpa": 77.6894,
            "d04_nested_mae_std_mpa": 7.2132,
            "d04_nested_rmse_mpa": 111.0717,
            "d04_nested_r2": 0.8581,
            "d04_nested_r2_std": 0.0398,
            "d04_mae_improvement_vs_fixed_extra_trees": 0.0187,
            "d04_mae_improvement_vs_random_forest": 0.1332,
            "d04_random_forest_mae_mpa": 89.6300,
            "d04_naive_mae_mpa": 229.7445,
            "external_comparator_mae_mpa": 87.7627,
            "external_comparator_note": "external literature, not reproduced",
        },
    }


def test_scorecard_is_deterministic_and_shows_predictive_metrics():
    first = build_scorecard_svg(_sample_metrics())
    second = build_scorecard_svg(_sample_metrics())

    assert first == second
    assert "Table 1" in first
    assert "Case 01" in first
    assert "Nested ExtraTrees" in first
    assert "0.7486 ± 0.0072" in first
    assert "0.8114 ± 0.0164" in first
    assert "77.6894 ± 7.2132" in first
    assert "111.0717 ± 12.3347" in first
    assert "0.8581 ± 0.0398" in first
    assert "79.1707 ± 8.6980" in first
    assert "Adoption Gate: PASS" in first
    assert "1.9%" in first
    assert "+5.50 pp" in first
    assert "87.7627 MPa MAE" in first
    assert "Not Independently Reproduced" in first
    assert "Cross-conformal 90% PI" in first
    assert "92.0%" in first
    assert "389.1 ± 30.8 MPa" in first


def test_comparison_chart_is_deterministic_and_uses_fold_metrics():
    first = build_comparison_svg(_sample_metrics())
    second = build_comparison_svg(_sample_metrics())

    assert first == second
    assert "Fig. 1" in first
    assert "UCI Steel Plates Faults — exact-match accuracy" in first
    # Regression test: Logistic baseline must plot 0.5013 (not 0.0000)
    assert "0.5013" in first
    assert "0.7486 ± 0.0072" in first
    assert "MatBench Steels — yield-strength MAE by official fold" in first
    assert "90.6" in first
    assert "MatBench Steels — coefficient of determination (R²)" in first
    assert "0.9106" in first
    assert "50% requirement" in first
    assert "62.46%" in first
    assert "MODNet" not in first


def test_report_command_writes_svg(tmp_path, capsys):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_sample_metrics()), encoding="utf-8")
    output_path = tmp_path / "figures" / "scorecard.svg"

    assert main(["report", "--metrics", str(metrics_path), "--output", str(output_path)]) == 0
    assert output_path.exists()
    assert "Table 1" in output_path.read_text(encoding="utf-8")
    comparison = output_path.with_name("c01_model_comparison.svg")
    assert comparison.exists()
    assert "Fig. 1" in comparison.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out
