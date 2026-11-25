"""Deterministic baselines used for the C01 reproducibility audit.

Both experiments are deliberately small: the point of C01 is provenance and
repeatability, not state-of-the-art accuracy. Published scores are quoted only
in ``docs/reproducibility_audit.md`` and are never presented as our results.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from metalkit.datasets import (
    DATA_FILES,
    load_matbench_splits,
    load_matbench_steels,
    load_uci_faults,
    verify_data_dir,
)
from metalkit.provenance import environment_info, source_fingerprint

_ELEMENT_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")


def composition_features(compositions: list[str]) -> tuple[np.ndarray, list[str]]:
    """Turn composition strings into atomic fractions over a sorted vocabulary.

    ``Fe0.8C0.2`` and ``Fe80C20`` therefore give the same feature vector.
    The vocabulary is derived only from input formulas, never from the target.
    """
    rows: list[dict[str, float]] = []
    vocabulary: set[str] = set()
    for formula in compositions:
        amounts: dict[str, float] = {}
        for symbol, count in _ELEMENT_TOKEN.findall(formula):
            amount = float(count) if count else 1.0
            amounts[symbol] = amounts.get(symbol, 0.0) + amount
        total = sum(amounts.values())
        if total <= 0.0:
            raise ValueError(f"Composition has no parseable elements: {formula!r}")
        rows.append({symbol: amount / total for symbol, amount in amounts.items()})
        vocabulary.update(amounts)

    elements = sorted(vocabulary)
    matrix = np.zeros((len(rows), len(elements)), dtype=float)
    for row_index, row in enumerate(rows):
        for column_index, element in enumerate(elements):
            matrix[row_index, column_index] = row.get(element, 0.0)
    return matrix, elements


def _round_metrics(metrics: dict[str, float]) -> dict[str, float]:
    return {name: round(float(value), 4) for name, value in metrics.items()}


def _ids_fingerprint(train_ids: list[str], test_ids: list[str]) -> str:
    blob = "|".join([*train_ids, *test_ids]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def run_uci_faults(data_dir: str | Path, seed: int = 42) -> dict:
    """Reproduce our own stratified fault-classification baseline on D01."""
    frame = load_uci_faults(Path(data_dir) / DATA_FILES["D01"][0])
    features = frame.iloc[:, :27]
    labels = frame.iloc[:, 27:].to_numpy(dtype=int)
    strata = [tuple(row) for row in labels]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=seed,
        shuffle=True,
        stratify=strata,
    )
    model = make_pipeline(
        StandardScaler(),
        OneVsRestClassifier(
            LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed),
            n_jobs=1,
        ),
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    metrics = _round_metrics(
        {
            "accuracy": accuracy_score(y_test, predictions),
            "macro_f1": f1_score(y_test, predictions, average="macro"),
        }
    )
    return {
        "dataset": "D01 UCI Steel Plates Faults",
        "model": (
            "StandardScaler + OneVsRestClassifier(LogisticRegression("
            "max_iter=2000, solver=lbfgs), n_jobs=1)"
        ),
        "seed": seed,
        "test_fraction": 0.2,
        "n_samples": int(len(frame)),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
        "n_features": 27,
        "n_labels": 7,
        "metrics": metrics,
    }


def run_matbench_steels(data_dir: str | Path, fold: int = 0) -> dict:
    """Reproduce our own composition-only Ridge baseline on an official fold."""
    root = Path(data_dir)
    frame = load_matbench_steels(root / DATA_FILES["D04"][0])
    folds = load_matbench_splits(root / DATA_FILES["D04-splits"][0])
    if fold not in range(5):
        raise ValueError(f"fold must be 0..4, got {fold}")

    split = folds[f"fold_{fold}"]
    position = {sample_id: index for index, sample_id in enumerate(frame["id"])}
    train_ids, test_ids = split["train"], split["test"]
    train_index = [position[sample_id] for sample_id in train_ids]
    test_index = [position[sample_id] for sample_id in test_ids]

    matrix, elements = composition_features(frame["composition"].tolist())
    target = frame["yield_strength_mpa"].to_numpy(dtype=float)
    model = Ridge(alpha=1.0, solver="cholesky")
    model.fit(matrix[train_index], target[train_index])
    predictions = model.predict(matrix[test_index])
    observed = target[test_index]

    error = predictions - observed
    metrics = _round_metrics(
        {
            "mae_mpa": mean_absolute_error(observed, predictions),
            "rmse_mpa": float(np.sqrt(np.mean(error**2))),
            "r2": float(1.0 - np.sum(error**2) / np.sum((observed - observed.mean()) ** 2)),
        }
    )
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model": "atomic-fraction composition vector + Ridge(alpha=1.0, cholesky)",
        "fold": fold,
        "split_random_state": 18012019,
        "split_fingerprint": _ids_fingerprint(train_ids, test_ids),
        "n_samples": int(len(frame)),
        "n_train": int(len(train_index)),
        "n_test": int(len(test_index)),
        "n_features": len(elements),
        "target_unit": "MPa",
        "metrics": metrics,
    }


def reproduce(data_dir: str | Path, seed: int = 42, fold: int = 0) -> dict:
    """Run each baseline twice; fail unless all metrics match to 4 decimals."""
    data = verify_data_dir(data_dir)
    experiments = {}
    for name, function, kwargs in (
        ("uci_faults", run_uci_faults, {"seed": seed}),
        ("matbench_steels", run_matbench_steels, {"fold": fold}),
    ):
        first = function(data_dir, **kwargs)
        second = function(data_dir, **kwargs)
        if first["metrics"] != second["metrics"]:
            raise RuntimeError(
                f"Non-reproducible metrics for {name}: {first['metrics']} != "
                f"{second['metrics']}"
            )
        experiments[name] = first

    return {
        "seed": seed,
        "fold": fold,
        "determinism_check": "two consecutive runs, metrics equal to 4 decimals",
        "code_fingerprint": source_fingerprint(Path(__file__).parent),
        "data": data,
        "environment": environment_info(),
        "experiments": experiments,
    }
