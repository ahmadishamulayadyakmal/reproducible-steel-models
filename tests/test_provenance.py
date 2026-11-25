"""Checks for hashing, source fingerprints and deterministic JSON output."""

from __future__ import annotations

import hashlib
import json

from metalkit.provenance import environment_info, sha256_file, source_fingerprint, write_json


def test_sha256_file_matches_known_digest(tmp_path):
    target = tmp_path / "sample.bin"
    target.write_bytes(b"metallurgy")

    assert sha256_file(target) == hashlib.sha256(b"metallurgy").hexdigest()


def test_environment_info_lists_core_packages():
    info = environment_info()

    assert info["python"]
    for name in ("numpy", "pandas", "scipy", "scikit-learn"):
        assert name in info["packages"]


def test_write_json_is_sorted_and_repeatable(tmp_path):
    first = write_json(tmp_path / "one.json", {"b": 1, "a": {"d": 2, "c": 3}})
    second = write_json(tmp_path / "two.json", {"a": {"c": 3, "d": 2}, "b": 1})

    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
    assert json.loads(first.read_text(encoding="utf-8")) == {
        "a": {"c": 3, "d": 2},
        "b": 1,
    }


def test_source_fingerprint_changes_with_source_bytes(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.py").write_text("x = 1\n", encoding="utf-8")
    before = source_fingerprint(source)

    (source / "a.py").write_text("x = 2\n", encoding="utf-8")

    assert source_fingerprint(source) != before
