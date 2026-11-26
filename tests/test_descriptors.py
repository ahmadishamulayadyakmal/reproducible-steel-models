"""Unit tests for deterministic metallurgical composition descriptors."""

from __future__ import annotations

import numpy as np
import pytest

from metalkit.descriptors import (
    ELEMENT_PROPERTIES,
    METALLURGICAL_INDEX_NAMES,
    PROPERTY_NAMES,
    MetallurgicalDescriptorVectorizer,
    metallurgical_features,
    parse_composition,
)


def test_parse_composition_is_scale_invariant():
    assert parse_composition("Fe80C20") == pytest.approx(parse_composition("Fe0.8C0.2"))


def test_metallurgical_features_shape_and_determinism():
    formulas = ["Fe0.85Cr0.12Ni0.02C0.01", "Fe0.70Ni0.18Co0.08Mo0.04"]
    vec = MetallurgicalDescriptorVectorizer().fit(formulas)
    first = vec.transform(formulas)
    second = vec.transform(formulas)

    expected_cols = len(vec.vocabulary_) + len(PROPERTY_NAMES) * 4 + len(METALLURGICAL_INDEX_NAMES)
    assert first.shape == (2, expected_cols)
    assert np.array_equal(first, second)


def test_metallurgical_vectorizer_ignores_unseen_test_elements():
    vec = MetallurgicalDescriptorVectorizer().fit(["Fe80C20"])
    assert vec.vocabulary_ == ["C", "Fe"]

    # Cu is unseen in training; must be ignored without leaking into feature count
    out = vec.transform(["Fe79C20Cu1"])
    expected_cols = 2 + len(PROPERTY_NAMES) * 4 + len(METALLURGICAL_INDEX_NAMES)
    assert out.shape == (1, expected_cols)
    # Raw atomic fractions for C and Fe remain [0.20, 0.79]
    assert out[0, 0] == pytest.approx(0.20)
    assert out[0, 1] == pytest.approx(0.79)


def test_physical_indices_are_nonnegative_and_sensible():
    # Pure Fe has zero atomic-size mismatch and zero mixing entropy
    vec = MetallurgicalDescriptorVectorizer().fit(["Fe1.0", "Fe0.70Ni0.18Co0.08Mo0.04"])
    feats = vec.transform(["Fe1.0", "Fe0.70Ni0.18Co0.08Mo0.04"])
    meta_start = len(vec.vocabulary_) + len(PROPERTY_NAMES) * 4

    # Pure Fe: delta == 0, mixing_entropy == 0, n_elements == 1
    assert feats[0, meta_start + 0] == pytest.approx(0.0)
    assert feats[0, meta_start + 2] == pytest.approx(0.0)
    assert feats[0, meta_start + 3] == pytest.approx(1.0)

    # Multi-element alloy: positive delta, positive mixing entropy, n_elements == 4
    assert feats[1, meta_start + 0] > 0.0
    assert feats[1, meta_start + 2] > 0.5
    assert feats[1, meta_start + 3] == pytest.approx(4.0)


def test_element_properties_cover_all_standard_steel_elements():
    for symbol in ("Al", "C", "Co", "Cr", "Fe", "Mn", "Mo", "N", "Nb", "Ni", "Si", "Ti", "V", "W"):
        assert symbol in ELEMENT_PROPERTIES
        assert len(ELEMENT_PROPERTIES[symbol]) == len(PROPERTY_NAMES)
