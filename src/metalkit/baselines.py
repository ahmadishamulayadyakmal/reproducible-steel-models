"""Reproducibility and predictive baselines for the C01 case.

The original two experiments remain available as historical baselines. The
predictive extension adds RandomForest and ExtraTrees models, multi-seed /
multi-fold error bars and an explicit, case-specific adoption gate. The current
headline model is ExtraTrees with a nested hyperparameter search: an inner CV
on each outer training split selects the hyperparameters, and the untouched
outer split is used only for the reported score. Fixed ExtraTrees and
RandomForest are retained as deterministic comparators. Published scores are
quoted only in the documentation and are never presented as our results.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    make_scorer,
    mean_absolute_error,
)
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from metalkit.datasets import (
    DATA_FILES,
    load_matbench_splits,
    load_matbench_steels,
    load_uci_faults,
    verify_data_dir,
)
from metalkit.descriptors import MetallurgicalDescriptorVectorizer
from metalkit.provenance import environment_info, source_fingerprint

_ELEMENT_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")
PREDICTIVE_SEEDS: tuple[int, ...] = (42, 7, 11, 19, 23)
OFFICIAL_FOLDS: tuple[int, ...] = (0, 1, 2, 3, 4)

# Nested search: each outer split keeps its own inner CV. No outer test row is
# used to choose a hyperparameter. The grids are deliberately small and fixed.
NESTED_UCI_INNER_FOLDS = 3
NESTED_MATBENCH_INNER_FOLDS = 4
NESTED_UCI_PARAM_GRID: dict[str, list[Any]] = {
    "model__max_features": [0.5, 1.0],
    "model__min_samples_leaf": [1, 2],
}
NESTED_MATBENCH_PARAM_GRID: dict[str, list[Any]] = {
    "model__max_features": [0.5, 1.0],
    "model__min_samples_leaf": [1, 2, 4],
}

# Cross-conformal prediction intervals for D04. Calibration residuals come
# only from out-of-fold predictions on the outer training split; the outer
# test fold is never used to choose the interval width.
CONFORMAL_TARGET_COVERAGE = 0.90
CONFORMAL_ALPHA = round(1.0 - CONFORMAL_TARGET_COVERAGE, 10)
CONFORMAL_CV_FOLDS = NESTED_MATBENCH_INNER_FOLDS
CONFORMAL_CV_SEED = 42

# A case-specific engineering gate, not a published material standard.
# It is intentionally simple and is evaluated only on public data.
DECISION_RULE: dict[str, Any] = {
    "description": (
        "Adopt only if the headline ensemble MAE is at least 50% lower than "
        "the train-mean predictor on every official fold AND mean R2 >= 0.70."
    ),
    "min_mae_reduction_vs_naive": 0.50,
    "min_mean_r2": 0.70,
    "scope": "public D01/D04 data only; no plant validation",
}


def _jsonable(value: Any) -> Any:
    """Convert NumPy scalar parameters into JSON-safe Python scalars."""
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _selected_params(search: GridSearchCV) -> dict[str, Any]:
    """Strip pipeline prefixes from ``best_params_`` for readable provenance."""
    return {
        key.split("__", 1)[-1]: _jsonable(value)
        for key, value in search.best_params_.items()
    }


def _grid_size(grid: dict[str, list[Any]]) -> int:
    size = 1
    for values in grid.values():
        size *= len(values)
    return size


def _matbench_nested_pipeline() -> Pipeline:
    """Return a fresh pipeline so cross-fitting clones cannot share fits."""
    return Pipeline(
        [
            ("vectorizer", CompositionVectorizer()),
            (
                "model",
                ExtraTreesRegressor(
                    n_estimators=300, random_state=42, n_jobs=1
                ),
            ),
        ]
    )


def conformal_half_width(
    features: np.ndarray,
    target: np.ndarray,
    selected_params: dict[str, Any],
    *,
    alpha: float = CONFORMAL_ALPHA,
    n_splits: int = CONFORMAL_CV_FOLDS,
    seed: int = CONFORMAL_CV_SEED,
) -> float:
    """Return a cross-conformal half-width from training data only.

    Out-of-fold absolute residuals are collected with the same K-fold
    protocol used by the nested search. The empirical quantile index is
    ``ceil((n + 1) * (1 - alpha))``, clipped to the available residuals.
    """
    residuals: list[float] = []
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    params = {
        f"model__{key}": value for key, value in selected_params.items()
    }
    for fit_index, calibration_index in splitter.split(features):
        estimator = clone(_matbench_nested_pipeline()).set_params(**params)
        estimator.fit(features[fit_index], target[fit_index])
        predicted = estimator.predict(features[calibration_index])
        residuals.extend(
            np.abs(predicted - target[calibration_index]).tolist()
        )
    ordered = np.sort(np.asarray(residuals, dtype=float))
    rank = int(np.ceil((len(ordered) + 1) * (1.0 - alpha)))
    return float(ordered[max(0, min(rank - 1, len(ordered) - 1))])


def _parse_composition(formula: str) -> dict[str, float]:
    """Return element -> atomic fraction for one composition string."""
    amounts: dict[str, float] = {}
    for symbol, count in _ELEMENT_TOKEN.findall(formula):
        amount = float(count) if count else 1.0
        amounts[symbol] = amounts.get(symbol, 0.0) + amount
    total = sum(amounts.values())
    if total <= 0.0:
        raise ValueError(f"Composition has no parseable elements: {formula!r}")
    return {symbol: amount / total for symbol, amount in amounts.items()}


def composition_vocabulary(compositions: Sequence[str]) -> list[str]:
    """Return the sorted element vocabulary fitted on training compositions."""
    vocabulary: set[str] = set()
    for formula in compositions:
        vocabulary.update(_parse_composition(formula))
    return sorted(vocabulary)


def composition_matrix(
    compositions: Sequence[str], vocabulary: Sequence[str]
) -> np.ndarray:
    """Encode compositions using only elements present in a fitted vocabulary.

    Unseen test elements are ignored rather than added, so no information from
    the test split changes the feature space.
    """
    columns = {element: index for index, element in enumerate(vocabulary)}
    matrix = np.zeros((len(compositions), len(vocabulary)), dtype=float)
    for row_index, formula in enumerate(compositions):
        for element, fraction in _parse_composition(formula).items():
            if element in columns:
                matrix[row_index, columns[element]] = fraction
    return matrix


class CompositionVectorizer(BaseEstimator, TransformerMixin):
    """Fit an element vocabulary inside each CV training split.

    Pipeline cloning gives every inner split its own vocabulary, so an inner
    validation composition cannot influence the feature space it is scored on.
    """

    def fit(self, X, y=None) -> "CompositionVectorizer":
        self.vocabulary_ = composition_vocabulary(list(X))
        return self

    def transform(self, X) -> np.ndarray:
        return composition_matrix(list(X), self.vocabulary_)


def composition_features(compositions: Sequence[str]) -> tuple[np.ndarray, list[str]]:
    """Fit a vocabulary on the given compositions and encode them.

    Retained for the historical baseline. Predictive runs fit the vocabulary
    on the training split only and call :func:`composition_matrix`.
    """
    vocabulary = composition_vocabulary(compositions)
    return composition_matrix(compositions, vocabulary), vocabulary


def _round_metrics(metrics: dict[str, float]) -> dict[str, float]:
    return {name: round(float(value), 4) for name, value in metrics.items()}


def _summary(values: Sequence[float]) -> dict[str, Any]:
    """Return mean, population standard deviation and rounded raw values."""
    array = np.asarray(list(values), dtype=float)
    return {
        "mean": round(float(array.mean()), 4),
        "std": round(float(array.std(ddof=0)), 4),
        "values": [round(float(value), 4) for value in array],
    }


def _ids_fingerprint(train_ids: Sequence[str], test_ids: Sequence[str]) -> str:
    blob = "|".join([*train_ids, *test_ids]).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def evaluate_decision_gate(
    naive_maes: Sequence[float],
    model_maes: Sequence[float],
    r2_values: Sequence[float],
) -> dict[str, Any]:
    """Apply the case-specific predictive adoption gate."""
    reductions = [
        (float(naive) - float(model)) / float(naive)
        for naive, model in zip(naive_maes, model_maes, strict=True)
    ]
    mean_r2 = float(np.mean(list(r2_values)))
    passed = (
        all(
            reduction >= DECISION_RULE["min_mae_reduction_vs_naive"]
            for reduction in reductions
        )
        and mean_r2 >= DECISION_RULE["min_mean_r2"]
    )
    return {
        **DECISION_RULE,
        "mae_reductions": [round(float(value), 4) for value in reductions],
        "mean_r2": round(mean_r2, 4),
        "passed": bool(passed),
    }


def _uci_estimator(model: str, seed: int):
    if model == "logistic":
        return make_pipeline(
            StandardScaler(),
            OneVsRestClassifier(
                LogisticRegression(max_iter=2000, solver="lbfgs", random_state=seed),
                n_jobs=1,
            ),
        )
    if model == "random_forest":
        return RandomForestClassifier(
            n_estimators=300, random_state=seed, n_jobs=1
        )
    if model == "extra_trees":
        return ExtraTreesClassifier(
            n_estimators=500, random_state=seed, n_jobs=1
        )
    raise ValueError(
        f"Unknown UCI model {model!r}; use logistic, random_forest or extra_trees"
    )


def _uci_model_label(model: str, seed: int) -> str:
    if model == "logistic":
        return (
            "StandardScaler + OneVsRestClassifier(LogisticRegression("
            "max_iter=2000, solver=lbfgs, n_jobs=1))"
        )
    if model == "random_forest":
        return (
            f"RandomForestClassifier(n_estimators=300, random_state={seed}, n_jobs=1)"
        )
    return f"ExtraTreesClassifier(n_estimators=500, random_state={seed}, n_jobs=1)"


def run_uci_faults(
    data_dir: str | Path, seed: int = 42, model: str = "logistic"
) -> dict:
    """Run one deterministic D01 fault-classification split."""
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
    estimator = _uci_estimator(model, seed)
    estimator.fit(x_train, y_train)
    predictions = estimator.predict(x_test)

    metrics = _round_metrics(
        {
            "accuracy": accuracy_score(y_test, predictions),
            "macro_f1": f1_score(y_test, predictions, average="macro"),
        }
    )
    return {
        "dataset": "D01 UCI Steel Plates Faults",
        "model": _uci_model_label(model, seed),
        "model_id": model,
        "seed": seed,
        "test_fraction": 0.2,
        "n_samples": int(len(frame)),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
        "n_features": 27,
        "n_labels": 7,
        "metrics": metrics,
    }


def run_uci_faults_multi(
    data_dir: str | Path,
    seeds: Sequence[int] = PREDICTIVE_SEEDS,
    model: str = "random_forest",
) -> dict:
    """Aggregate D01 metrics over several fixed seeds."""
    runs = [run_uci_faults(data_dir, seed=seed, model=model) for seed in seeds]
    metric_names = ("accuracy", "macro_f1")
    return {
        "dataset": "D01 UCI Steel Plates Faults",
        "model_id": model,
        "model": _uci_model_label(model, int(seeds[0])),
        "seeds": list(seeds),
        "n_runs": len(runs),
        "n_samples": runs[0]["n_samples"],
        "n_features": runs[0]["n_features"],
        "n_labels": runs[0]["n_labels"],
        "metrics": {
            name: _summary([run["metrics"][name] for run in runs])
            for name in metric_names
        },
        "per_seed": [
            {"seed": run["seed"], "metrics": run["metrics"]} for run in runs
        ],
    }


def run_uci_faults_nested(data_dir: str | Path, seed: int = 42) -> dict:
    """Run one D01 split with an inner CV hyperparameter search on train only."""
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
    pipeline = Pipeline(
        [
            (
                "model",
                ExtraTreesClassifier(
                    n_estimators=300, random_state=seed, n_jobs=1
                ),
            )
        ]
    )
    search = GridSearchCV(
        pipeline,
        NESTED_UCI_PARAM_GRID,
        scoring=make_scorer(f1_score, average="macro"),
        cv=KFold(
            n_splits=NESTED_UCI_INNER_FOLDS, shuffle=True, random_state=seed
        ),
        n_jobs=1,
        refit=True,
    )
    search.fit(x_train, y_train)
    predictions = search.predict(x_test)
    metrics = _round_metrics(
        {
            "accuracy": accuracy_score(y_test, predictions),
            "macro_f1": f1_score(y_test, predictions, average="macro"),
        }
    )
    return {
        "dataset": "D01 UCI Steel Plates Faults",
        "model": (
            "ExtraTreesClassifier(n_estimators=300, n_jobs=1) with inner-CV "
            "selection of max_features and min_samples_leaf"
        ),
        "model_id": "nested_extra_trees",
        "seed": seed,
        "test_fraction": 0.2,
        "n_samples": int(len(frame)),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
        "n_features": 27,
        "n_labels": 7,
        "inner_cv_folds": NESTED_UCI_INNER_FOLDS,
        "inner_cv_scoring": "macro_f1",
        "candidate_count": _grid_size(NESTED_UCI_PARAM_GRID),
        "selected_params": _selected_params(search),
        "inner_cv_best_macro_f1": round(float(search.best_score_), 4),
        "metrics": metrics,
    }


def run_uci_faults_nested_multi(
    data_dir: str | Path, seeds: Sequence[int] = PREDICTIVE_SEEDS
) -> dict:
    """Aggregate nested D01 results over fixed outer seeds."""
    runs = [run_uci_faults_nested(data_dir, seed=seed) for seed in seeds]
    metric_names = ("accuracy", "macro_f1")
    return {
        "dataset": "D01 UCI Steel Plates Faults",
        "model_id": "nested_extra_trees",
        "model": runs[0]["model"],
        "seeds": list(seeds),
        "n_runs": len(runs),
        "n_samples": runs[0]["n_samples"],
        "n_features": runs[0]["n_features"],
        "n_labels": runs[0]["n_labels"],
        "inner_cv_folds": NESTED_UCI_INNER_FOLDS,
        "inner_cv_scoring": "macro_f1",
        "candidate_count": _grid_size(NESTED_UCI_PARAM_GRID),
        "metrics": {
            name: _summary([run["metrics"][name] for run in runs])
            for name in metric_names
        },
        "inner_cv_best_macro_f1": _summary(
            [run["inner_cv_best_macro_f1"] for run in runs]
        ),
        "per_seed": [
            {
                "seed": run["seed"],
                "metrics": run["metrics"],
                "selected_params": run["selected_params"],
                "inner_cv_best_macro_f1": run["inner_cv_best_macro_f1"],
            }
            for run in runs
        ],
    }


def _matbench_estimator(model: str):
    if model == "ridge":
        return Ridge(alpha=1.0, solver="cholesky")
    if model == "random_forest":
        return RandomForestRegressor(
            n_estimators=300, random_state=42, n_jobs=1
        )
    if model == "extra_trees":
        return ExtraTreesRegressor(
            n_estimators=500, random_state=42, n_jobs=1
        )
    raise ValueError(
        f"Unknown MatBench model {model!r}; use ridge, random_forest or extra_trees"
    )


def _matbench_model_label(model: str) -> str:
    if model == "ridge":
        return "atomic-fraction composition vector + Ridge(alpha=1.0, cholesky)"
    if model == "random_forest":
        return (
            "train-fitted atomic-fraction vector + RandomForestRegressor("
            "n_estimators=300, random_state=42)"
        )
    return (
        "train-fitted atomic-fraction vector + ExtraTreesRegressor("
        "n_estimators=500, random_state=42)"
    )


def run_matbench_steels(
    data_dir: str | Path, fold: int = 0, model: str = "ridge"
) -> dict:
    """Run one deterministic D04 experiment on an official fold."""
    root = Path(data_dir)
    frame = load_matbench_steels(root / DATA_FILES["D04"][0])
    folds = load_matbench_splits(root / DATA_FILES["D04-splits"][0])
    if fold not in OFFICIAL_FOLDS:
        raise ValueError(f"fold must be 0..4, got {fold}")

    split = folds[f"fold_{fold}"]
    position = {sample_id: index for index, sample_id in enumerate(frame["id"])}
    train_ids, test_ids = split["train"], split["test"]
    train_index = [position[sample_id] for sample_id in train_ids]
    test_index = [position[sample_id] for sample_id in test_ids]

    compositions = frame["composition"].tolist()
    # Fit the feature vocabulary on training formulas only: no test leakage.
    vocabulary = composition_vocabulary([compositions[i] for i in train_index])
    matrix = composition_matrix(compositions, vocabulary)
    target = frame["yield_strength_mpa"].to_numpy(dtype=float)

    estimator = _matbench_estimator(model)
    estimator.fit(matrix[train_index], target[train_index])
    predictions = estimator.predict(matrix[test_index])
    observed = target[test_index]
    error = predictions - observed
    naive_mae = mean_absolute_error(
        observed, np.full(len(observed), target[train_index].mean())
    )

    metrics = _round_metrics(
        {
            "mae_mpa": mean_absolute_error(observed, predictions),
            "rmse_mpa": float(np.sqrt(np.mean(error**2))),
            "r2": float(
                1.0 - np.sum(error**2) / np.sum((observed - observed.mean()) ** 2)
            ),
            "naive_mae_mpa": naive_mae,
        }
    )
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model": _matbench_model_label(model),
        "model_id": model,
        "fold": fold,
        "split_random_state": 18012019,
        "split_fingerprint": _ids_fingerprint(train_ids, test_ids),
        "n_samples": int(len(frame)),
        "n_train": int(len(train_index)),
        "n_test": int(len(test_index)),
        "n_features": len(vocabulary),
        "target_unit": "MPa",
        "metrics": metrics,
    }


def run_matbench_steels_multi(
    data_dir: str | Path,
    folds: Sequence[int] = OFFICIAL_FOLDS,
    model: str = "random_forest",
) -> dict:
    """Aggregate D04 metrics over all five official folds."""
    runs = [run_matbench_steels(data_dir, fold=fold, model=model) for fold in folds]
    metric_names = ("mae_mpa", "rmse_mpa", "r2", "naive_mae_mpa")
    gate = evaluate_decision_gate(
        [run["metrics"]["naive_mae_mpa"] for run in runs],
        [run["metrics"]["mae_mpa"] for run in runs],
        [run["metrics"]["r2"] for run in runs],
    )
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model_id": model,
        "model": _matbench_model_label(model),
        "folds": list(folds),
        "n_folds": len(runs),
        "n_samples": runs[0]["n_samples"],
        "target_unit": "MPa",
        "metrics": {
            name: _summary([run["metrics"][name] for run in runs])
            for name in metric_names
        },
        "per_fold": [
            {
                "fold": run["fold"],
                "metrics": run["metrics"],
                "split_fingerprint": run["split_fingerprint"],
            }
            for run in runs
        ],
        "decision_gate": gate,
    }


def run_matbench_steels_nested(
    data_dir: str | Path, fold: int = 0
) -> dict:
    """Run one official D04 fold with an inner CV search on training data only."""
    root = Path(data_dir)
    frame = load_matbench_steels(root / DATA_FILES["D04"][0])
    folds = load_matbench_splits(root / DATA_FILES["D04-splits"][0])
    if fold not in OFFICIAL_FOLDS:
        raise ValueError(f"fold must be 0..4, got {fold}")

    split = folds[f"fold_{fold}"]
    position = {sample_id: index for index, sample_id in enumerate(frame["id"])}
    train_ids, test_ids = split["train"], split["test"]
    train_index = [position[sample_id] for sample_id in train_ids]
    test_index = [position[sample_id] for sample_id in test_ids]

    compositions = np.asarray(frame["composition"].tolist(), dtype=object)
    target = frame["yield_strength_mpa"].to_numpy(dtype=float)
    pipeline = _matbench_nested_pipeline()
    search = GridSearchCV(
        pipeline,
        NESTED_MATBENCH_PARAM_GRID,
        scoring="neg_mean_absolute_error",
        cv=KFold(
            n_splits=NESTED_MATBENCH_INNER_FOLDS,
            shuffle=True,
            random_state=42,
        ),
        n_jobs=1,
        refit=True,
    )
    search.fit(compositions[train_index], target[train_index])
    predictions = search.predict(compositions[test_index])
    observed = target[test_index]
    error = predictions - observed
    naive_mae = mean_absolute_error(
        observed, np.full(len(observed), target[train_index].mean())
    )
    metrics = _round_metrics(
        {
            "mae_mpa": mean_absolute_error(observed, predictions),
            "rmse_mpa": float(np.sqrt(np.mean(error**2))),
            "r2": float(
                1.0 - np.sum(error**2) / np.sum((observed - observed.mean()) ** 2)
            ),
            "naive_mae_mpa": naive_mae,
        }
    )
    vocabulary = search.best_estimator_.named_steps["vectorizer"].vocabulary_
    selected_params = _selected_params(search)
    half_width = conformal_half_width(
        compositions[train_index], target[train_index], selected_params
    )
    lower = predictions - half_width
    upper = predictions + half_width
    coverage = float(np.mean((observed >= lower) & (observed <= upper)))
    interval_calibration = {
        "method": "cross-conformal out-of-fold residuals on the outer training split",
        "target_coverage": CONFORMAL_TARGET_COVERAGE,
        "alpha": CONFORMAL_ALPHA,
        "calibration_folds": CONFORMAL_CV_FOLDS,
        "calibration_rows": int(len(train_index)),
        "half_width_mpa": round(float(half_width), 4),
        "mean_width_mpa": round(float(2.0 * half_width), 4),
        "empirical_coverage": round(coverage, 4),
    }
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model": (
            "train-fitted atomic-fraction vector + ExtraTreesRegressor("
            "n_estimators=300, n_jobs=1) with inner-CV selection of "
            "max_features and min_samples_leaf"
        ),
        "model_id": "nested_extra_trees",
        "fold": fold,
        "split_random_state": 18012019,
        "split_fingerprint": _ids_fingerprint(train_ids, test_ids),
        "n_samples": int(len(frame)),
        "n_train": int(len(train_index)),
        "n_test": int(len(test_index)),
        "n_features": len(vocabulary),
        "target_unit": "MPa",
        "inner_cv_folds": NESTED_MATBENCH_INNER_FOLDS,
        "inner_cv_scoring": "neg_mean_absolute_error",
        "candidate_count": _grid_size(NESTED_MATBENCH_PARAM_GRID),
        "selected_params": selected_params,
        "inner_cv_best_mae_mpa": round(float(-search.best_score_), 4),
        "interval_calibration": interval_calibration,
        "metrics": metrics,
    }


def run_matbench_steels_nested_multi(
    data_dir: str | Path, folds: Sequence[int] = OFFICIAL_FOLDS
) -> dict:
    """Aggregate nested D04 results over the official folds."""
    runs = [run_matbench_steels_nested(data_dir, fold=fold) for fold in folds]
    metric_names = ("mae_mpa", "rmse_mpa", "r2", "naive_mae_mpa")
    gate = evaluate_decision_gate(
        [run["metrics"]["naive_mae_mpa"] for run in runs],
        [run["metrics"]["mae_mpa"] for run in runs],
        [run["metrics"]["r2"] for run in runs],
    )
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model_id": "nested_extra_trees",
        "model": runs[0]["model"],
        "folds": list(folds),
        "n_folds": len(runs),
        "n_samples": runs[0]["n_samples"],
        "target_unit": "MPa",
        "inner_cv_folds": NESTED_MATBENCH_INNER_FOLDS,
        "inner_cv_scoring": "neg_mean_absolute_error",
        "candidate_count": _grid_size(NESTED_MATBENCH_PARAM_GRID),
        "metrics": {
            name: _summary([run["metrics"][name] for run in runs])
            for name in metric_names
        },
        "inner_cv_best_mae_mpa": _summary(
            [run["inner_cv_best_mae_mpa"] for run in runs]
        ),
        "interval_calibration": {
            "method": runs[0]["interval_calibration"]["method"],
            "target_coverage": CONFORMAL_TARGET_COVERAGE,
            "alpha": CONFORMAL_ALPHA,
            "calibration_folds": CONFORMAL_CV_FOLDS,
            "calibration_rows": runs[0]["interval_calibration"]["calibration_rows"],
            "half_width_mpa": _summary(
                [run["interval_calibration"]["half_width_mpa"] for run in runs]
            ),
            "mean_width_mpa": _summary(
                [run["interval_calibration"]["mean_width_mpa"] for run in runs]
            ),
            "empirical_coverage": _summary(
                [run["interval_calibration"]["empirical_coverage"] for run in runs]
            ),
        },
        "per_fold": [
            {
                "fold": run["fold"],
                "metrics": run["metrics"],
                "split_fingerprint": run["split_fingerprint"],
                "selected_params": run["selected_params"],
                "inner_cv_best_mae_mpa": run["inner_cv_best_mae_mpa"],
                "interval_calibration": run["interval_calibration"],
            }
            for run in runs
        ],
        "decision_gate": gate,
    }


UCI_FAULT_CLASSES: tuple[str, ...] = (
    "Pastry",
    "Z_Scratch",
    "K_Scatch",
    "Stains",
    "Dirtiness",
    "Bumps",
    "Other_Faults",
)
ADAPTIVE_CONFORMAL_EPS = 10.0
HYBRID_BLEND_WEIGHTS: tuple[float, ...] = (0.0, 0.35, 0.5)


def _tree_mean_std(estimator: ExtraTreesRegressor, features: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ensemble mean and across-tree standard deviation for uncertainty scaling."""
    tree_preds = np.column_stack([tree.predict(features) for tree in estimator.estimators_])
    return tree_preds.mean(axis=1), tree_preds.std(axis=1)


def run_uci_faults_multiclass_ensemble(
    data_dir: str | Path, seeds: Sequence[int] = PREDICTIVE_SEEDS
) -> dict[str, Any]:
    """Run single-label 7-class ExtraTrees + GradientBoosting soft-voting ensemble on D01.

    UCI Steel Plates Faults has mutually exclusive 1-of-7 fault classes (every row
    has exactly one active fault). Training as a single-label multiclass problem
    prevents invalid zero-fault or multi-fault predictions and captures per-class
    confusion diagnostics.
    """
    frame = load_uci_faults(Path(data_dir) / DATA_FILES["D01"][0])
    features = frame.iloc[:, :27].to_numpy(dtype=float)
    label_matrix = frame.iloc[:, 27:].to_numpy(dtype=int)
    if not np.all(label_matrix.sum(axis=1) == 1):
        raise ValueError("UCI fault labels are not strictly mutually exclusive.")
    target = np.argmax(label_matrix, axis=1)
    class_names = list(frame.columns[27:])

    per_seed: list[dict[str, Any]] = []
    agg_cm = np.zeros((len(class_names), len(class_names)), dtype=int)

    for seed in seeds:
        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=seed,
            shuffle=True,
            stratify=target,
        )
        et = ExtraTreesClassifier(
            n_estimators=300, max_features=0.7, random_state=seed, n_jobs=1
        ).fit(x_train, y_train)
        gbc = GradientBoostingClassifier(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.8,
            random_state=seed,
        ).fit(x_train, y_train)

        proba_et = et.predict_proba(x_test)
        proba_gbc = gbc.predict_proba(x_test)
        pred_et = np.argmax(proba_et, axis=1)
        pred_gbc = np.argmax(proba_gbc, axis=1)
        pred_ens = np.argmax(0.5 * (proba_et + proba_gbc), axis=1)

        agg_cm += confusion_matrix(y_test, pred_ens, labels=list(range(len(class_names))))
        per_seed.append(
            {
                "seed": int(seed),
                "metrics": _round_metrics(
                    {
                        "accuracy": accuracy_score(y_test, pred_ens),
                        "macro_f1": f1_score(y_test, pred_ens, average="macro"),
                    }
                ),
                "extra_trees_metrics": _round_metrics(
                    {
                        "accuracy": accuracy_score(y_test, pred_et),
                        "macro_f1": f1_score(y_test, pred_et, average="macro"),
                    }
                ),
                "gradient_boosting_metrics": _round_metrics(
                    {
                        "accuracy": accuracy_score(y_test, pred_gbc),
                        "macro_f1": f1_score(y_test, pred_gbc, average="macro"),
                    }
                ),
            }
        )

    row_sums = agg_cm.sum(axis=1, keepdims=True)
    cm_normalized = np.divide(
        agg_cm, row_sums, out=np.zeros_like(agg_cm, dtype=float), where=row_sums > 0
    )
    return {
        "dataset": "D01 UCI Steel Plates Faults (7-class mutually exclusive)",
        "model_id": "multiclass_soft_voting_ensemble",
        "model": (
            "Soft-voting 7-class ensemble: ExtraTreesClassifier(n_estimators=300, "
            "max_features=0.7) + GradientBoostingClassifier(n_estimators=120, "
            "lr=0.08, max_depth=4, subsample=0.8)"
        ),
        "seeds": list(seeds),
        "n_runs": len(per_seed),
        "n_samples": int(len(frame)),
        "n_features": 27,
        "n_classes": len(class_names),
        "class_names": class_names,
        "metrics": {
            "accuracy": _summary([row["metrics"]["accuracy"] for row in per_seed]),
            "macro_f1": _summary([row["metrics"]["macro_f1"] for row in per_seed]),
        },
        "comparators": {
            "multiclass_extra_trees": {
                "accuracy": _summary(
                    [row["extra_trees_metrics"]["accuracy"] for row in per_seed]
                ),
                "macro_f1": _summary(
                    [row["extra_trees_metrics"]["macro_f1"] for row in per_seed]
                ),
            },
            "multiclass_gradient_boosting": {
                "accuracy": _summary(
                    [row["gradient_boosting_metrics"]["accuracy"] for row in per_seed]
                ),
                "macro_f1": _summary(
                    [row["gradient_boosting_metrics"]["macro_f1"] for row in per_seed]
                ),
            },
        },
        "confusion_matrix_counts": agg_cm.tolist(),
        "confusion_matrix_normalized": [
            [round(float(val), 4) for val in row] for row in cm_normalized
        ],
        "per_seed": per_seed,
    }


def _fit_hybrid_pair(
    train_comps: np.ndarray,
    train_y: np.ndarray,
    max_features: float,
    min_samples_leaf: int,
) -> tuple[Pipeline, Pipeline]:
    raw_pipe = Pipeline(
        [
            ("vectorizer", CompositionVectorizer()),
            (
                "model",
                ExtraTreesRegressor(
                    n_estimators=300,
                    max_features=max_features,
                    min_samples_leaf=min_samples_leaf,
                    random_state=42,
                    n_jobs=1,
                ),
            ),
        ]
    ).fit(train_comps, train_y)
    phys_pipe = Pipeline(
        [
            ("vectorizer", MetallurgicalDescriptorVectorizer()),
            (
                "model",
                ExtraTreesRegressor(
                    n_estimators=300,
                    max_features=max_features,
                    min_samples_leaf=min_samples_leaf,
                    random_state=42,
                    n_jobs=1,
                ),
            ),
        ]
    ).fit(train_comps, train_y)
    return raw_pipe, phys_pipe


def _predict_hybrid_with_spread(
    raw_pipe: Pipeline,
    phys_pipe: Pipeline,
    comps: np.ndarray,
    phys_weight: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Return blended prediction and tree-spread uncertainty scale sigma(x)."""
    x_raw = raw_pipe.named_steps["vectorizer"].transform(comps)
    mu_raw, sd_raw = _tree_mean_std(raw_pipe.named_steps["model"], x_raw)
    if phys_weight <= 0.0:
        return mu_raw, sd_raw
    x_phys = phys_pipe.named_steps["vectorizer"].transform(comps)
    mu_phys, sd_phys = _tree_mean_std(phys_pipe.named_steps["model"], x_phys)
    mu = (1.0 - phys_weight) * mu_raw + phys_weight * mu_phys
    sd = (1.0 - phys_weight) * sd_raw + phys_weight * sd_phys
    return mu, sd


def adaptive_conformal_quantile(
    train_comps: np.ndarray,
    train_y: np.ndarray,
    max_features: float,
    min_samples_leaf: int,
    phys_weight: float,
    *,
    alpha: float = CONFORMAL_ALPHA,
    n_splits: int = CONFORMAL_CV_FOLDS,
    seed: int = CONFORMAL_CV_SEED,
    eps: float = ADAPTIVE_CONFORMAL_EPS,
) -> float:
    """Return locally-weighted cross-conformal quantile q from training data only.

    Nonconformity score: s_i = |y_i - y_hat_i| / (sigma_i + eps), where sigma_i
    is the ensemble across-tree standard deviation. Outer test data is never used.
    """
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    scores: list[float] = []
    for fit_idx, cal_idx in splitter.split(train_comps):
        raw_pipe, phys_pipe = _fit_hybrid_pair(
            train_comps[fit_idx], train_y[fit_idx], max_features, min_samples_leaf
        )
        mu, sd = _predict_hybrid_with_spread(
            raw_pipe, phys_pipe, train_comps[cal_idx], phys_weight
        )
        norm_res = np.abs(mu - train_y[cal_idx]) / (sd + eps)
        scores.extend(norm_res.tolist())
    ordered = np.sort(np.asarray(scores, dtype=float))
    rank = int(np.ceil((len(ordered) + 1) * (1.0 - alpha)))
    return float(ordered[max(0, min(rank - 1, len(ordered) - 1))])


def run_matbench_steels_physics_hybrid(
    data_dir: str | Path, folds: Sequence[int] = OFFICIAL_FOLDS
) -> dict[str, Any]:
    """Run leakage-safe hybrid composition + metallurgical descriptor ensemble on D04.

    Includes:
    - Inner-CV selection of ExtraTrees hyperparameters and physics-descriptor blend
      weight strictly on each outer training fold.
    - GradientBoostingRegressor comparator with metallurgical descriptors.
    - Locally-weighted (adaptive) 90% cross-conformal prediction intervals.
    - Per-sample out-of-fold parity records for all 312 steels.
    """
    root = Path(data_dir)
    frame = load_matbench_steels(root / DATA_FILES["D04"][0])
    splits = load_matbench_splits(root / DATA_FILES["D04-splits"][0])
    position = {sample_id: index for index, sample_id in enumerate(frame["id"])}
    compositions = np.asarray(frame["composition"].tolist(), dtype=object)
    target = frame["yield_strength_mpa"].to_numpy(dtype=float)

    per_fold: list[dict[str, Any]] = []
    gbr_per_fold: list[dict[str, Any]] = []
    parity_points: list[dict[str, Any]] = []

    for fold in folds:
        split = splits[f"fold_{fold}"]
        train_ids, test_ids = split["train"], split["test"]
        train_idx = [position[sid] for sid in train_ids]
        test_idx = [position[sid] for sid in test_ids]
        tr_c, tr_y = compositions[train_idx], target[train_idx]
        te_c, te_y = compositions[test_idx], target[test_idx]

        # Inner 4-fold CV on outer training split only to select (mf, leaf, phys_weight)
        inner_kf = KFold(n_splits=NESTED_MATBENCH_INNER_FOLDS, shuffle=True, random_state=42)
        best_score = float("inf")
        best_cfg = (1.0, 1, 0.35)
        for mf in (0.5, 1.0):
            for leaf in (1, 2):
                oof_raw = np.zeros(len(tr_y), dtype=float)
                oof_phys = np.zeros(len(tr_y), dtype=float)
                for fi, vi in inner_kf.split(tr_c):
                    r_pipe, p_pipe = _fit_hybrid_pair(tr_c[fi], tr_y[fi], mf, leaf)
                    oof_raw[vi] = r_pipe.predict(tr_c[vi])
                    oof_phys[vi] = p_pipe.predict(tr_c[vi])
                for w_phys in HYBRID_BLEND_WEIGHTS:
                    oof_blend = (1.0 - w_phys) * oof_raw + w_phys * oof_phys
                    mae_val = float(mean_absolute_error(tr_y, oof_blend))
                    if mae_val < best_score:
                        best_score = mae_val
                        best_cfg = (mf, leaf, w_phys)

        sel_mf, sel_leaf, sel_w = best_cfg
        raw_pipe, phys_pipe = _fit_hybrid_pair(tr_c, tr_y, sel_mf, sel_leaf)
        preds, spread = _predict_hybrid_with_spread(raw_pipe, phys_pipe, te_c, sel_w)

        q_scale = adaptive_conformal_quantile(tr_c, tr_y, sel_mf, sel_leaf, sel_w)
        half_widths = q_scale * (spread + ADAPTIVE_CONFORMAL_EPS)
        coverage = float(
            np.mean((te_y >= preds - half_widths) & (te_y <= preds + half_widths))
        )

        error = preds - te_y
        naive_mae = float(
            mean_absolute_error(te_y, np.full(len(te_y), tr_y.mean()))
        )
        fold_metrics = _round_metrics(
            {
                "mae_mpa": mean_absolute_error(te_y, preds),
                "rmse_mpa": float(np.sqrt(np.mean(error**2))),
                "r2": float(1.0 - np.sum(error**2) / np.sum((te_y - te_y.mean()) ** 2)),
                "naive_mae_mpa": naive_mae,
            }
        )
        adaptive_cal = {
            "method": "locally-weighted cross-conformal (tree-spread normalized residuals on train only)",
            "target_coverage": CONFORMAL_TARGET_COVERAGE,
            "alpha": CONFORMAL_ALPHA,
            "calibration_folds": CONFORMAL_CV_FOLDS,
            "quantile_scale": round(float(q_scale), 4),
            "mean_half_width_mpa": round(float(np.mean(half_widths)), 4),
            "mean_width_mpa": round(float(np.mean(2.0 * half_widths)), 4),
            "median_width_mpa": round(float(np.median(2.0 * half_widths)), 4),
            "empirical_coverage": round(coverage, 4),
        }
        per_fold.append(
            {
                "fold": int(fold),
                "metrics": fold_metrics,
                "split_fingerprint": _ids_fingerprint(train_ids, test_ids),
                "selected_params": {
                    "max_features": sel_mf,
                    "min_samples_leaf": sel_leaf,
                    "physics_weight": sel_w,
                },
                "inner_cv_best_mae_mpa": round(best_score, 4),
                "adaptive_interval": adaptive_cal,
            }
        )

        for obs_v, pred_v, hw_v in zip(te_y, preds, half_widths, strict=True):
            parity_points.append(
                {
                    "fold": int(fold),
                    "observed_mpa": round(float(obs_v), 2),
                    "predicted_mpa": round(float(pred_v), 2),
                    "half_width_mpa": round(float(hw_v), 2),
                }
            )

        # Boosting comparator with metallurgical descriptors on identical split
        gbr_pipe = Pipeline(
            [
                ("vectorizer", MetallurgicalDescriptorVectorizer()),
                (
                    "model",
                    GradientBoostingRegressor(
                        n_estimators=200,
                        learning_rate=0.05,
                        max_depth=3,
                        subsample=0.8,
                        random_state=42,
                    ),
                ),
            ]
        ).fit(tr_c, tr_y)
        gbr_pred = gbr_pipe.predict(te_c)
        gbr_err = gbr_pred - te_y
        gbr_per_fold.append(
            {
                "fold": int(fold),
                "metrics": _round_metrics(
                    {
                        "mae_mpa": mean_absolute_error(te_y, gbr_pred),
                        "rmse_mpa": float(np.sqrt(np.mean(gbr_err**2))),
                        "r2": float(
                            1.0 - np.sum(gbr_err**2) / np.sum((te_y - te_y.mean()) ** 2)
                        ),
                        "naive_mae_mpa": naive_mae,
                    }
                ),
            }
        )

    gate = evaluate_decision_gate(
        [row["metrics"]["naive_mae_mpa"] for row in per_fold],
        [row["metrics"]["mae_mpa"] for row in per_fold],
        [row["metrics"]["r2"] for row in per_fold],
    )
    metric_names = ("mae_mpa", "rmse_mpa", "r2", "naive_mae_mpa")
    return {
        "dataset": "D04 matbench_steels (R08)",
        "model_id": "physics_hybrid_extra_trees",
        "model": (
            "Inner-CV hybrid ensemble: atomic-fraction ExtraTrees + "
            "MetallurgicalDescriptorVectorizer ExtraTrees (adaptive 90% PI)"
        ),
        "folds": list(folds),
        "n_folds": len(per_fold),
        "n_samples": int(len(frame)),
        "target_unit": "MPa",
        "metrics": {
            name: _summary([row["metrics"][name] for row in per_fold])
            for name in metric_names
        },
        "adaptive_interval": {
            "method": per_fold[0]["adaptive_interval"]["method"],
            "target_coverage": CONFORMAL_TARGET_COVERAGE,
            "alpha": CONFORMAL_ALPHA,
            "calibration_folds": CONFORMAL_CV_FOLDS,
            "mean_width_mpa": _summary(
                [row["adaptive_interval"]["mean_width_mpa"] for row in per_fold]
            ),
            "median_width_mpa": _summary(
                [row["adaptive_interval"]["median_width_mpa"] for row in per_fold]
            ),
            "empirical_coverage": _summary(
                [row["adaptive_interval"]["empirical_coverage"] for row in per_fold]
            ),
        },
        "boosting_comparator": {
            "model": "MetallurgicalDescriptorVectorizer + GradientBoostingRegressor(n_estimators=200, lr=0.05, max_depth=3)",
            "metrics": {
                name: _summary([row["metrics"][name] for row in gbr_per_fold])
                for name in metric_names
            },
            "per_fold": gbr_per_fold,
        },
        "parity_points": parity_points,
        "per_fold": per_fold,
        "decision_gate": gate,
    }


def _run_twice(name: str, function, kwargs: dict[str, Any]) -> dict:
    first = function(**kwargs)
    second = function(**kwargs)
    if first != second:
        raise RuntimeError(
            f"Non-reproducible payload for {name}: {first!r} != {second!r}"
        )
    return first


def reproduce(data_dir: str | Path, seed: int = 42, fold: int = 0) -> dict:
    """Run every experiment twice; fail unless all payloads are identical."""
    data_dir = Path(data_dir)
    data = verify_data_dir(data_dir)
    experiments: dict[str, Any] = {}

    experiments["uci_faults"] = _run_twice(
        "uci_faults",
        run_uci_faults,
        {"data_dir": data_dir, "seed": seed, "model": "logistic"},
    )
    experiments["matbench_steels"] = _run_twice(
        "matbench_steels",
        run_matbench_steels,
        {"data_dir": data_dir, "fold": fold, "model": "ridge"},
    )
    experiments["uci_faults_random_forest"] = _run_twice(
        "uci_faults_random_forest",
        run_uci_faults_multi,
        {"data_dir": data_dir, "seeds": PREDICTIVE_SEEDS, "model": "random_forest"},
    )
    experiments["matbench_steels_ridge_folds"] = _run_twice(
        "matbench_steels_ridge_folds",
        run_matbench_steels_multi,
        {"data_dir": data_dir, "folds": OFFICIAL_FOLDS, "model": "ridge"},
    )
    experiments["matbench_steels_random_forest"] = _run_twice(
        "matbench_steels_random_forest",
        run_matbench_steels_multi,
        {"data_dir": data_dir, "folds": OFFICIAL_FOLDS, "model": "random_forest"},
    )
    experiments["uci_faults_extra_trees"] = _run_twice(
        "uci_faults_extra_trees",
        run_uci_faults_multi,
        {"data_dir": data_dir, "seeds": PREDICTIVE_SEEDS, "model": "extra_trees"},
    )
    experiments["matbench_steels_extra_trees"] = _run_twice(
        "matbench_steels_extra_trees",
        run_matbench_steels_multi,
        {"data_dir": data_dir, "folds": OFFICIAL_FOLDS, "model": "extra_trees"},
    )
    experiments["uci_faults_nested_extra_trees"] = _run_twice(
        "uci_faults_nested_extra_trees",
        run_uci_faults_nested_multi,
        {"data_dir": data_dir, "seeds": PREDICTIVE_SEEDS},
    )
    experiments["matbench_steels_nested_extra_trees"] = _run_twice(
        "matbench_steels_nested_extra_trees",
        run_matbench_steels_nested_multi,
        {"data_dir": data_dir, "folds": OFFICIAL_FOLDS},
    )
    experiments["uci_faults_multiclass_ensemble"] = _run_twice(
        "uci_faults_multiclass_ensemble",
        run_uci_faults_multiclass_ensemble,
        {"data_dir": data_dir, "seeds": PREDICTIVE_SEEDS},
    )
    experiments["matbench_steels_physics_hybrid"] = _run_twice(
        "matbench_steels_physics_hybrid",
        run_matbench_steels_physics_hybrid,
        {"data_dir": data_dir, "folds": OFFICIAL_FOLDS},
    )

    rf_d01 = experiments["uci_faults_random_forest"]["metrics"]
    rf_d04 = experiments["matbench_steels_random_forest"]["metrics"]
    et_d01 = experiments["uci_faults_extra_trees"]["metrics"]
    et_d04 = experiments["matbench_steels_extra_trees"]["metrics"]
    nested_u = experiments["uci_faults_nested_extra_trees"]["metrics"]
    nested_d = experiments["matbench_steels_nested_extra_trees"]["metrics"]
    mc_u = experiments["uci_faults_multiclass_ensemble"]["metrics"]
    hyb_d = experiments["matbench_steels_physics_hybrid"]["metrics"]
    hyb_adaptive = experiments["matbench_steels_physics_hybrid"]["adaptive_interval"]
    hyb_gate = experiments["matbench_steels_physics_hybrid"]["decision_gate"]
    intervals = experiments["matbench_steels_nested_extra_trees"][
        "interval_calibration"
    ]
    gate = experiments["matbench_steels_nested_extra_trees"]["decision_gate"]
    mae_gain_vs_rf = (
        rf_d04["mae_mpa"]["mean"] - nested_d["mae_mpa"]["mean"]
    ) / rf_d04["mae_mpa"]["mean"]
    mae_gain_vs_et = (
        et_d04["mae_mpa"]["mean"] - nested_d["mae_mpa"]["mean"]
    ) / et_d04["mae_mpa"]["mean"]
    d01_gain_pp = (
        nested_u["accuracy"]["mean"] - et_d01["accuracy"]["mean"]
    ) * 100.0
    d01_mc_gain_pp = (
        mc_u["accuracy"]["mean"] - nested_u["accuracy"]["mean"]
    ) * 100.0
    summary = {
        "headline_model": (
            "UCI: 7-class Soft-Voting Ensemble (ET + GBC) · "
            "MatBench: Inner-CV Hybrid Physics/Composition ExtraTrees (Adaptive 90% PI)"
        ),
        "case_verdict": (
            "predictive gate passed"
            if (gate["passed"] and hyb_gate["passed"])
            else "predictive gate not passed"
        ),
        "decision_gate_passed": bool(gate["passed"] and hyb_gate["passed"]),
        "nested_search": {
            "outer_protocol": (
                "D01: five fixed stratified seeds; D04: five official MatBench folds"
            ),
            "d01_inner_cv": {
                "folds": NESTED_UCI_INNER_FOLDS,
                "scoring": "macro_f1",
                "candidate_count": _grid_size(NESTED_UCI_PARAM_GRID),
            },
            "d04_inner_cv": {
                "folds": NESTED_MATBENCH_INNER_FOLDS,
                "scoring": "neg_mean_absolute_error",
                "candidate_count": _grid_size(NESTED_MATBENCH_PARAM_GRID),
            },
            "leakage_control": (
                "GridSearchCV refits only on the outer training split; the "
                "composition vectorizer is cloned and fitted inside each inner "
                "training split"
            ),
            "d04_interval_calibration": {
                "method": intervals["method"],
                "target_coverage": CONFORMAL_TARGET_COVERAGE,
                "calibration_folds": CONFORMAL_CV_FOLDS,
                "leakage_control": (
                    "out-of-fold residuals come only from the outer training "
                    "split; the outer test fold sets neither width nor quantile"
                ),
            },
        },
        "d01_nested_accuracy": nested_u["accuracy"]["mean"],
        "d01_nested_accuracy_std": nested_u["accuracy"]["std"],
        "d01_nested_macro_f1": nested_u["macro_f1"]["mean"],
        "d01_nested_macro_f1_std": nested_u["macro_f1"]["std"],
        "d01_multiclass_accuracy": mc_u["accuracy"]["mean"],
        "d01_multiclass_accuracy_std": mc_u["accuracy"]["std"],
        "d01_multiclass_macro_f1": mc_u["macro_f1"]["mean"],
        "d01_multiclass_macro_f1_std": mc_u["macro_f1"]["std"],
        "d01_multiclass_gain_vs_nested_pp": round(float(d01_mc_gain_pp), 2),
        "d04_nested_mae_mpa": nested_d["mae_mpa"]["mean"],
        "d04_nested_mae_std_mpa": nested_d["mae_mpa"]["std"],
        "d04_nested_rmse_mpa": nested_d["rmse_mpa"]["mean"],
        "d04_nested_r2": nested_d["r2"]["mean"],
        "d04_nested_r2_std": nested_d["r2"]["std"],
        "d04_hybrid_mae_mpa": hyb_d["mae_mpa"]["mean"],
        "d04_hybrid_mae_std_mpa": hyb_d["mae_mpa"]["std"],
        "d04_hybrid_rmse_mpa": hyb_d["rmse_mpa"]["mean"],
        "d04_hybrid_r2": hyb_d["r2"]["mean"],
        "d04_hybrid_r2_std": hyb_d["r2"]["std"],
        "d04_adaptive_interval_empirical_coverage": hyb_adaptive["empirical_coverage"]["mean"],
        "d04_adaptive_interval_empirical_coverage_std": hyb_adaptive["empirical_coverage"]["std"],
        "d04_adaptive_interval_mean_width_mpa": hyb_adaptive["mean_width_mpa"]["mean"],
        "d04_adaptive_interval_median_width_mpa": hyb_adaptive["median_width_mpa"]["mean"],
        "d04_interval_target_coverage": CONFORMAL_TARGET_COVERAGE,
        "d04_interval_empirical_coverage": intervals["empirical_coverage"]["mean"],
        "d04_interval_empirical_coverage_std": intervals["empirical_coverage"]["std"],
        "d04_interval_half_width_mpa": intervals["half_width_mpa"]["mean"],
        "d04_interval_mean_width_mpa": intervals["mean_width_mpa"]["mean"],
        "d01_accuracy_gain_vs_fixed_extra_trees_pp": round(float(d01_gain_pp), 2),
        "d04_mae_improvement_vs_fixed_extra_trees": round(float(mae_gain_vs_et), 4),
        "d01_extra_trees_accuracy": et_d01["accuracy"]["mean"],
        "d01_extra_trees_accuracy_std": et_d01["accuracy"]["std"],
        "d01_extra_trees_macro_f1": et_d01["macro_f1"]["mean"],
        "d01_extra_trees_macro_f1_std": et_d01["macro_f1"]["std"],
        "d04_extra_trees_mae_mpa": et_d04["mae_mpa"]["mean"],
        "d04_extra_trees_mae_std_mpa": et_d04["mae_mpa"]["std"],
        "d04_extra_trees_rmse_mpa": et_d04["rmse_mpa"]["mean"],
        "d04_extra_trees_r2": et_d04["r2"]["mean"],
        "d04_extra_trees_r2_std": et_d04["r2"]["std"],
        "d04_naive_mae_mpa": nested_d["naive_mae_mpa"]["mean"],
        "d04_mae_improvement_vs_random_forest": round(float(mae_gain_vs_rf), 4),
        "d01_random_forest_accuracy": rf_d01["accuracy"]["mean"],
        "d04_random_forest_mae_mpa": rf_d04["mae_mpa"]["mean"],
        "d04_random_forest_r2": rf_d04["r2"]["mean"],
        "external_comparator_mae_mpa": 87.7627,
        "external_comparator_note": (
            "MatBench MODNet v0.1.12, different model and featurization; "
            "quoted as external literature, not reproduced"
        ),
    }

    return {
        "seed": seed,
        "fold": fold,
        "determinism_check": "two consecutive runs, all experiment payloads identical",
        "code_fingerprint": source_fingerprint(Path(__file__).parent),
        "data": data,
        "environment": environment_info(),
        "experiments": experiments,
        "summary": summary,
    }
