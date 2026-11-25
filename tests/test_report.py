"""Tests for the deterministic C01 result scorecard."""

import json

from metalkit.cli import main
from metalkit.report import build_scorecard_svg


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
        },
        "summary": {
            "case_verdict": "predictive gate passed",
            "decision_gate_passed": True,
            "d01_random_forest_accuracy": 0.6766,
            "d01_random_forest_accuracy_std": 0.0075,
            "d04_random_forest_mae_mpa": 89.6300,
            "d04_random_forest_mae_std_mpa": 7.4424,
            "d04_random_forest_r2": 0.8141,
            "d04_naive_mae_mpa": 229.7445,
            "external_comparator_mae_mpa": 87.7627,
            "external_comparator_note": "external literature, not reproduced",
        },
    }


def test_scorecard_is_deterministic_and_shows_predictive_metrics():
    first = build_scorecard_svg(_sample_metrics())
    second = build_scorecard_svg(_sample_metrics())

    assert first == second
    assert "C01" in first
    assert "predictive case scorecard" in first
    assert "0.6766" in first
    assert "0.7526" in first
    assert "89.6300 MPa" in first
    assert "127.9791 MPa" in first
    assert "0.8141" in first
    assert "Adoption gate: PASS" in first
    assert "87.7627 MPa" in first
    assert "not reproduced" in first


def test_report_command_writes_svg(tmp_path, capsys):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_sample_metrics()), encoding="utf-8")
    output_path = tmp_path / "figures" / "scorecard.svg"

    assert main(["report", "--metrics", str(metrics_path), "--output", str(output_path)]) == 0
    assert output_path.exists()
    assert "C01" in output_path.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out
