"""Deterministic, pure-NumPy metallurgical composition descriptors.

Computes Magpie-style composition-weighted elemental statistics and physical
metallurgy indices (atomic-size mismatch delta, electronegativity spread,
valence electron concentration, configurational mixing entropy, interstitial
fraction, and carbon / Cr / Ni equivalent proxies) with zero external
featurization dependencies.

All physical constants follow standard CRC Handbook / NIST reference values.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

_ELEMENT_TOKEN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")

# Elemental physical properties:
#   (atomic_number, atomic_mass_u, covalent_radius_pm, pauling_en,
#    valence_electrons, melting_point_k, mendeleev_number)
ELEMENT_PROPERTIES: dict[str, tuple[float, float, float, float, float, float, float]] = {
    "B":  (5.0,  10.811,  84.0,  2.04, 3.0,  2349.0, 72.0),
    "C":  (6.0,  12.011,  76.0,  2.55, 4.0,  3823.0, 77.0),
    "N":  (7.0,  14.007,  71.0,  3.04, 5.0,    63.1, 82.0),
    "O":  (8.0,  15.999,  66.0,  3.44, 6.0,    54.4, 87.0),
    "Al": (13.0, 26.982, 121.0,  1.61, 3.0,   933.5, 73.0),
    "Si": (14.0, 28.086, 111.0,  1.90, 4.0,  1687.0, 78.0),
    "P":  (15.0, 30.974, 107.0,  2.19, 5.0,   317.3, 83.0),
    "S":  (16.0, 32.065, 105.0,  2.58, 6.0,   388.4, 88.0),
    "Ti": (22.0, 47.867, 160.0,  1.54, 4.0,  1941.0, 43.0),
    "V":  (23.0, 50.942, 153.0,  1.63, 5.0,  2183.0, 46.0),
    "Cr": (24.0, 51.996, 139.0,  1.66, 6.0,  2180.0, 49.0),
    "Mn": (25.0, 54.938, 139.0,  1.55, 7.0,  1519.0, 52.0),
    "Fe": (26.0, 55.845, 132.0,  1.83, 8.0,  1811.0, 55.0),
    "Co": (27.0, 58.933, 126.0,  1.88, 9.0,  1768.0, 58.0),
    "Ni": (28.0, 58.693, 124.0,  1.91, 10.0, 1728.0, 61.0),
    "Cu": (29.0, 63.546, 132.0,  1.90, 11.0, 1357.8, 64.0),
    "Zr": (40.0, 91.224, 175.0,  1.33, 4.0,  2128.0, 44.0),
    "Nb": (41.0, 92.906, 164.0,  1.60, 5.0,  2750.0, 47.0),
    "Mo": (42.0, 95.950, 154.0,  2.16, 6.0,  2896.0, 50.0),
    "Ta": (73.0, 180.948, 170.0, 1.50, 5.0,  3290.0, 48.0),
    "W":  (74.0, 183.840, 162.0, 2.36, 6.0,  3695.0, 51.0),
}

PROPERTY_NAMES: tuple[str, ...] = (
    "atomic_number",
    "atomic_mass",
    "covalent_radius",
    "electronegativity",
    "valence_electrons",
    "melting_point",
    "mendeleev_number",
)

METALLURGICAL_INDEX_NAMES: tuple[str, ...] = (
    "atomic_size_mismatch_delta",
    "electronegativity_mismatch",
    "mixing_entropy_over_r",
    "n_elements",
    "non_fe_solute_fraction",
    "interstitial_fraction",
    "carbon_equivalent_proxy",
    "cr_equivalent_proxy",
    "ni_equivalent_proxy",
    "precipitate_former_fraction",
    "refractory_fraction",
)


def parse_composition(formula: str) -> dict[str, float]:
    """Return element -> atomic fraction for one composition string."""
    amounts: dict[str, float] = {}
    for symbol, count in _ELEMENT_TOKEN.findall(formula):
        amount = float(count) if count else 1.0
        amounts[symbol] = amounts.get(symbol, 0.0) + amount
    total = sum(amounts.values())
    if total <= 0.0:
        raise ValueError(f"Composition has no parseable elements: {formula!r}")
    return {symbol: amount / total for symbol, amount in amounts.items()}


def metallurgical_features(
    compositions: Sequence[str], vocabulary: Sequence[str]
) -> np.ndarray:
    """Encode atomic fractions plus composition-weighted metallurgical features.

    Only elements present in ``vocabulary`` (fitted on training formulas) are
    used, guaranteeing zero test-split leakage into the feature space.
    """
    vocab_index = {element: idx for idx, element in enumerate(vocabulary)}
    n_vocab = len(vocabulary)
    n_props = len(PROPERTY_NAMES)
    # 4 stats per property: weighted mean, weighted std, min, max
    n_stat_cols = n_props * 4
    n_meta_cols = len(METALLURGICAL_INDEX_NAMES)
    total_cols = n_vocab + n_stat_cols + n_meta_cols

    matrix = np.zeros((len(compositions), total_cols), dtype=float)

    for row_idx, formula in enumerate(compositions):
        parsed = parse_composition(formula)
        # Keep only elements seen in the training vocabulary
        filtered = {el: frac for el, frac in parsed.items() if el in vocab_index}
        if not filtered:
            continue

        # 1. Raw atomic fractions over training vocabulary
        for el, frac in filtered.items():
            matrix[row_idx, vocab_index[el]] = frac

        # Renormalize known-property weights strictly over filtered elements
        known = [(el, frac, ELEMENT_PROPERTIES[el]) for el, frac in filtered.items() if el in ELEMENT_PROPERTIES]
        if not known:
            continue
        w_sum = sum(frac for _, frac, _ in known)
        weights = np.array([frac / w_sum for _, frac, _ in known], dtype=float)
        prop_table = np.array([props for _, _, props in known], dtype=float)  # (k, n_props)

        # 2. Composition-weighted mean, std, min, max for each elemental property
        col = n_vocab
        means = np.dot(weights, prop_table)  # (n_props,)
        for p_idx in range(n_props):
            vals = prop_table[:, p_idx]
            mean_val = float(means[p_idx])
            std_val = float(np.sqrt(np.sum(weights * (vals - mean_val) ** 2)))
            matrix[row_idx, col] = mean_val
            matrix[row_idx, col + 1] = std_val
            matrix[row_idx, col + 2] = float(vals.min())
            matrix[row_idx, col + 3] = float(vals.max())
            col += 4

        # 3. Physical metallurgy & solid-solution indices
        radii = prop_table[:, 2]
        r_bar = float(means[2])
        delta = float(np.sqrt(np.sum(weights * (1.0 - radii / r_bar) ** 2))) if r_bar > 0 else 0.0

        en_vals = prop_table[:, 3]
        en_bar = float(means[3])
        delta_en = float(np.sqrt(np.sum(weights * (en_vals - en_bar) ** 2)))

        mixing_entropy = float(-sum(w * math.log(w) for w in weights if w > 0.0))
        n_elements = float(len(filtered))

        c_fe = filtered.get("Fe", 0.0)
        c_c = filtered.get("C", 0.0)
        c_n = filtered.get("N", 0.0)
        c_b = filtered.get("B", 0.0)
        c_mn = filtered.get("Mn", 0.0)
        c_cr = filtered.get("Cr", 0.0)
        c_mo = filtered.get("Mo", 0.0)
        c_v = filtered.get("V", 0.0)
        c_ni = filtered.get("Ni", 0.0)
        c_cu = filtered.get("Cu", 0.0)
        c_si = filtered.get("Si", 0.0)
        c_nb = filtered.get("Nb", 0.0)
        c_ti = filtered.get("Ti", 0.0)
        c_al = filtered.get("Al", 0.0)
        c_co = filtered.get("Co", 0.0)
        c_w = filtered.get("W", 0.0)

        # Atomic-fraction proxies for classic steelmaking equivalents
        c_eq = c_c + c_mn / 6.0 + (c_cr + c_mo + c_v) / 5.0 + (c_ni + c_cu) / 15.0
        cr_eq = c_cr + c_mo + 1.5 * c_si + 0.5 * c_nb + 2.0 * c_ti
        ni_eq = c_ni + 30.0 * (c_c + c_n) + 0.5 * c_mn + 0.5 * c_co
        precip_formers = c_ti + c_al + c_nb + c_v + c_mo
        refractories = c_mo + c_w + c_nb + c_v

        meta_values = (
            delta,
            delta_en,
            mixing_entropy,
            n_elements,
            1.0 - c_fe,
            c_c + c_n + c_b,
            c_eq,
            cr_eq,
            ni_eq,
            precip_formers,
            refractories,
        )
        for offset, val in enumerate(meta_values):
            matrix[row_idx, col + offset] = val

    return matrix


class MetallurgicalDescriptorVectorizer(BaseEstimator, TransformerMixin):
    """Fit an element vocabulary on training formulas and emit physics descriptors.

    Cloning inside scikit-learn CV ensures each inner and outer split builds
    its vocabulary strictly from its own training formulas.
    """

    def fit(self, X, y=None) -> "MetallurgicalDescriptorVectorizer":
        vocab: set[str] = set()
        for formula in list(X):
            vocab.update(parse_composition(formula))
        self.vocabulary_ = sorted(vocab)
        return self

    def transform(self, X) -> np.ndarray:
        return metallurgical_features(list(X), self.vocabulary_)
