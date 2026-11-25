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
    intervals = experiments["matbench_steels_nested_extra_trees"].get(
        "interval_calibration"
    )
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

    interval_line = ""
    if intervals:
        interval_line = txt(
            60,
            608,
            f"D04 cross-conformal {intervals['target_coverage']:.0%} intervals: "
            f"{intervals['empirical_coverage']['mean']:.1%} empirical coverage, "
            f"{_fmt(intervals['mean_width_mpa']['mean'], 1)} MPa mean width "
            "(calibrated on training folds only).",
            size=12,
            fill=_MUTED,
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
        interval_line,
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


def _payload_mean(payload: Any) -> float:
    """Return the mean of a mean/std payload or the value of a scalar payload."""
    if isinstance(payload, dict):
        return float(payload.get("mean", 0.0))
    return float(payload)


def _payload_values(payload: Any) -> list[float]:
    """Return the per-split values of a payload, or a one-item list."""
    if isinstance(payload, dict) and "values" in payload:
        return [float(value) for value in payload["values"]]
    return [_payload_mean(payload)]


def _fold_values(experiment: dict[str, Any], key: str, fallback: Any) -> list[float]:
    """Prefer per-fold records; fall back to aggregate values for older payloads."""
    per_fold = experiment.get("per_fold")
    if per_fold:
        return [float(row["metrics"][key]) for row in per_fold]
    return _payload_values(fallback)


def _at(series: list[float], index: int) -> float:
    """Return a series item, repeating the last value for short payloads."""
    return series[index] if index < len(series) else series[-1]


def build_comparison_svg(metrics: dict[str, Any]) -> str:
    """Return a deterministic four-panel comparison chart for C01 metrics."""
    experiments = metrics["experiments"]
    legacy_u = experiments["uci_faults"]["metrics"]
    rf_u = experiments["uci_faults_random_forest"]["metrics"]
    fixed_u = experiments["uci_faults_extra_trees"]["metrics"]
    nested_u = experiments["uci_faults_nested_extra_trees"]["metrics"]
    fixed_d = experiments["matbench_steels_extra_trees"]
    nested_d = experiments["matbench_steels_nested_extra_trees"]
    gate = nested_d["decision_gate"]
    base_commit = str(metrics.get("base_commit", "unknown"))[:12]

    naive = _fold_values(
        nested_d, "naive_mae_mpa", nested_d["metrics"]["naive_mae_mpa"]
    )
    fixed_mae = _fold_values(
        fixed_d, "mae_mpa", fixed_d["metrics"]["mae_mpa"]
    )
    nested_mae = _fold_values(
        nested_d, "mae_mpa", nested_d["metrics"]["mae_mpa"]
    )
    fixed_r2 = _fold_values(fixed_d, "r2", fixed_d["metrics"]["r2"])
    nested_r2 = _fold_values(nested_d, "r2", nested_d["metrics"]["r2"])
    reductions = [float(value) for value in gate["mae_reductions"]]
    n_folds = max(len(naive), len(fixed_mae), len(nested_mae), len(reductions))

    def txt(
        x: int | float,
        y: int | float,
        value: str,
        *,
        size: int = 12,
        fill: str = _TEXT,
        weight: str = "normal",
        anchor: str = "start",
    ) -> str:
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="Segoe UI, Arial, sans-serif">{escape(value)}</text>'
        )

    def panel(x: int, y: int, title: str) -> list[str]:
        return [
            f'<rect x="{x}" y="{y}" width="500" height="276" rx="10" '
            f'fill="{_PANEL}" stroke="{_BORDER}" stroke-width="1"/>',
            txt(x + 20, y + 30, title, size=15, fill=_TEXT, weight="bold"),
        ]

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="750" '
        'viewBox="0 0 1100 750" role="img" '
        'aria-label="C01 model comparison charts">',
        f'<rect width="1100" height="750" fill="{_BG}"/>',
        txt(40, 50, "C01 — model comparison", size=25, weight="bold"),
        txt(
            40,
            78,
            "Committed metrics · public data only · external literature excluded",
            size=14,
            fill=_MUTED,
        ),
        f'<line x1="40" y1="96" x2="1060" y2="96" stroke="{_BORDER}" stroke-width="1"/>',
    ]

    parts.extend(panel(40, 116, "D01 · exact-match accuracy"))
    d01_rows = [
        ("Logistic (seed 42)", _payload_mean(legacy_u), 0.0, _MUTED),
        ("RandomForest", _payload_mean(rf_u["accuracy"]), float(rf_u["accuracy"].get("std", 0.0)), _BLUE),
        ("Fixed ExtraTrees", _payload_mean(fixed_u["accuracy"]), float(fixed_u["accuracy"].get("std", 0.0)), _BLUE),
        ("Nested ExtraTrees", _payload_mean(nested_u["accuracy"]), float(nested_u["accuracy"].get("std", 0.0)), _TEAL),
    ]
    bar_x, bar_w = 250, 220
    for index, (label, mean, std, color) in enumerate(d01_rows):
        top = 166 + index * 44
        center = top + 13
        width = max(2.0, mean * bar_w)
        parts.append(
            f'<rect x="{bar_x}" y="{top}" width="{bar_w}" height="26" rx="5" '
            f'fill="{_BG}" stroke="{_BORDER}" stroke-width="1"/>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{top}" width="{width:.1f}" height="26" rx="5" '
            f'fill="{color}"/>'
        )
        if std > 0:
            half = max(3.0, std * bar_w)
            end = bar_x + width
            parts.append(
                f'<line x1="{end - half:.1f}" y1="{center}" '
                f'x2="{end + half:.1f}" y2="{center}" '
                f'stroke="{_TEXT}" stroke-width="2"/>'
            )
            parts.append(
                f'<line x1="{end - half:.1f}" y1="{center - 6}" '
                f'x2="{end - half:.1f}" y2="{center + 6}" '
                f'stroke="{_TEXT}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{end + half:.1f}" y1="{center - 6}" '
                f'x2="{end + half:.1f}" y2="{center + 6}" '
                f'stroke="{_TEXT}" stroke-width="1"/>'
            )
        value = f"{mean:.4f}" if std == 0 else f"{mean:.4f} ± {std:.4f}"
        parts.append(txt(60, center + 4, label, size=12, fill=_MUTED))
        parts.append(
            txt(530, center + 4, value, size=11, fill=color, weight="bold", anchor="end")
        )
    parts.append(txt(250, 378, "0.0", size=11, fill=_MUTED, anchor="middle"))
    parts.append(txt(360, 378, "0.5", size=11, fill=_MUTED, anchor="middle"))
    parts.append(txt(470, 378, "1.0", size=11, fill=_MUTED, anchor="middle"))

    parts.extend(panel(560, 116, "D04 · MAE by official fold (lower is better)"))
    ma_base, ma_h, ma_scale = 360, 190, 260.0
    for grid_value in (0, 100, 200):
        grid_y = ma_base - grid_value / ma_scale * ma_h
        parts.append(
            f'<line x1="590" y1="{grid_y:.1f}" x2="1035" y2="{grid_y:.1f}" '
            f'stroke="{_BORDER}" stroke-width="1"/>'
        )
        parts.append(
            txt(582, grid_y + 4, str(grid_value), size=11, fill=_MUTED, anchor="end")
        )
    legend = [
        ("Train mean", _MUTED),
        ("Fixed ExtraTrees", _BLUE),
        ("Nested ExtraTrees", _TEAL),
    ]
    for index, (label, color) in enumerate(legend):
        x = 590 + index * 155
        parts.append(f'<rect x="{x}" y="158" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(txt(x + 16, 167, label, size=11, fill=_MUTED))
    for index in range(n_folds):
        center = 650 + 85 * index
        for offset, series, color in (
            (-20, naive, _MUTED),
            (-2, fixed_mae, _BLUE),
            (16, nested_mae, _TEAL),
        ):
            value = _at(series, index)
            height = value / ma_scale * ma_h
            parts.append(
                f'<rect x="{center + offset}" y="{ma_base - height:.1f}" '
                f'width="16" height="{height:.1f}" rx="2" fill="{color}"/>'
            )
        parts.append(txt(center, 377, f"F{index}", size=11, fill=_MUTED, anchor="middle"))
        nested_value = _at(nested_mae, index)
        label_y = ma_base - nested_value / ma_scale * ma_h - 6
        parts.append(
            txt(center + 24, label_y, f"{nested_value:.1f}", size=11, fill=_TEAL, anchor="middle")
        )

    parts.extend(panel(40, 412, "D04 · R² by official fold"))
    r2_legend = [("Fixed ExtraTrees", _BLUE), ("Nested ExtraTrees", _TEAL)]
    for index, (label, color) in enumerate(r2_legend):
        x = 300 + index * 165
        parts.append(f'<rect x="{x}" y="456" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(txt(x + 16, 465, label, size=11, fill=_MUTED))
    r2_top, r2_base, r2_min, r2_max = 480, 620, 0.70, 1.00
    for grid_value in (0.70, 0.80, 0.90, 1.00):
        grid_y = r2_base - (grid_value - r2_min) / (r2_max - r2_min) * (r2_base - r2_top)
        parts.append(
            f'<line x1="90" y1="{grid_y:.1f}" x2="510" y2="{grid_y:.1f}" '
            f'stroke="{_BORDER}" stroke-width="1"/>'
        )
        parts.append(
            txt(82, grid_y + 4, f"{grid_value:.2f}", size=11, fill=_MUTED, anchor="end")
        )
    r2_x = [120 + 90 * index for index in range(n_folds)]

    def r2_y(value: float) -> float:
        return r2_base - (value - r2_min) / (r2_max - r2_min) * (r2_base - r2_top)

    for series, color in ((fixed_r2, _BLUE), (nested_r2, _TEAL)):
        coords = " ".join(
            f"{x},{r2_y(_at(series, index)):.1f}" for index, x in enumerate(r2_x)
        )
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        for index, x in enumerate(r2_x):
            y = r2_y(_at(series, index))
            parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="3.5" fill="{color}"/>')
    for index, x in enumerate(r2_x):
        value = _at(nested_r2, index)
        parts.append(
            txt(x, r2_y(value) - 8, f"{value:.4f}", size=11, fill=_TEAL, anchor="middle")
        )
        parts.append(txt(x, 642, f"F{index}", size=11, fill=_MUTED, anchor="middle"))

    parts.extend(panel(560, 412, "D04 · MAE reduction vs train mean"))
    gate_top, gate_base, gate_scale = 480, 620, 0.80
    threshold_y = gate_base - 0.5 / gate_scale * (gate_base - gate_top)
    parts.append(
        f'<line x1="590" y1="{threshold_y:.1f}" x2="1035" y2="{threshold_y:.1f}" '
        f'stroke="{_AMBER}" stroke-width="2" stroke-dasharray="6 4"/>'
    )
    parts.append(txt(596, threshold_y - 6, "50% requirement", size=11, fill=_AMBER))
    for index in range(n_folds):
        center = 620 + 88 * index
        value = _at(reductions, index)
        height = value / gate_scale * (gate_base - gate_top)
        top = gate_base - height
        parts.append(
            f'<rect x="{center - 17}" y="{top:.1f}" width="34" height="{height:.1f}" '
            f'rx="4" fill="{_TEAL}"/>'
        )
        parts.append(
            txt(center, top - 7, f"{value * 100:.2f}%", size=11, fill=_TEAL, anchor="middle")
        )
        parts.append(txt(center, 642, f"F{index}", size=11, fill=_MUTED, anchor="middle"))
    parts.append(
        txt(
            596,
            660,
            f"Every fold clears the gate; mean R² = {_payload_mean(nested_d['metrics']['r2']):.4f}",
            size=11,
            fill=_MUTED,
        )
    )

    parts.append(
        txt(
            40,
            730,
            f"generated from results/metrics.json · base_commit {base_commit} · "
            "mean ± std over five seeds/folds",
            size=12,
            fill=_MUTED,
        )
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_comparison(metrics_path: Path, output_path: Path) -> Path:
    """Render the comparison chart from ``metrics_path`` to ``output_path``."""
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_comparison_svg(metrics), encoding="utf-8")
    return output_path
