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
        },
    }


def test_scorecard_is_deterministic_and_shows_metrics():
    first = build_scorecard_svg(_sample_metrics())
    second = build_scorecard_svg(_sample_metrics())

    assert first == second
    assert "C01" in first
    assert "0.5013" in first
    assert "0.6207" in first
    assert "220.0009 MPa" in first
    assert "273.1735 MPa" in first
    assert "0.1271" in first
    assert "not reproduced" in first
    assert "87.7627 MPa" in first
    assert "0.97" in first


def test_report_command_writes_svg(tmp_path, capsys):
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps(_sample_metrics()), encoding="utf-8")
    output_path = tmp_path / "figures" / "scorecard.svg"

    assert main(["report", "--metrics", str(metrics_path), "--output", str(output_path)]) == 0
    assert output_path.exists()
    assert "C01" in output_path.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out
