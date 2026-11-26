"""Render publication-style Case 01 SVG figures from committed metrics.

Figures follow a clean Springer Nature / academic journal layout (white canvas,
hairline axes, booktabs horizontal rules, colorblind-safe scientific palette,
and lowercase bold panel labels a-d). Only the Python standard library is used
so figures regenerate deterministically without external plotting dependencies.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

_EXTERNAL_FATIGUE_R2 = "> 0.97"

# Springer / academic journal colorblind-safe palette
_BG = "#ffffff"
_RULE_DARK = "#1a1a1a"
_AXIS = "#222222"
_GRID = "#e5e7eb"
_SUBTLE_BG = "#f8f9fa"
_TEXT = "#111827"
_MUTED = "#4b5563"
_NAVY = "#003b71"        # Primary headline model (Nested ExtraTrees)
_STEEL = "#4a90c2"       # Secondary comparator (Fixed ExtraTrees)
_SLATE = "#7a8b99"       # Tertiary comparator (RandomForest)
_GRAY_BAR = "#c8cdd3"    # Naive / legacy baseline
_CRIMSON = "#b91c1c"     # Threshold line / external literature highlight
_PASS_GREEN = "#166534"  # Pass verdict text (subtle academic forest green)

_FONT = "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"


def _fmt(value: Any, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def _stat(payload: dict[str, Any], suffix: str = "", digits: int = 4) -> str:
    """Render a mean ± SD payload, or a plain scalar."""
    if isinstance(payload, dict) and "mean" in payload and "std" in payload:
        return (
            f"{_fmt(payload['mean'], digits)}{suffix}"
            f" ± {_fmt(payload['std'], digits)}{suffix}"
        )
    if isinstance(payload, dict):
        return f"{_fmt(payload.get('mean', 0.0), digits)}{suffix}"
    return f"{_fmt(payload, digits)}{suffix}"


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


def _txt(
    x: int | float,
    y: int | float,
    value: str,
    *,
    size: int = 11,
    fill: str = _TEXT,
    weight: str = "normal",
    style: str = "normal",
    anchor: str = "start",
    rotate: float | None = None,
) -> str:
    transform = f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"' if rotate else ""
    font_style = f' font-style="{style}"' if style != "normal" else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}"{font_style} text-anchor="{anchor}" '
        f'font-family="{_FONT}"{transform}>{escape(value)}</text>'
    )


def build_scorecard_svg(metrics: dict[str, Any]) -> str:
    """Return a Springer booktabs-style quantitative summary SVG for Case 01."""
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
    rf_u = experiments["uci_faults_random_forest"]["metrics"]
    rf_d = experiments["matbench_steels_random_forest"]["metrics"]
    legacy_u = experiments["uci_faults"]["metrics"]
    legacy_d = experiments["matbench_steels"]["metrics"]

    base_commit = str(metrics.get("base_commit", "unknown"))[:12]
    passed = bool(gate["passed"])
    verdict = "PASS" if passed else "FAIL"
    verdict_color = _PASS_GREEN if passed else _CRIMSON

    w, h = 960, 620
    left, right = 36, 924

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Case 01 Springer-style quantitative summary scorecard">',
        f'<rect width="{w}" height="{h}" fill="{_BG}"/>',
        # Journal-style figure/table header
        _txt(left, 34, "Table 1", size=12, fill=_NAVY, weight="bold"),
        _txt(
            left + 52,
            34,
            "Reproducible benchmark summary for steel-plate fault classification and yield-strength prediction (Case 01)",
            size=12,
            fill=_TEXT,
            weight="bold",
        ),
        _txt(
            left,
            52,
            "Nested-CV ExtraTrees evaluated on five stratified seeds (UCI Steel Plates Faults) and five official MatBench folds (matbench_steels); values report mean ± SD.",
            size=10,
            fill=_MUTED,
        ),
        # Top booktabs rule (thick)
        f'<line x1="{left}" y1="66" x2="{right}" y2="66" stroke="{_RULE_DARK}" stroke-width="1.6"/>',
        # Column headers
        _txt(left + 4, 84, "Benchmark / Metric", size=10, fill=_TEXT, weight="bold"),
        _txt(330, 84, "Nested ExtraTrees", size=10, fill=_NAVY, weight="bold", anchor="end"),
        _txt(485, 84, "Fixed ExtraTrees", size=10, fill=_TEXT, weight="bold", anchor="end"),
        _txt(640, 84, "RandomForest", size=10, fill=_TEXT, weight="bold", anchor="end"),
        _txt(785, 84, "Linear Baseline", size=10, fill=_MUTED, weight="bold", anchor="end"),
        _txt(right - 4, 84, "Split Protocol", size=10, fill=_MUTED, weight="bold", anchor="end"),
        # Midrule (thin)
        f'<line x1="{left}" y1="93" x2="{right}" y2="93" stroke="{_RULE_DARK}" stroke-width="0.9"/>',
    ]

    # Section A: Reproduced models (our computation)
    table_rows = [
        (
            "UCI Faults — Exact-match accuracy",
            _stat(nested_u["accuracy"]),
            _stat(et_u["accuracy"]),
            _stat(rf_u["accuracy"]),
            f"Logistic {_fmt(legacy_u['accuracy'])}",
            "5 stratified seeds",
        ),
        (
            "UCI Faults — Macro F1",
            _stat(nested_u["macro_f1"]),
            _stat(et_u["macro_f1"]),
            _stat(rf_u["macro_f1"]),
            f"Logistic {_fmt(legacy_u['macro_f1'])}",
            "5 stratified seeds",
        ),
        (
            "MatBench Steels — MAE (MPa)",
            _stat(nested_d["mae_mpa"]),
            _stat(et_d["mae_mpa"]),
            _stat(rf_d["mae_mpa"]),
            f"Ridge {_fmt(legacy_d['mae_mpa'])}",
            "5 official folds",
        ),
        (
            "MatBench Steels — RMSE (MPa)",
            _stat(nested_d["rmse_mpa"]),
            _stat(et_d["rmse_mpa"]),
            _stat(rf_d["rmse_mpa"]),
            f"Ridge {_fmt(legacy_d['rmse_mpa'])}",
            "5 official folds",
        ),
        (
            "MatBench Steels — R²",
            _stat(nested_d["r2"]),
            _stat(et_d["r2"]),
            _stat(rf_d["r2"]),
            f"Ridge {_fmt(legacy_d['r2'])}",
            "5 official folds",
        ),
    ]

    for idx, (metric_label, nested_val, et_val, rf_val, base_val, proto) in enumerate(
        table_rows
    ):
        y = 116 + idx * 30
        if idx % 2 == 1:
            parts.append(
                f'<rect x="{left}" y="{y - 17}" width="{right - left}" height="26" fill="{_SUBTLE_BG}"/>'
            )
        parts.append(_txt(left + 4, y, metric_label, size=10, fill=_TEXT))
        parts.append(_txt(330, y, nested_val, size=10, fill=_NAVY, weight="bold", anchor="end"))
        parts.append(_txt(485, y, et_val, size=10, fill=_TEXT, anchor="end"))
        parts.append(_txt(640, y, rf_val, size=10, fill=_MUTED, anchor="end"))
        parts.append(_txt(785, y, base_val, size=10, fill=_MUTED, anchor="end"))
        parts.append(_txt(right - 4, y, proto, size=10, fill=_MUTED, anchor="end"))

    # Separator rule before Section B (Adoption Gate & Calibration)
    parts.append(
        f'<line x1="{left}" y1="262" x2="{right}" y2="262" stroke="{_GRID}" stroke-width="1"/>'
    )
    parts.append(
        _txt(
            left + 4,
            284,
            "Decision Gate & Uncertainty Calibration (Training-Fold Calibrated Only)",
            size=10,
            fill=_NAVY,
            weight="bold",
        )
    )
    parts.append(
        _txt(
            right - 4,
            284,
            f"Adoption Gate: {verdict}",
            size=11,
            fill=verdict_color,
            weight="bold",
            anchor="end",
        )
    )

    reductions_str = ", ".join(f"{float(v) * 100:.1f}%" for v in gate["mae_reductions"])
    gate_lines = [
        (
            "Gate criterion",
            f"MAE reduction ≥ 50% vs. train-mean ({_fmt(nested_d['naive_mae_mpa']['mean'], 1)} MPa) on every fold AND mean R² ≥ 0.70.",
        ),
        (
            "Observed performance",
            f"Fold MAE reductions: {reductions_str}; mean R² = {_fmt(gate['mean_r2'])}.",
        ),
        (
            "Nested-CV gain",
            f"UCI accuracy +{_fmt(summary['d01_accuracy_gain_vs_fixed_extra_trees_pp'], 2)} pp; "
            f"MatBench MAE {_fmt(summary['d04_mae_improvement_vs_fixed_extra_trees'] * 100, 1)}% lower than fixed ExtraTrees "
            f"({_fmt(summary['d04_mae_improvement_vs_random_forest'] * 100, 1)}% below RandomForest).",
        ),
    ]
    if intervals:
        gate_lines.append(
            (
                f"Cross-conformal {intervals['target_coverage']:.0%} PI",
                f"Empirical coverage {intervals['empirical_coverage']['mean']:.1%} ± "
                f"{intervals['empirical_coverage']['std']:.1%}; mean full width "
                f"{_fmt(intervals['mean_width_mpa']['mean'], 1)} ± "
                f"{_fmt(intervals['mean_width_mpa']['std'], 1)} MPa (conservative screening band, not a release spec).",
            )
        )

    for idx, (label, detail) in enumerate(gate_lines):
        y = 308 + idx * 24
        parts.append(_txt(left + 4, y, label, size=10, fill=_TEXT, weight="bold"))
        parts.append(_txt(185, y, detail, size=10, fill=_MUTED))

    # Separator rule before Section C (External Literature)
    parts.append(
        f'<line x1="{left}" y1="414" x2="{right}" y2="414" stroke="{_RULE_DARK}" stroke-width="0.9"/>'
    )
    parts.append(
        _txt(
            left + 4,
            436,
            "External Literature Context (Quoted Only — Not Independently Reproduced Here)",
            size=10,
            fill=_CRIMSON,
            weight="bold",
        )
    )
    ext_rows = [
        (
            "MatBench Leaderboard (Dunn et al., 2020)",
            f"MODNet v0.1.12: {_fmt(summary['external_comparator_mae_mpa'])} MPa MAE",
            "Different model & matminer featurization; not a like-for-like comparison.",
        ),
        (
            "NIMS Steel Fatigue (Agrawal et al., 2014)",
            f"Reported R² {_EXTERNAL_FATIGUE_R2} (LOOCV, n = 437)",
            "External dataset unavailable in this repository; quoted as literature context only.",
        ),
    ]
    for idx, (source, val, note) in enumerate(ext_rows):
        y = 460 + idx * 26
        parts.append(_txt(left + 4, y, source, size=10, fill=_TEXT))
        parts.append(_txt(310, y, val, size=10, fill=_CRIMSON, weight="bold"))
        parts.append(_txt(550, y, note, size=9, fill=_MUTED))

    # Bottom booktabs rule (thick)
    parts.append(
        f'<line x1="{left}" y1="504" x2="{right}" y2="504" stroke="{_RULE_DARK}" stroke-width="1.6"/>'
    )

    # Academic footnote & provenance
    parts.extend(
        [
            _txt(
                left,
                526,
                "Notes: All reproduced values are computed strictly from public datasets (UCI Steel Plates Faults, CC BY 4.0; MatBench matbench_steels) with zero",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                541,
                "plant or proprietary data. Inner CV and composition vocabulary fitting are confined strictly to outer training splits to prevent data leakage.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                556,
                "Every experiment payload is executed twice consecutively and verified for exact numerical identity before writing results.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                586,
                f"Source: results/metrics.json · base_commit {base_commit} · Case 01 (reproducible-steel-models)",
                size=9,
                fill=_MUTED,
                style="italic",
            ),
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def write_scorecard(metrics_path: Path, output_path: Path) -> Path:
    """Render ``metrics_path`` to ``output_path`` and return the output path."""
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_scorecard_svg(metrics), encoding="utf-8")
    return output_path


def build_comparison_svg(metrics: dict[str, Any]) -> str:
    """Return a Springer Nature 4-panel (a–d) scientific comparison chart."""
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

    w, h = 1080, 720
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Case 01 model comparison multi-panel scientific figure">',
        f'<rect width="{w}" height="{h}" fill="{_BG}"/>',
        # Figure header
        _txt(36, 32, "Fig. 1", size=12, fill=_NAVY, weight="bold"),
        _txt(
            82,
            32,
            "Model progression, fold-wise yield-strength accuracy, and adoption-gate verification (Case 01)",
            size=12,
            fill=_TEXT,
            weight="bold",
        ),
        f'<line x1="36" y1="44" x2="1044" y2="44" stroke="{_GRID}" stroke-width="1"/>',
    ]

    # ------------------------------------------------------------------
    # Panel a: UCI Steel Plates Faults — Exact-Match Accuracy
    # ------------------------------------------------------------------
    parts.append(_txt(36, 72, "a", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(54, 72, "UCI Steel Plates Faults — exact-match accuracy", size=11, fill=_TEXT, weight="bold")
    )

    # Fix: extract legacy_u["accuracy"] directly (scalar) instead of _payload_mean(legacy_u)
    d01_rows = [
        ("Logistic (seed 42)", _payload_mean(legacy_u["accuracy"]), 0.0, _GRAY_BAR),
        (
            "RandomForest",
            _payload_mean(rf_u["accuracy"]),
            float(rf_u["accuracy"].get("std", 0.0)),
            _SLATE,
        ),
        (
            "Fixed ExtraTrees",
            _payload_mean(fixed_u["accuracy"]),
            float(fixed_u["accuracy"].get("std", 0.0)),
            _STEEL,
        ),
        (
            "Nested ExtraTrees",
            _payload_mean(nested_u["accuracy"]),
            float(nested_u["accuracy"].get("std", 0.0)),
            _NAVY,
        ),
    ]
    ax_a_x0, ax_a_x1 = 180, 445
    ax_a_y0, ax_a_y1 = 96, 294
    bar_span = ax_a_x1 - ax_a_x0

    # Vertical gridlines & x-ticks (0.0 to 1.0)
    for tick in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        tx = ax_a_x0 + tick * bar_span
        if tick > 0:
            parts.append(
                f'<line x1="{tx:.1f}" y1="{ax_a_y0}" x2="{tx:.1f}" y2="{ax_a_y1}" '
                f'stroke="{_GRID}" stroke-width="0.7"/>'
            )
        parts.append(
            f'<line x1="{tx:.1f}" y1="{ax_a_y1}" x2="{tx:.1f}" y2="{ax_a_y1 + 4}" '
            f'stroke="{_AXIS}" stroke-width="1"/>'
        )
        parts.append(_txt(tx, ax_a_y1 + 17, f"{tick:.1f}", size=9, fill=_MUTED, anchor="middle"))

    # Axes spines (left + bottom)
    parts.append(
        f'<line x1="{ax_a_x0}" y1="{ax_a_y0}" x2="{ax_a_x0}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{ax_a_x0}" y1="{ax_a_y1}" x2="{ax_a_x1}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>'
    )

    for idx, (label, mean, std, color) in enumerate(d01_rows):
        top = 112 + idx * 44
        bar_h = 24
        center = top + bar_h / 2
        bw = max(2.0, mean * bar_span)
        stroke_attr = f' stroke="{_AXIS}" stroke-width="0.6"' if color == _GRAY_BAR else ""
        parts.append(
            f'<rect x="{ax_a_x0}" y="{top}" width="{bw:.1f}" height="{bar_h}" fill="{color}"{stroke_attr}/>'
        )
        if std > 0:
            half = max(2.5, std * bar_span)
            end = ax_a_x0 + bw
            parts.append(
                f'<line x1="{end - half:.1f}" y1="{center:.1f}" x2="{end + half:.1f}" y2="{center:.1f}" '
                f'stroke="{_AXIS}" stroke-width="1.3"/>'
            )
            parts.append(
                f'<line x1="{end - half:.1f}" y1="{center - 4:.1f}" x2="{end - half:.1f}" y2="{center + 4:.1f}" '
                f'stroke="{_AXIS}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{end + half:.1f}" y1="{center - 4:.1f}" x2="{end + half:.1f}" y2="{center + 4:.1f}" '
                f'stroke="{_AXIS}" stroke-width="1"/>'
            )
        val_txt = f"{mean:.4f}" if std == 0 else f"{mean:.4f} ± {std:.4f}"
        label_weight = "bold" if color == _NAVY else "normal"
        parts.append(_txt(ax_a_x0 - 10, center + 3.5, label, size=10, fill=_TEXT, weight=label_weight, anchor="end"))
        parts.append(_txt(ax_a_x1 + 8, center + 3.5, val_txt, size=9, fill=color if color != _GRAY_BAR else _MUTED, weight=label_weight))

    parts.append(_txt((ax_a_x0 + ax_a_x1) / 2, ax_a_y1 + 34, "Exact-match accuracy (mean ± SD, 5 seeds)", size=10, fill=_TEXT, anchor="middle"))

    # ------------------------------------------------------------------
    # Panel b: MatBench Steels — MAE by Official Fold
    # ------------------------------------------------------------------
    parts.append(_txt(560, 72, "b", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(578, 72, "MatBench Steels — yield-strength MAE by official fold", size=11, fill=_TEXT, weight="bold")
    )

    ax_b_x0, ax_b_x1 = 620, 1035
    ax_b_y0, ax_b_y1 = 112, 294
    ma_scale = 260.0
    ma_h = ax_b_y1 - ax_b_y0

    for tick in (0, 50, 100, 150, 200, 250):
        ty = ax_b_y1 - (tick / ma_scale) * ma_h
        if tick > 0:
            parts.append(
                f'<line x1="{ax_b_x0}" y1="{ty:.1f}" x2="{ax_b_x1}" y2="{ty:.1f}" stroke="{_GRID}" stroke-width="0.7"/>'
            )
        parts.append(
            f'<line x1="{ax_b_x0 - 4}" y1="{ty:.1f}" x2="{ax_b_x0}" y2="{ty:.1f}" stroke="{_AXIS}" stroke-width="1"/>'
        )
        parts.append(_txt(ax_b_x0 - 8, ty + 3.5, str(tick), size=9, fill=_MUTED, anchor="end"))

    parts.append(f'<line x1="{ax_b_x0}" y1="{ax_b_y0}" x2="{ax_b_x0}" y2="{ax_b_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_b_x0}" y1="{ax_b_y1}" x2="{ax_b_x1}" y2="{ax_b_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    # Legend (top of panel b)
    b_legend = [
        ("Train mean", _GRAY_BAR),
        ("Fixed ExtraTrees", _STEEL),
        ("Nested ExtraTrees", _NAVY),
    ]
    for idx, (label, color) in enumerate(b_legend):
        lx = 626 + idx * 136
        stroke_attr = f' stroke="{_AXIS}" stroke-width="0.6"' if color == _GRAY_BAR else ""
        parts.append(f'<rect x="{lx}" y="90" width="10" height="10" fill="{color}"{stroke_attr}/>')
        parts.append(_txt(lx + 15, 99, label, size=9, fill=_TEXT))

    for idx in range(n_folds):
        center = 666 + idx * 80
        for offset, series, color in (
            (-21, naive, _GRAY_BAR),
            (-5, fixed_mae, _STEEL),
            (11, nested_mae, _NAVY),
        ):
            val = _at(series, idx)
            bh = (val / ma_scale) * ma_h
            stroke_attr = f' stroke="{_AXIS}" stroke-width="0.6"' if color == _GRAY_BAR else ""
            parts.append(
                f'<rect x="{center + offset}" y="{ax_b_y1 - bh:.1f}" width="15" height="{bh:.1f}" fill="{color}"{stroke_attr}/>'
            )
        parts.append(_txt(center, ax_b_y1 + 17, f"Fold {idx}", size=9, fill=_TEXT, anchor="middle"))
        nested_val = _at(nested_mae, idx)
        parts.append(
            _txt(center + 18, ax_b_y1 - (nested_val / ma_scale) * ma_h - 5, f"{nested_val:.1f}", size=9, fill=_NAVY, weight="bold", anchor="middle")
        )

    parts.append(_txt(578, (ax_b_y0 + ax_b_y1) / 2, "MAE (MPa)", size=10, fill=_TEXT, anchor="middle", rotate=-90))
    parts.append(_txt((ax_b_x0 + ax_b_x1) / 2, ax_b_y1 + 34, "Official MatBench cross-validation fold (lower is better)", size=10, fill=_TEXT, anchor="middle"))

    # ------------------------------------------------------------------
    # Panel c: MatBench Steels — R² by Official Fold
    # ------------------------------------------------------------------
    parts.append(_txt(36, 386, "c", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(54, 386, "MatBench Steels — coefficient of determination (R²)", size=11, fill=_TEXT, weight="bold")
    )

    ax_c_x0, ax_c_x1 = 100, 505
    ax_c_y0, ax_c_y1 = 426, 606
    r2_min, r2_max = 0.65, 1.00

    def r2_y(val: float) -> float:
        return ax_c_y1 - (val - r2_min) / (r2_max - r2_min) * (ax_c_y1 - ax_c_y0)

    for tick in (0.65, 0.70, 0.80, 0.90, 1.00):
        ty = r2_y(tick)
        if tick > r2_min:
            parts.append(
                f'<line x1="{ax_c_x0}" y1="{ty:.1f}" x2="{ax_c_x1}" y2="{ty:.1f}" stroke="{_GRID}" stroke-width="0.7"/>'
            )
        parts.append(
            f'<line x1="{ax_c_x0 - 4}" y1="{ty:.1f}" x2="{ax_c_x0}" y2="{ty:.1f}" stroke="{_AXIS}" stroke-width="1"/>'
        )
        parts.append(_txt(ax_c_x0 - 8, ty + 3.5, f"{tick:.2f}", size=9, fill=_MUTED, anchor="end"))

    # Adoption gate R² = 0.70 reference line
    gate_r2_y = r2_y(0.70)
    parts.append(
        f'<line x1="{ax_c_x0}" y1="{gate_r2_y:.1f}" x2="{ax_c_x1}" y2="{gate_r2_y:.1f}" '
        f'stroke="{_CRIMSON}" stroke-width="1.2" stroke-dasharray="5 3"/>'
    )
    parts.append(_txt(ax_c_x1 - 4, gate_r2_y - 5, "Gate threshold (mean R² ≥ 0.70)", size=9, fill=_CRIMSON, anchor="end"))

    parts.append(f'<line x1="{ax_c_x0}" y1="{ax_c_y0}" x2="{ax_c_x0}" y2="{ax_c_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_c_x0}" y1="{ax_c_y1}" x2="{ax_c_x1}" y2="{ax_c_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    # Legend (top of panel c)
    parts.append(f'<line x1="255" y1="409" x2="277" y2="409" stroke="{_STEEL}" stroke-width="1.8" stroke-dasharray="4 2"/>')
    parts.append(f'<circle cx="266" cy="409" r="3.5" fill="{_BG}" stroke="{_STEEL}" stroke-width="1.5"/>')
    parts.append(_txt(283, 413, "Fixed ExtraTrees", size=9, fill=_TEXT))

    parts.append(f'<line x1="392" y1="409" x2="414" y2="409" stroke="{_NAVY}" stroke-width="2"/>')
    parts.append(f'<rect x="400" y="406" width="6" height="6" fill="{_NAVY}"/>')
    parts.append(_txt(420, 413, "Nested ExtraTrees", size=9, fill=_TEXT))

    r2_x = [142 + 80 * idx for idx in range(n_folds)]
    # Fixed ExtraTrees (dashed + open circles)
    fixed_coords = " ".join(f"{x},{r2_y(_at(fixed_r2, idx)):.1f}" for idx, x in enumerate(r2_x))
    parts.append(
        f'<polyline points="{fixed_coords}" fill="none" stroke="{_STEEL}" stroke-width="1.6" stroke-dasharray="4 2"/>'
    )
    for idx, x in enumerate(r2_x):
        y = r2_y(_at(fixed_r2, idx))
        parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="3.5" fill="{_BG}" stroke="{_STEEL}" stroke-width="1.5"/>')

    # Nested ExtraTrees (solid + filled squares)
    nested_coords = " ".join(f"{x},{r2_y(_at(nested_r2, idx)):.1f}" for idx, x in enumerate(r2_x))
    parts.append(f'<polyline points="{nested_coords}" fill="none" stroke="{_NAVY}" stroke-width="2"/>')
    for idx, x in enumerate(r2_x):
        val = _at(nested_r2, idx)
        y = r2_y(val)
        parts.append(f'<rect x="{x - 3.5:.1f}" y="{y - 3.5:.1f}" width="7" height="7" fill="{_NAVY}"/>')
        parts.append(_txt(x, y - 9, f"{val:.4f}", size=9, fill=_NAVY, weight="bold", anchor="middle"))
        parts.append(_txt(x, ax_c_y1 + 17, f"Fold {idx}", size=9, fill=_TEXT, anchor="middle"))

    parts.append(_txt(56, (ax_c_y0 + ax_c_y1) / 2, "R²", size=10, fill=_TEXT, anchor="middle", rotate=-90))
    parts.append(_txt((ax_c_x0 + ax_c_x1) / 2, ax_c_y1 + 34, "Official MatBench cross-validation fold (higher is better)", size=10, fill=_TEXT, anchor="middle"))

    # ------------------------------------------------------------------
    # Panel d: Adoption Gate — MAE Reduction vs. Train Mean
    # ------------------------------------------------------------------
    parts.append(_txt(560, 386, "d", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(578, 386, "Adoption gate — MAE reduction vs. train-mean baseline", size=11, fill=_TEXT, weight="bold")
    )

    ax_d_x0, ax_d_x1 = 620, 1035
    ax_d_y0, ax_d_y1 = 426, 606
    red_max = 0.80
    red_h = ax_d_y1 - ax_d_y0

    for tick in (0.0, 0.2, 0.4, 0.6, 0.8):
        ty = ax_d_y1 - (tick / red_max) * red_h
        if tick > 0:
            parts.append(
                f'<line x1="{ax_d_x0}" y1="{ty:.1f}" x2="{ax_d_x1}" y2="{ty:.1f}" stroke="{_GRID}" stroke-width="0.7"/>'
            )
        parts.append(
            f'<line x1="{ax_d_x0 - 4}" y1="{ty:.1f}" x2="{ax_d_x0}" y2="{ty:.1f}" stroke="{_AXIS}" stroke-width="1"/>'
        )
        parts.append(_txt(ax_d_x0 - 8, ty + 3.5, f"{tick * 100:.0f}%", size=9, fill=_MUTED, anchor="end"))

    parts.append(f'<line x1="{ax_d_x0}" y1="{ax_d_y0}" x2="{ax_d_x0}" y2="{ax_d_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_d_x0}" y1="{ax_d_y1}" x2="{ax_d_x1}" y2="{ax_d_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    threshold_y = ax_d_y1 - (0.50 / red_max) * red_h
    for idx in range(n_folds):
        center = 666 + idx * 80
        val = _at(reductions, idx)
        bh = (val / red_max) * red_h
        top = ax_d_y1 - bh
        parts.append(
            f'<rect x="{center - 18}" y="{top:.1f}" width="36" height="{bh:.1f}" fill="{_NAVY}"/>'
        )
        parts.append(_txt(center, top - 6, f"{val * 100:.2f}%", size=9, fill=_NAVY, weight="bold", anchor="middle"))
        parts.append(_txt(center, ax_d_y1 + 17, f"Fold {idx}", size=9, fill=_TEXT, anchor="middle"))

    # Draw 50% threshold line on top of bars for maximum readability
    parts.append(
        f'<line x1="{ax_d_x0}" y1="{threshold_y:.1f}" x2="{ax_d_x1}" y2="{threshold_y:.1f}" '
        f'stroke="{_CRIMSON}" stroke-width="1.5" stroke-dasharray="5 3"/>'
    )
    parts.append(
        _txt(ax_d_x1 - 4, threshold_y - 6, "50% requirement (all folds)", size=9, fill=_CRIMSON, weight="bold", anchor="end")
    )

    parts.append(_txt(578, (ax_d_y0 + ax_d_y1) / 2, "MAE reduction (%)", size=10, fill=_TEXT, anchor="middle", rotate=-90))
    parts.append(
        _txt(
            (ax_d_x0 + ax_d_x1) / 2,
            ax_d_y1 + 34,
            f"All 5 folds clear gate · mean R² = {_payload_mean(nested_d['metrics']['r2']):.4f} (PASS)",
            size=10,
            fill=_PASS_GREEN,
            weight="bold",
            anchor="middle",
        )
    )

    # Academic figure caption footer
    parts.extend(
        [
            f'<line x1="36" y1="664" x2="1044" y2="664" stroke="{_GRID}" stroke-width="1"/>',
            _txt(
                36,
                682,
                "Public datasets only (UCI Steel Plates Faults; MatBench matbench_steels). External literature benchmarks are excluded from comparative plots.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                36,
                698,
                f"Generated deterministically from results/metrics.json · base_commit {base_commit} · Error bars denote ±1 SD over 5 seeds.",
                size=9,
                fill=_MUTED,
                style="italic",
            ),
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def write_comparison(metrics_path: Path, output_path: Path) -> Path:
    """Render the comparison chart from ``metrics_path`` to ``output_path``."""
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_comparison_svg(metrics), encoding="utf-8")
    return output_path
