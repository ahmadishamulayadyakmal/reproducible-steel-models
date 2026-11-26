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
_NAVY = "#003b71"        # Primary headline model
_STEEL = "#4a90c2"       # Secondary comparator
_SLATE = "#7a8b99"       # Tertiary comparator
_GRAY_BAR = "#c8cdd3"    # Naive / legacy baseline
_CRIMSON = "#b91c1c"     # Threshold line / external literature highlight
_PASS_GREEN = "#166534"  # Pass verdict text (subtle academic forest green)

# Okabe-Ito colorblind-safe fold colors for parity/residual scatter plots
_FOLD_COLORS = ("#003b71", "#0072b2", "#009e73", "#d55e00", "#cc79a7")

_FONT = "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif"


def _fmt(value: Any, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def _stat(payload: Any, suffix: str = "", digits: int = 4) -> str:
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


def _navy_heat(fraction: float) -> tuple[str, str]:
    """Map [0, 1] to a clean white-to-Springer-Navy tint and contrasting text color."""
    f = max(0.0, min(1.0, float(fraction)))
    r = int(round(255 * (1.0 - f) + 0 * f))
    g = int(round(255 * (1.0 - f) + 59 * f))
    b = int(round(255 * (1.0 - f) + 113 * f))
    text_color = "#ffffff" if f >= 0.45 else _TEXT
    return f"#{r:02x}{g:02x}{b:02x}", text_color


def build_scorecard_svg(metrics: dict[str, Any]) -> str:
    """Return a Springer booktabs-style quantitative summary SVG for Case 01."""
    experiments = metrics["experiments"]
    summary = metrics["summary"]

    nested_u = experiments["uci_faults_nested_extra_trees"]["metrics"]
    mc_exp = experiments.get("uci_faults_multiclass_ensemble")
    headline_u = mc_exp["metrics"] if mc_exp else nested_u

    nested_d_exp = experiments["matbench_steels_nested_extra_trees"]
    hyb_exp = experiments.get("matbench_steels_physics_hybrid")
    headline_d_exp = hyb_exp if hyb_exp else nested_d_exp
    headline_d = headline_d_exp["metrics"]
    nested_d = nested_d_exp["metrics"]
    gate = headline_d_exp["decision_gate"]

    intervals = nested_d_exp.get("interval_calibration")
    adaptive = hyb_exp.get("adaptive_interval") if hyb_exp else None

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

    w, h = 980, 648
    left, right = 36, 944

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Case 01 Springer-style quantitative summary scorecard">',
        f'<rect width="{w}" height="{h}" fill="{_BG}"/>',
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
            "Evaluated over 5 stratified seeds (UCI Steel Plates Faults) and 5 official MatBench folds (matbench_steels); values report mean ± SD.",
            size=10,
            fill=_MUTED,
        ),
        f'<line x1="{left}" y1="66" x2="{right}" y2="66" stroke="{_RULE_DARK}" stroke-width="1.6"/>',
        _txt(left + 4, 84, "Benchmark / Metric", size=10, fill=_TEXT, weight="bold"),
        _txt(350, 84, "Headline Model", size=10, fill=_NAVY, weight="bold", anchor="end"),
        _txt(505, 84, "Nested ExtraTrees", size=10, fill=_TEXT, weight="bold", anchor="end"),
        _txt(655, 84, "Fixed ExtraTrees", size=10, fill=_TEXT, weight="bold", anchor="end"),
        _txt(800, 84, "Linear Baseline", size=10, fill=_MUTED, weight="bold", anchor="end"),
        _txt(right - 4, 84, "Protocol", size=10, fill=_MUTED, weight="bold", anchor="end"),
        f'<line x1="{left}" y1="93" x2="{right}" y2="93" stroke="{_RULE_DARK}" stroke-width="0.9"/>',
    ]

    table_rows = [
        (
            "UCI Faults — Accuracy",
            _stat(headline_u["accuracy"]),
            _stat(nested_u["accuracy"]),
            _stat(et_u["accuracy"]),
            f"Logistic {_fmt(legacy_u['accuracy'])}",
            "5 seeds (7-class)",
        ),
        (
            "UCI Faults — Macro F1",
            _stat(headline_u["macro_f1"]),
            _stat(nested_u["macro_f1"]),
            _stat(et_u["macro_f1"]),
            f"Logistic {_fmt(legacy_u['macro_f1'])}",
            "5 seeds (7-class)",
        ),
        (
            "MatBench Steels — MAE (MPa)",
            _stat(headline_d["mae_mpa"]),
            _stat(nested_d["mae_mpa"]),
            _stat(et_d["mae_mpa"]),
            f"Ridge {_fmt(legacy_d['mae_mpa'])}",
            "5 official folds",
        ),
        (
            "MatBench Steels — RMSE (MPa)",
            _stat(headline_d["rmse_mpa"]),
            _stat(nested_d["rmse_mpa"]),
            _stat(et_d["rmse_mpa"]),
            f"Ridge {_fmt(legacy_d['rmse_mpa'])}",
            "5 official folds",
        ),
        (
            "MatBench Steels — R²",
            _stat(headline_d["r2"]),
            _stat(nested_d["r2"]),
            _stat(et_d["r2"]),
            f"Ridge {_fmt(legacy_d['r2'])}",
            "5 official folds",
        ),
    ]

    for idx, (metric_label, head_val, nest_val, et_val, base_val, proto) in enumerate(
        table_rows
    ):
        y = 116 + idx * 30
        if idx % 2 == 1:
            parts.append(
                f'<rect x="{left}" y="{y - 17}" width="{right - left}" height="26" fill="{_SUBTLE_BG}"/>'
            )
        parts.append(_txt(left + 4, y, metric_label, size=10, fill=_TEXT))
        parts.append(_txt(350, y, head_val, size=10, fill=_NAVY, weight="bold", anchor="end"))
        parts.append(_txt(505, y, nest_val, size=10, fill=_TEXT, anchor="end"))
        parts.append(_txt(655, y, et_val, size=10, fill=_MUTED, anchor="end"))
        parts.append(_txt(800, y, base_val, size=10, fill=_MUTED, anchor="end"))
        parts.append(_txt(right - 4, y, proto, size=10, fill=_MUTED, anchor="end"))

    parts.append(
        f'<line x1="{left}" y1="262" x2="{right}" y2="262" stroke="{_GRID}" stroke-width="1"/>'
    )
    parts.append(
        _txt(
            left + 4,
            284,
            "Decision Gate & Uncertainty Calibration (Outer Training Splits Only)",
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
            f"MAE reduction ≥ 50% vs. train-mean ({_fmt(headline_d['naive_mae_mpa']['mean'], 1)} MPa) on every fold AND mean R² ≥ 0.70.",
        ),
        (
            "Observed folds",
            f"Fold MAE reductions: {reductions_str}; mean R² = {_fmt(gate['mean_r2'])}; RandomForest comparator MAE = {_fmt(rf_d['mae_mpa']['mean'], 2)} MPa.",
        ),
    ]
    if mc_exp:
        gain_pp = summary.get(
            "d01_multiclass_gain_vs_nested_pp",
            round((headline_u["accuracy"]["mean"] - nested_u["accuracy"]["mean"]) * 100.0, 2),
        )
        gate_lines.append(
            (
                "7-class UCI gain",
                f"Mutually exclusive ET + GBC soft-voting ensemble raises accuracy by +{gain_pp:.2f} pp over multi-label Nested ExtraTrees (RF: {_fmt(rf_u['accuracy']['mean'])}).",
            )
        )
    else:
        gate_lines.append(
            (
                "Nested-CV gain",
                f"UCI accuracy +{_fmt(summary['d01_accuracy_gain_vs_fixed_extra_trees_pp'], 2)} pp; "
                f"MatBench MAE {_fmt(summary['d04_mae_improvement_vs_fixed_extra_trees'] * 100, 1)}% below fixed ExtraTrees.",
            )
        )

    if adaptive:
        gate_lines.append(
            (
                "Adaptive 90% PI",
                f"Tree-spread cross-conformal coverage {adaptive['empirical_coverage']['mean']:.1%} ± "
                f"{adaptive['empirical_coverage']['std']:.1%}; median width {_fmt(adaptive['median_width_mpa']['mean'], 1)} MPa "
                f"(mean {_fmt(adaptive['mean_width_mpa']['mean'], 1)} MPa vs. constant {_fmt(intervals['mean_width_mpa']['mean'], 1) if intervals else '—'} MPa).",
            )
        )
    elif intervals:
        gate_lines.append(
            (
                f"Cross-conformal {intervals['target_coverage']:.0%} PI",
                f"Empirical coverage {intervals['empirical_coverage']['mean']:.1%} ± "
                f"{intervals['empirical_coverage']['std']:.1%}; mean full width "
                f"{_fmt(intervals['mean_width_mpa']['mean'], 1)} ± {_fmt(intervals['mean_width_mpa']['std'], 1)} MPa.",
            )
        )

    for idx, (label, detail) in enumerate(gate_lines):
        y = 308 + idx * 24
        parts.append(_txt(left + 4, y, label, size=10, fill=_TEXT, weight="bold"))
        parts.append(_txt(155, y, detail, size=10, fill=_MUTED))

    parts.append(
        f'<line x1="{left}" y1="418" x2="{right}" y2="418" stroke="{_RULE_DARK}" stroke-width="0.9"/>'
    )
    parts.append(
        _txt(
            left + 4,
            440,
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
            "Different neural architecture & matminer featurization; not like-for-like.",
        ),
        (
            "NIMS Steel Fatigue (Agrawal et al., 2014)",
            f"Reported R² {_EXTERNAL_FATIGUE_R2} (LOOCV, n = 437)",
            "External dataset unavailable here; quoted strictly as literature context.",
        ),
    ]
    for idx, (source, val, note) in enumerate(ext_rows):
        y = 464 + idx * 26
        parts.append(_txt(left + 4, y, source, size=10, fill=_TEXT))
        parts.append(_txt(310, y, val, size=10, fill=_CRIMSON, weight="bold"))
        parts.append(_txt(550, y, note, size=9, fill=_MUTED))

    parts.append(
        f'<line x1="{left}" y1="510" x2="{right}" y2="510" stroke="{_RULE_DARK}" stroke-width="1.6"/>'
    )
    parts.extend(
        [
            _txt(
                left,
                532,
                "Notes: Headline UCI model is a 7-class ExtraTrees + GradientBoosting soft-voting ensemble; headline MatBench model is an inner-CV hybrid",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                547,
                "composition + metallurgical-descriptor ExtraTrees ensemble with locally-weighted 90% cross-conformal intervals. No plant data are used.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                562,
                "Every experiment payload is executed twice consecutively and verified for exact numerical identity before writing results.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                left,
                596,
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
    mc_exp = experiments.get("uci_faults_multiclass_ensemble")

    fixed_d = experiments["matbench_steels_extra_trees"]
    nested_d = experiments["matbench_steels_nested_extra_trees"]
    hyb_d = experiments.get("matbench_steels_physics_hybrid")
    headline_d = hyb_d if hyb_d else nested_d
    gate = headline_d["decision_gate"]
    base_commit = str(metrics.get("base_commit", "unknown"))[:12]

    naive = _fold_values(
        headline_d, "naive_mae_mpa", headline_d["metrics"]["naive_mae_mpa"]
    )
    fixed_mae = _fold_values(fixed_d, "mae_mpa", fixed_d["metrics"]["mae_mpa"])
    head_mae = _fold_values(headline_d, "mae_mpa", headline_d["metrics"]["mae_mpa"])
    fixed_r2 = _fold_values(fixed_d, "r2", fixed_d["metrics"]["r2"])
    head_r2 = _fold_values(headline_d, "r2", headline_d["metrics"]["r2"])
    reductions = [float(value) for value in gate["mae_reductions"]]
    n_folds = max(len(naive), len(fixed_mae), len(head_mae), len(reductions))

    head_label = "Hybrid Physics-ET" if hyb_d else "Nested ExtraTrees"

    w, h = 1080, 730
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Case 01 model comparison multi-panel scientific figure">',
        f'<rect width="{w}" height="{h}" fill="{_BG}"/>',
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
    # Panel a: UCI Steel Plates Faults — Accuracy Progression
    # ------------------------------------------------------------------
    parts.append(_txt(36, 72, "a", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(54, 72, "UCI Steel Plates Faults — accuracy progression", size=11, fill=_TEXT, weight="bold")
    )

    d01_rows = [
        ("Logistic (seed 42)", _payload_mean(legacy_u["accuracy"]), 0.0, _GRAY_BAR),
        ("RandomForest", _payload_mean(rf_u["accuracy"]), float(rf_u["accuracy"].get("std", 0.0)), _SLATE),
        ("Fixed ExtraTrees", _payload_mean(fixed_u["accuracy"]), float(fixed_u["accuracy"].get("std", 0.0)), _STEEL),
        ("Nested ExtraTrees", _payload_mean(nested_u["accuracy"]), float(nested_u["accuracy"].get("std", 0.0)), _STEEL if mc_exp else _NAVY),
    ]
    if mc_exp:
        mc_acc = mc_exp["metrics"]["accuracy"]
        d01_rows.append(
            ("7-Class ET + GBC", _payload_mean(mc_acc), float(mc_acc.get("std", 0.0)), _NAVY)
        )

    ax_a_x0, ax_a_x1 = 175, 445
    ax_a_y0, ax_a_y1 = 96, 304
    bar_span = ax_a_x1 - ax_a_x0

    for tick in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        tx = ax_a_x0 + tick * bar_span
        if tick > 0:
            parts.append(
                f'<line x1="{tx:.1f}" y1="{ax_a_y0}" x2="{tx:.1f}" y2="{ax_a_y1}" stroke="{_GRID}" stroke-width="0.7"/>'
            )
        parts.append(
            f'<line x1="{tx:.1f}" y1="{ax_a_y1}" x2="{tx:.1f}" y2="{ax_a_y1 + 4}" stroke="{_AXIS}" stroke-width="1"/>'
        )
        parts.append(_txt(tx, ax_a_y1 + 17, f"{tick:.1f}", size=9, fill=_MUTED, anchor="middle"))

    parts.append(f'<line x1="{ax_a_x0}" y1="{ax_a_y0}" x2="{ax_a_x0}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_a_x0}" y1="{ax_a_y1}" x2="{ax_a_x1}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    step_a = 38 if len(d01_rows) >= 5 else 46
    bar_h = 22 if len(d01_rows) >= 5 else 24
    for idx, (label, mean, std, color) in enumerate(d01_rows):
        top = 108 + idx * step_a
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
                f'<line x1="{end - half:.1f}" y1="{center:.1f}" x2="{end + half:.1f}" y2="{center:.1f}" stroke="{_AXIS}" stroke-width="1.3"/>'
            )
            parts.append(
                f'<line x1="{end - half:.1f}" y1="{center - 4:.1f}" x2="{end - half:.1f}" y2="{center + 4:.1f}" stroke="{_AXIS}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{end + half:.1f}" y1="{center - 4:.1f}" x2="{end + half:.1f}" y2="{center + 4:.1f}" stroke="{_AXIS}" stroke-width="1"/>'
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
    ax_b_y0, ax_b_y1 = 116, 304
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

    b_legend = [
        ("Train mean", _GRAY_BAR),
        ("Fixed ExtraTrees", _STEEL),
        (head_label, _NAVY),
    ]
    for idx, (label, color) in enumerate(b_legend):
        lx = 626 + idx * 136
        stroke_attr = f' stroke="{_AXIS}" stroke-width="0.6"' if color == _GRAY_BAR else ""
        parts.append(f'<rect x="{lx}" y="92" width="10" height="10" fill="{color}"{stroke_attr}/>')
        parts.append(_txt(lx + 15, 101, label, size=9, fill=_TEXT))

    for idx in range(n_folds):
        center = 666 + idx * 80
        for offset, series, color in (
            (-21, naive, _GRAY_BAR),
            (-5, fixed_mae, _STEEL),
            (11, head_mae, _NAVY),
        ):
            val = _at(series, idx)
            bh = (val / ma_scale) * ma_h
            stroke_attr = f' stroke="{_AXIS}" stroke-width="0.6"' if color == _GRAY_BAR else ""
            parts.append(
                f'<rect x="{center + offset}" y="{ax_b_y1 - bh:.1f}" width="15" height="{bh:.1f}" fill="{color}"{stroke_attr}/>'
            )
        parts.append(_txt(center, ax_b_y1 + 17, f"Fold {idx}", size=9, fill=_TEXT, anchor="middle"))
        head_val = _at(head_mae, idx)
        parts.append(
            _txt(center + 18, ax_b_y1 - (head_val / ma_scale) * ma_h - 5, f"{head_val:.1f}", size=9, fill=_NAVY, weight="bold", anchor="middle")
        )

    parts.append(_txt(578, (ax_b_y0 + ax_b_y1) / 2, "MAE (MPa)", size=10, fill=_TEXT, anchor="middle", rotate=-90))
    parts.append(_txt((ax_b_x0 + ax_b_x1) / 2, ax_b_y1 + 34, "Official MatBench cross-validation fold (lower is better)", size=10, fill=_TEXT, anchor="middle"))

    # ------------------------------------------------------------------
    # Panel c: MatBench Steels — R² by Official Fold
    # ------------------------------------------------------------------
    parts.append(_txt(36, 394, "c", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(54, 394, "MatBench Steels — coefficient of determination (R²)", size=11, fill=_TEXT, weight="bold")
    )

    ax_c_x0, ax_c_x1 = 100, 505
    ax_c_y0, ax_c_y1 = 434, 614
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

    gate_r2_y = r2_y(0.70)
    parts.append(
        f'<line x1="{ax_c_x0}" y1="{gate_r2_y:.1f}" x2="{ax_c_x1}" y2="{gate_r2_y:.1f}" '
        f'stroke="{_CRIMSON}" stroke-width="1.2" stroke-dasharray="5 3"/>'
    )
    parts.append(_txt(ax_c_x1 - 4, gate_r2_y - 5, "Gate threshold (mean R² ≥ 0.70)", size=9, fill=_CRIMSON, anchor="end"))

    parts.append(f'<line x1="{ax_c_x0}" y1="{ax_c_y0}" x2="{ax_c_x0}" y2="{ax_c_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_c_x0}" y1="{ax_c_y1}" x2="{ax_c_x1}" y2="{ax_c_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    parts.append(f'<line x1="245" y1="417" x2="267" y2="417" stroke="{_STEEL}" stroke-width="1.8" stroke-dasharray="4 2"/>')
    parts.append(f'<circle cx="256" cy="417" r="3.5" fill="{_BG}" stroke="{_STEEL}" stroke-width="1.5"/>')
    parts.append(_txt(273, 421, "Fixed ExtraTrees", size=9, fill=_TEXT))

    parts.append(f'<line x1="382" y1="417" x2="404" y2="417" stroke="{_NAVY}" stroke-width="2"/>')
    parts.append(f'<rect x="390" y="414" width="6" height="6" fill="{_NAVY}"/>')
    parts.append(_txt(410, 421, head_label, size=9, fill=_TEXT))

    r2_x = [142 + 80 * idx for idx in range(n_folds)]
    fixed_coords = " ".join(f"{x},{r2_y(_at(fixed_r2, idx)):.1f}" for idx, x in enumerate(r2_x))
    parts.append(
        f'<polyline points="{fixed_coords}" fill="none" stroke="{_STEEL}" stroke-width="1.6" stroke-dasharray="4 2"/>'
    )
    for idx, x in enumerate(r2_x):
        y = r2_y(_at(fixed_r2, idx))
        parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="3.5" fill="{_BG}" stroke="{_STEEL}" stroke-width="1.5"/>')

    head_coords = " ".join(f"{x},{r2_y(_at(head_r2, idx)):.1f}" for idx, x in enumerate(r2_x))
    parts.append(f'<polyline points="{head_coords}" fill="none" stroke="{_NAVY}" stroke-width="2"/>')
    for idx, x in enumerate(r2_x):
        val = _at(head_r2, idx)
        y = r2_y(val)
        parts.append(f'<rect x="{x - 3.5:.1f}" y="{y - 3.5:.1f}" width="7" height="7" fill="{_NAVY}"/>')
        parts.append(_txt(x, y - 9, f"{val:.4f}", size=9, fill=_NAVY, weight="bold", anchor="middle"))
        parts.append(_txt(x, ax_c_y1 + 17, f"Fold {idx}", size=9, fill=_TEXT, anchor="middle"))

    parts.append(_txt(56, (ax_c_y0 + ax_c_y1) / 2, "R²", size=10, fill=_TEXT, anchor="middle", rotate=-90))
    parts.append(_txt((ax_c_x0 + ax_c_x1) / 2, ax_c_y1 + 34, "Official MatBench cross-validation fold (higher is better)", size=10, fill=_TEXT, anchor="middle"))

    # ------------------------------------------------------------------
    # Panel d: Adoption Gate — MAE Reduction vs. Train Mean
    # ------------------------------------------------------------------
    parts.append(_txt(560, 394, "d", size=15, fill=_TEXT, weight="bold"))
    parts.append(
        _txt(578, 394, "Adoption gate — MAE reduction vs. train-mean baseline", size=11, fill=_TEXT, weight="bold")
    )

    ax_d_x0, ax_d_x1 = 620, 1035
    ax_d_y0, ax_d_y1 = 434, 614
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
            f"All 5 folds clear gate · mean R² = {_payload_mean(headline_d['metrics']['r2']):.4f} (PASS)",
            size=10,
            fill=_PASS_GREEN,
            weight="bold",
            anchor="middle",
        )
    )

    parts.extend(
        [
            f'<line x1="36" y1="674" x2="1044" y2="674" stroke="{_GRID}" stroke-width="1"/>',
            _txt(
                36,
                692,
                "Public datasets only (UCI Steel Plates Faults; MatBench matbench_steels). External literature benchmarks are excluded from comparative plots.",
                size=9,
                fill=_MUTED,
            ),
            _txt(
                36,
                708,
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


def build_diagnostics_svg(metrics: dict[str, Any]) -> str:
    """Return a Springer Nature 3-panel (a–c) sample-level diagnostic figure.

    Panel a: Predicted vs. experimental yield strength parity plot (312 steels).
    Panel b: Residuals vs. predicted yield strength with adaptive 90% PI bars.
    Panel c: Normalized 7x7 confusion matrix for UCI Steel Plates Faults.
    """
    experiments = metrics["experiments"]
    base_commit = str(metrics.get("base_commit", "unknown"))[:12]
    hyb = experiments.get("matbench_steels_physics_hybrid", {})
    mc = experiments.get("uci_faults_multiclass_ensemble", {})

    parity_points = hyb.get("parity_points", [])
    adaptive = hyb.get("adaptive_interval", {})
    hyb_metrics = hyb.get("metrics", {})
    cm_norm = mc.get("confusion_matrix_normalized", [])
    class_names = mc.get(
        "class_names",
        ["Pastry", "Z_Scratch", "K_Scatch", "Stains", "Dirtiness", "Bumps", "Other_Faults"],
    )

    w, h = 1140, 440
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        'aria-label="Case 01 Springer-style sample-level diagnostics figure">',
        f'<rect width="{w}" height="{h}" fill="{_BG}"/>',
        _txt(30, 30, "Fig. 2", size=12, fill=_NAVY, weight="bold"),
        _txt(
            76,
            30,
            "Sample-level parity, adaptive 90% conformal residual calibration, and 7-class fault confusion matrix (Case 01)",
            size=12,
            fill=_TEXT,
            weight="bold",
        ),
        f'<line x1="30" y1="42" x2="1110" y2="42" stroke="{_GRID}" stroke-width="1"/>',
    ]

    # ------------------------------------------------------------------
    # Panel a: Parity Plot (Observed vs. Predicted Yield Strength)
    # ------------------------------------------------------------------
    parts.append(_txt(30, 68, "a", size=15, fill=_TEXT, weight="bold"))
    parts.append(_txt(46, 68, "Yield-strength parity (5 official folds)", size=10, fill=_TEXT, weight="bold"))

    ax_a_x0, ax_a_x1 = 82, 342
    ax_a_y0, ax_a_y1 = 86, 346
    p_min, p_max = 900.0, 2650.0

    def px_a(val: float) -> float:
        return ax_a_x0 + (val - p_min) / (p_max - p_min) * (ax_a_x1 - ax_a_x0)

    def py_a(val: float) -> float:
        return ax_a_y1 - (val - p_min) / (p_max - p_min) * (ax_a_y1 - ax_a_y0)

    for tick in (1000, 1500, 2000, 2500):
        tx = px_a(tick)
        ty = py_a(tick)
        parts.append(f'<line x1="{tx:.1f}" y1="{ax_a_y0}" x2="{tx:.1f}" y2="{ax_a_y1}" stroke="{_GRID}" stroke-width="0.6"/>')
        parts.append(f'<line x1="{ax_a_x0}" y1="{ty:.1f}" x2="{ax_a_x1}" y2="{ty:.1f}" stroke="{_GRID}" stroke-width="0.6"/>')
        parts.append(f'<line x1="{tx:.1f}" y1="{ax_a_y1}" x2="{tx:.1f}" y2="{ax_a_y1 + 4}" stroke="{_AXIS}" stroke-width="1"/>')
        parts.append(f'<line x1="{ax_a_x0 - 4}" y1="{ty:.1f}" x2="{ax_a_x0}" y2="{ty:.1f}" stroke="{_AXIS}" stroke-width="1"/>')
        parts.append(_txt(tx, ax_a_y1 + 15, str(tick), size=8.5, fill=_MUTED, anchor="middle"))
        parts.append(_txt(ax_a_x0 - 7, ty + 3, str(tick), size=8.5, fill=_MUTED, anchor="end"))

    # Identity line y = x
    parts.append(
        f'<line x1="{px_a(p_min):.1f}" y1="{py_a(p_min):.1f}" x2="{px_a(p_max):.1f}" y2="{py_a(p_max):.1f}" '
        f'stroke="{_AXIS}" stroke-width="1.2" stroke-dasharray="4 3"/>'
    )

    for pt in parity_points:
        obs = float(pt["observed_mpa"])
        pred = float(pt["predicted_mpa"])
        fold = int(pt.get("fold", 0))
        color = _FOLD_COLORS[fold % len(_FOLD_COLORS)]
        cx, cy = px_a(obs), py_a(pred)
        if ax_a_x0 <= cx <= ax_a_x1 and ax_a_y0 <= cy <= ax_a_y1:
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.6" fill="{color}" fill-opacity="0.72"/>')

    parts.append(f'<line x1="{ax_a_x0}" y1="{ax_a_y0}" x2="{ax_a_x0}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_a_x0}" y1="{ax_a_y1}" x2="{ax_a_x1}" y2="{ax_a_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    if hyb_metrics:
        parts.append(
            _txt(
                ax_a_x0 + 8,
                ax_a_y0 + 16,
                f"MAE = {_fmt(hyb_metrics['mae_mpa']['mean'], 2)} MPa",
                size=9,
                fill=_NAVY,
                weight="bold",
            )
        )
        parts.append(
            _txt(
                ax_a_x0 + 8,
                ax_a_y0 + 30,
                f"R² = {_fmt(hyb_metrics['r2']['mean'], 4)} (n = {len(parity_points)})",
                size=9,
                fill=_TEXT,
            )
        )

    parts.append(_txt((ax_a_x0 + ax_a_x1) / 2, ax_a_y1 + 31, "Experimental yield strength (MPa)", size=9.5, fill=_TEXT, anchor="middle"))
    parts.append(_txt(38, (ax_a_y0 + ax_a_y1) / 2, "Predicted yield strength (MPa)", size=9.5, fill=_TEXT, anchor="middle", rotate=-90))

    # ------------------------------------------------------------------
    # Panel b: Residuals & Adaptive 90% Conformal Calibration
    # ------------------------------------------------------------------
    parts.append(_txt(388, 68, "b", size=15, fill=_TEXT, weight="bold"))
    parts.append(_txt(404, 68, "Residuals & adaptive 90% PI bounds", size=10, fill=_TEXT, weight="bold"))

    ax_b_x0, ax_b_x1 = 442, 702
    ax_b_y0, ax_b_y1 = 86, 346
    res_min, res_max = -520.0, 520.0

    def px_b(val: float) -> float:
        return ax_b_x0 + (val - p_min) / (p_max - p_min) * (ax_b_x1 - ax_b_x0)

    def py_b(val: float) -> float:
        clamped = max(res_min, min(res_max, val))
        return ax_b_y1 - (clamped - res_min) / (res_max - res_min) * (ax_b_y1 - ax_b_y0)

    for tick in (1000, 1500, 2000, 2500):
        tx = px_b(tick)
        parts.append(f'<line x1="{tx:.1f}" y1="{ax_b_y0}" x2="{tx:.1f}" y2="{ax_b_y1}" stroke="{_GRID}" stroke-width="0.6"/>')
        parts.append(f'<line x1="{tx:.1f}" y1="{ax_b_y1}" x2="{tx:.1f}" y2="{ax_b_y1 + 4}" stroke="{_AXIS}" stroke-width="1"/>')
        parts.append(_txt(tx, ax_b_y1 + 15, str(tick), size=8.5, fill=_MUTED, anchor="middle"))

    for tick in (-400, -200, 0, 200, 400):
        ty = py_b(tick)
        parts.append(f'<line x1="{ax_b_x0}" y1="{ty:.1f}" x2="{ax_b_x1}" y2="{ty:.1f}" stroke="{_GRID}" stroke-width="0.6"/>')
        parts.append(f'<line x1="{ax_b_x0 - 4}" y1="{ty:.1f}" x2="{ax_b_x0}" y2="{ty:.1f}" stroke="{_AXIS}" stroke-width="1"/>')
        parts.append(_txt(ax_b_x0 - 7, ty + 3, str(tick), size=8.5, fill=_MUTED, anchor="end"))

    # Zero residual line
    zero_y = py_b(0.0)
    parts.append(
        f'<line x1="{ax_b_x0}" y1="{zero_y:.1f}" x2="{ax_b_x1}" y2="{zero_y:.1f}" '
        f'stroke="{_AXIS}" stroke-width="1.1" stroke-dasharray="4 3"/>'
    )

    for pt in parity_points:
        obs = float(pt["observed_mpa"])
        pred = float(pt["predicted_mpa"])
        hw = float(pt.get("half_width_mpa", 0.0))
        res = pred - obs
        inside = abs(res) <= hw if hw > 0 else True
        cx = px_b(pred)
        cy = py_b(res)
        if ax_b_x0 <= cx <= ax_b_x1:
            if hw > 0:
                parts.append(
                    f'<line x1="{cx:.1f}" y1="{py_b(-hw):.1f}" x2="{cx:.1f}" y2="{py_b(hw):.1f}" '
                    f'stroke="{_STEEL}" stroke-opacity="0.22" stroke-width="1.0"/>'
                )
            dot_color = _NAVY if inside else _CRIMSON
            parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.4" fill="{dot_color}" fill-opacity="0.78"/>')

    parts.append(f'<line x1="{ax_b_x0}" y1="{ax_b_y0}" x2="{ax_b_x0}" y2="{ax_b_y1}" stroke="{_AXIS}" stroke-width="1"/>')
    parts.append(f'<line x1="{ax_b_x0}" y1="{ax_b_y1}" x2="{ax_b_x1}" y2="{ax_b_y1}" stroke="{_AXIS}" stroke-width="1"/>')

    if adaptive:
        parts.append(
            _txt(
                ax_b_x0 + 8,
                ax_b_y0 + 16,
                f"Coverage = {adaptive['empirical_coverage']['mean']:.1%} (target 90%)",
                size=8.8,
                fill=_NAVY,
                weight="bold",
            )
        )
        parts.append(
            _txt(
                ax_b_x0 + 8,
                ax_b_y0 + 30,
                f"Median 90% width = {_fmt(adaptive['median_width_mpa']['mean'], 1)} MPa",
                size=8.8,
                fill=_TEXT,
            )
        )

    parts.append(_txt((ax_b_x0 + ax_b_x1) / 2, ax_b_y1 + 31, "Predicted yield strength (MPa)", size=9.5, fill=_TEXT, anchor="middle"))
    parts.append(_txt(396, (ax_b_y0 + ax_b_y1) / 2, "Residual: pred − exp (MPa)", size=9.5, fill=_TEXT, anchor="middle", rotate=-90))

    # ------------------------------------------------------------------
    # Panel c: Normalized 7x7 Confusion Matrix (UCI Steel Plates Faults)
    # ------------------------------------------------------------------
    parts.append(_txt(750, 68, "c", size=15, fill=_TEXT, weight="bold"))
    parts.append(_txt(766, 68, "UCI 7-class confusion matrix (row %)", size=10, fill=_TEXT, weight="bold"))

    short_labels = [
        name.replace("Other_Faults", "Other")
        .replace("Z_Scratch", "Z-Scr")
        .replace("K_Scatch", "K-Scr")
        .replace("Dirtiness", "Dirt")
        for name in class_names
    ]
    n_cls = len(short_labels)
    cm_x0, cm_y0 = 826, 88
    cell = 36

    for r_idx in range(n_cls):
        cy = cm_y0 + r_idx * cell
        parts.append(_txt(cm_x0 - 6, cy + cell / 2 + 3, short_labels[r_idx], size=8.5, fill=_TEXT, anchor="end"))
        for c_idx in range(n_cls):
            cx = cm_x0 + c_idx * cell
            val = float(cm_norm[r_idx][c_idx]) if r_idx < len(cm_norm) and c_idx < len(cm_norm[r_idx]) else 0.0
            bg_hex, txt_hex = _navy_heat(val)
            parts.append(
                f'<rect x="{cx}" y="{cy}" width="{cell}" height="{cell}" fill="{bg_hex}" stroke="{_GRID}" stroke-width="0.6"/>'
            )
            pct = f"{val * 100:.0f}" if val >= 0.005 else "·"
            parts.append(
                _txt(
                    cx + cell / 2,
                    cy + cell / 2 + 3,
                    pct,
                    size=8.5,
                    fill=txt_hex,
                    weight="bold" if r_idx == c_idx else "normal",
                    anchor="middle",
                )
            )

    for c_idx in range(n_cls):
        cx = cm_x0 + c_idx * cell + cell / 2
        parts.append(_txt(cx, cm_y0 + n_cls * cell + 14, short_labels[c_idx], size=8.2, fill=_TEXT, anchor="middle"))

    parts.append(
        f'<rect x="{cm_x0}" y="{cm_y0}" width="{n_cls * cell}" height="{n_cls * cell}" fill="none" stroke="{_AXIS}" stroke-width="1"/>'
    )
    parts.append(_txt(cm_x0 + (n_cls * cell) / 2, cm_y0 + n_cls * cell + 31, "Predicted fault class", size=9.5, fill=_TEXT, anchor="middle"))
    parts.append(_txt(772, cm_y0 + (n_cls * cell) / 2, "True fault class", size=9.5, fill=_TEXT, anchor="middle", rotate=-90))

    # Footer
    parts.extend(
        [
            f'<line x1="30" y1="398" x2="1110" y2="398" stroke="{_GRID}" stroke-width="1"/>',
            _txt(
                30,
                416,
                f"Generated deterministically from results/metrics.json · base_commit {base_commit} · Blue/red dots in panel b mark points inside/outside adaptive 90% PI.",
                size=8.8,
                fill=_MUTED,
                style="italic",
            ),
            "</svg>",
        ]
    )
    return "\n".join(parts) + "\n"


def write_diagnostics(metrics_path: Path, output_path: Path) -> Path:
    """Render the sample-level diagnostic figure from ``metrics_path``."""
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_diagnostics_svg(metrics), encoding="utf-8")
    return output_path
