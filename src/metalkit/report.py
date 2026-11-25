"""Render the C01 case scorecard directly from committed metrics.

The figure uses only the Python standard library so that it can be regenerated
in the pinned environment without adding a plotting dependency.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

# These source numbers are quoted in docs/reproducibility_audit.md. They are
# deliberately NOT taken from our metrics: they are external literature.
_EXTERNAL_MAE_MPA = "87.7627"
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


def _fmt(value: Any, digits: int = 4) -> str:
    """Format a metric value with a fixed number of decimals."""
    return f"{float(value):.{digits}f}"


def build_scorecard_svg(metrics: dict[str, Any]) -> str:
    """Return a deterministic SVG scorecard for the C01 metrics dictionary."""
    experiments = metrics["experiments"]
    uci = experiments["uci_faults"]
    matbench = experiments["matbench_steels"]

    accuracy = _fmt(uci["metrics"]["accuracy"])
    macro_f1 = _fmt(uci["metrics"]["macro_f1"])
    mae = _fmt(matbench["metrics"]["mae_mpa"])
    rmse = _fmt(matbench["metrics"]["rmse_mpa"])
    r2 = _fmt(matbench["metrics"]["r2"])
    seed = int(metrics.get("seed", 42))
    fold = int(matbench.get("fold", 0))
    commit = str(metrics.get("base_commit", "unknown"))[:12]

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

    def row(y: int, label: str, value: str, accent: str) -> str:
        return (
            f'<rect x="60" y="{y - 24}" width="400" height="34" rx="6" '
            f'fill="{_BG}" stroke="{_BORDER}" stroke-width="1"/>'
            + txt(72, y, label, size=14, fill=_MUTED)
            + txt(448, y, value, size=15, fill=accent, weight="bold", anchor="end")
        )

    parts: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="620" '
        'viewBox="0 0 980 620" role="img" '
        'aria-label="C01 reproducibility case scorecard">',
        f'<rect width="980" height="620" fill="{_BG}"/>',
        txt(40, 50, "C01 — reproducibility case scorecard", size=25, weight="bold"),
        txt(
            40,
            78,
            "Public data · pinned environment · evidence A · no plant data",
            size=14,
            fill=_MUTED,
        ),
        f'<line x1="40" y1="96" x2="940" y2="96" stroke="{_BORDER}" stroke-width="1"/>',
        f'<rect x="40" y="116" width="440" height="300" rx="10" fill="{_PANEL}" '
        f'stroke="{_BORDER}" stroke-width="1"/>',
        txt(60, 146, "OUR RESULTS — reproduced", size=16, fill=_TEAL, weight="bold"),
        row(
            190,
            "D01 exact-match accuracy",
            accuracy,
            _TEAL,
        ),
        row(232, "D01 macro F1", macro_f1, _TEAL),
        row(274, "D04 yield strength MAE", f"{mae} MPa", _TEAL),
        row(316, "D04 yield strength RMSE", f"{rmse} MPa", _TEAL),
        row(358, "D04 yield strength R²", r2, _TEAL),
        txt(
            60,
            398,
            f"seed {seed} · official fold {fold} · two identical runs",
            size=12,
            fill=_MUTED,
        ),
        f'<rect x="500" y="116" width="440" height="300" rx="10" fill="{_PANEL}" '
        f'stroke="{_BORDER}" stroke-width="1"/>',
        txt(
            520,
            146,
            "EXTERNAL LITERATURE — not reproduced",
            size=16,
            fill=_AMBER,
            weight="bold",
        ),
        row(200, "MatBench MODNet MAE", f"{_EXTERNAL_MAE_MPA} MPa", _AMBER),
        row(244, "Y2R12 fatigue R²", _EXTERNAL_FATIGUE_R2, _AMBER),
        txt(
            520,
            300,
            "Different model / featurization, or unavailable data.",
            size=14,
            fill=_MUTED,
        ),
        txt(
            520,
            326,
            "These numbers are cited, never claimed as our results.",
            size=14,
            fill=_MUTED,
        ),
        txt(
            520,
            366,
            "No plant validation is claimed in this repository.",
            size=13,
            fill=_AMBER,
            weight="bold",
        ),
        f'<rect x="40" y="436" width="900" height="144" rx="10" '
        f'fill="{_BLUE_TINT}" stroke="{_BLUE_BORDER}" stroke-width="1"/>',
        txt(60, 468, "Case verdict", size=16, fill=_BLUE, weight="bold"),
        txt(
            60,
            498,
            "A downstream lab can regenerate all five of our numbers from public "
            "inputs and a pinned environment.",
            size=15,
        ),
        txt(
            60,
            526,
            "The published high scores above remain external literature: this "
            "repository does not reproduce them.",
            size=15,
        ),
        txt(
            60,
            554,
            "Use our baselines as a reproducibility floor, not as a "
            "plant-validated performance claim.",
            size=15,
        ),
        txt(
            40,
            602,
            f"generated from results/metrics.json · base_commit {commit}",
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
