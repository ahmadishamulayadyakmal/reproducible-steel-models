"""Loaders and checksum verification for the two open C01 datasets."""

from __future__ import annotations

import gzip
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

from metalkit.provenance import sha256_file

# (filename, SHA-256, bytes, upstream URL) — keep in sync with data/SOURCES.md.
DATA_FILES: dict[str, tuple[str, str, int, str]] = {
    "D01": (
        "steel_plates_faults.zip",
        "cb8eb9859198b63f053e443513036b401746fa517ef58bd17c846c6741c93919",
        100890,
        "https://archive.ics.uci.edu/static/public/198/steel+plates+faults.zip",
    ),
    "D04": (
        "matbench_steels.json.gz",
        "473bc4957b2ea5e6465aef84bc29bb48ac34db27d69ea4ec5f508745c6fae252",
        8836,
        "https://github.com/materialsproject/matbench/blob/main/benchmarks/"
        "matbench_v0.1_Atomic_Affine_QRF/inputs/matbench_steels.json.gz",
    ),
    "D04-splits": (
        "steels_splits.json",
        "ef3bc6cf09ec08a23a8d0a6f1e04c0e2108296644d5e522abd8900f55e2b1a4f",
        42676,
        "https://github.com/materialsproject/matbench/blob/main/benchmarks/"
        "matbench_v0.1_Atomic_Affine_QRF/inputs/steels_splits.json",
    ),
}


def verify_data_dir(data_dir: str | Path) -> dict[str, dict]:
    """Verify all pinned raw files and return manifest entries without paths."""
    root = Path(data_dir)
    verified: dict[str, dict] = {}
    for key, (filename, expected_hash, expected_bytes, url) in DATA_FILES.items():
        path = root / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {filename}. Download it as documented in data/SOURCES.md."
            )
        digest = sha256_file(path)
        if digest != expected_hash or path.stat().st_size != expected_bytes:
            raise ValueError(
                f"Checksum/size mismatch for {filename}: expected "
                f"{expected_hash} / {expected_bytes} bytes, got "
                f"{digest} / {path.stat().st_size} bytes"
            )
        verified[key] = {
            "file": filename,
            "sha256": digest,
            "bytes": expected_bytes,
            "url": url,
        }
    return verified


def load_uci_faults(path: str | Path) -> pd.DataFrame:
    """Return 27 features + 7 fault indicators (1941 rows) from UCI D01."""
    with zipfile.ZipFile(path) as archive:
        names = [
            line.strip()
            for line in archive.read("Faults27x7_var").decode("latin-1").splitlines()
            if line.strip()
        ]
        payload = io.StringIO(archive.read("Faults.NNA").decode("latin-1"))
        frame = pd.read_csv(payload, sep="\t", header=None, names=names)

    if frame.shape != (1941, 34):
        raise ValueError(f"Unexpected UCI fault table shape: {frame.shape}")
    return frame


def load_matbench_steels(path: str | Path) -> pd.DataFrame:
    """Return 312 compositions with a stable ``mb-steels-NNN`` sample ID."""
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)

    frame = pd.DataFrame(payload["data"], columns=payload["columns"])
    if list(frame.columns) != ["composition", "yield strength"]:
        raise ValueError(f"Unexpected MatBench columns: {list(frame.columns)}")
    frame.insert(0, "id", [f"mb-steels-{i:03d}" for i in range(1, len(frame) + 1)])
    frame = frame.rename(columns={"yield strength": "yield_strength_mpa"})
    return frame


def load_matbench_splits(path: str | Path) -> dict[str, dict[str, list[str]]]:
    """Return the official five folds for ``matbench_steels``."""
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)

    metadata = payload["metadata"]
    if metadata != {"n_splits": 5, "random_state": 18012019, "shuffle": True}:
        raise ValueError(f"Unexpected MatBench split metadata: {metadata}")
    return payload["splits"]["matbench_steels"]
