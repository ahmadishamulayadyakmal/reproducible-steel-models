"""Render the C01 predictive case scorecard from committed metrics.

The figure uses only the Python standard library so it can be regenerated in
the pinned environment without adding a plotting dependency.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

_EXTERNAL_FATIGUE_R2 = "> 0.97"

_BG = "#ffffff"
_PANEL = "#f6f8fb"
_BORDER = "#d8dee9"
_TEXT = "#17202c"
_MUTED = "#5b6673"
_BLUE = "#1d4ed8"
_TEAL = "#0f766e"
_AMBER = "#b45309"
_BLUE_TINT = "#eff6ff"
_BLUE_BORDER = "#bfdbfe"
_GREEN_TINT = "#ecfdf5"
_GREEN_BORDER = "#a7f3d0"


def _fmt(value: Any, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def _stat(payload: dict[str, Any], suffix: str = "") -> str:
    """Render a mean ± std payload, or a plain legacy scalar."""
    if "mean" in payload and "std" in payload:
        return f"{_fmt(payload['mean'])}{suffix} ± {_fmt(payload['std'])}{suffix}"
    return f"{_fmt(payload.get('mean', payload))}{suffix}"


def build_scorecard_svg(metrics: dict[str, Any]) -> str:
    """Return a deterministic SVG scorecard for the C01 metrics dictionary."""
    experiments = metrics["experiments"]
    summary = metrics["summary"]
    nested_u = experiments["uci_faults_nested_extra_trees"]["metrics"]
    nested_d = experiments["matbench_steels_nested_extra_trees"]["metrics"]
    gate = experiments["matbench_steels_nested_extra_trees"]["decision_gate"]
    et_u = experiments["uci_faults_extra_trees"]["metrics"]
    et_d = experiments["matbench_steels_extra_trees"]["metrics"]
    legacy_u = experiments["uci_faults"]["metrics"]
    legacy_d = experiments["matbench_steels"]["metrics"]

    base_commit = str(metrics.get("base_commit", "unknown"))[:12]
    passed = bool(gate["passed"])
    verdict = "PASS" if passed else "FAIL"
    gate_fill = _GREEN_TINT if passed else _BLUE_TINT
    gate_border = _GREEN_BORDER if passed else _BLUE_BORDER
    gate_text = _TEAL if passed else _AMBER

    def txt(
        x: int,
        y: int,
        value: str,
        *,
        size: int = 15,
        fill: str = _TEXT,
        weight: str = "normal",
        anchor: str = "start",
    ) -> str:
        return (
            f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="Segoe UI, Arial, sans-serif">{escape(value)}</text>'
        )

    def row(y: int, label: str, value: str, accent: str, *, x: int = 60) -> str:
        return (
            f'<rect x="{x}" y="{y - 24}" width="400" height="34" rx="6" '
            f'fill="{_BG}" stroke="{_BORDER}" stroke-width="1"/>'
            + txt(x + 12, y, label, size=14, fill=_MUTED)
            + txt(
                x + 388,
                y,
                value,
                size=14,
                fill=accent,
                weight="bold",
                anchor="end",
            )
        )

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="660" '
        'viewBox="0 0 980 660" role="img" '
        'aria-label="C01 predictive case scorecard">',
        f'<rect width="980" height="660" fill="{_BG}"/>',
        txt(40, 50, "C01 — predictive case scorecard", size=25, weight="bold"),
        txt(
            40,
            78,
            "Nested-CV ExtraTrees · 5 seeds / 5 official folds · inner CV on train only",
            size=14,
            fill=_MUTED,
        ),
        f'<line x1="40" y1="96" x2="940" y2="96" stroke="{_BORDER}" stroke-width="1"/>',
        f'<rect x="40" y="116" width="440" height="300" rx="10" fill="{_PANEL}" '
        f'stroke="{_BORDER}" stroke-width="1"/>',
        txt(
            60,
            146,
            "PREDICTIVE MODEL — ours (mean ± std)",
            size=15,
            fill=_TEAL,
            weight="bold",
        ),
        row(190, "D01 exact-match accuracy", _stat(nested_u["accuracy"]), _TEAL),
        row(232, "D01 macro F1", _stat(nested_u["macro_f1"]), _TEAL),
        row(274, "D04 yield strength MAE", _stat(nested_d["mae_mpa"], " MPa"), _TEAL),
        row(316, "D04 yield strength RMSE", _stat(nested_d["rmse_mpa"], " MPa"), _TEAL),
        row(358, "D04 yield strength R²", _stat(nested_d["r2"]), _TEAL),
        txt(
            60,
            398,
            "inner CV selects max_features / min_samples_leaf on train only",
            size=12,
            fill=_MUTED,
        ),
        f'<rect x="500" y="116" width="440" height="300" rx="10" fill="{_PANEL}" '
        f'stroke="{_BORDER}" stroke-width="1"/>',
        txt(
            520,
            146,
            "BASELINE / EXTERNAL — context only",
            size=15,
            fill=_AMBER,
            weight="bold",
        ),
        row(
            182,
            "Logistic D01 accuracy",
            _fmt(legacy_u["accuracy"]),
            _MUTED,
            x=520,
        ),
        row(
            216,
            "Fixed ExtraTrees D01 accuracy",
            _fmt(et_u["accuracy"]["mean"]),
            _MUTED,
            x=520,
        ),
        row(
            250,
            "Ridge D04 MAE (fold 0)",
            f"{_fmt(legacy_d['mae_mpa'])} MPa",
            _MUTED,
            x=520,
        ),
        row(
            284,
            "Fixed ExtraTrees D04 MAE",
            f"{_fmt(et_d['mae_mpa']['mean'])} MPa",
            _MUTED,
            x=520,
        ),
        row(
            318,
            "MODNet MAE — external",
            f"{_fmt(summary['external_comparator_mae_mpa'])} MPa",
            _AMBER,
            x=520,
        ),
        row(
            352,
            "Y2R12 fatigue R² — external",
            _EXTERNAL_FATIGUE_R2,
            _AMBER,
            x=520,
        ),
        txt(
            520,
            398,
            "external numbers are not reproduced by this repository",
            size=12,
            fill=_AMBER,
        ),
        f'<rect x="40" y="436" width="900" height="184" rx="10" '
        f'fill="{gate_fill}" stroke="{gate_border}" stroke-width="1"/>',
        txt(60, 468, f"Adoption gate: {verdict}", size=16, fill=gate_text, weight="bold"),
        txt(
            60,
            498,
            "MAE reduction vs train-mean on all five folds: "
            + ", ".join(f"{_fmt(value, 2)}" for value in gate["mae_reductions"]),
            size=14,
        ),
        txt(
            60,
            526,
            "Requirement: >= 50% on every fold and mean R2 >= 0.70; "
            f"train-mean MAE {_fmt(nested_d['naive_mae_mpa']['mean'])} MPa, "
            f"observed mean R2 = {_fmt(gate['mean_r2'])}.",
            size=14,
        ),
        txt(
            60,
            554,
            f"Nested search: MAE {_fmt(summary['d04_mae_improvement_vs_fixed_extra_trees'] * 100, 1)}% "
            f"below fixed ExtraTrees; D01 accuracy +{_fmt(summary['d01_accuracy_gain_vs_fixed_extra_trees_pp'], 2)} pp. "
            f"Our {_fmt(summary['d04_nested_mae_mpa'])} MPa is not a MODNet reproduction.",
            size=14,
        ),
        txt(
            60,
            584,
            "No plant data. No MODNet reproduction and no plant validation is claimed.",
            size=14,
            fill=_AMBER,
            weight="bold",
        ),
        txt(
            40,
            642,
            f"generated from results/metrics.json · base_commit {base_commit}",
            size=12,
            fill=_MUTED,
        ),
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def write_scorecard(metrics_path: Path, output_path: Path) -> Path:
    """Render ``metrics_path`` to ``output_path`` and return the output path."""
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_scorecard_svg(metrics), encoding="utf-8")
    return output_path
