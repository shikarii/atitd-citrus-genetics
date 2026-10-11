"""Numerical equivalence tests for native C++ acceleration.

Verifies that the C++ implementations produce results within tolerance
of the pure Python implementations for all core functions.
"""

from __future__ import annotations

import numpy as np
import pytest

from citrus_genetics.core._native import is_native_available

pytestmark = pytest.mark.skipif(
    not is_native_available(),
    reason="Native extension not built",
)


# Force Python path for comparison
def _python_trait_rows(rule, a, b, kern, rround, *, need_both=False):
    """Pure Python trait_rows (bypass native dispatch)."""
    from citrus_genetics.core.model import V, display

    offs, kp = kern
    pairs = [(a[0], a[1]), (b[0], b[1]), (a[0], b[1]), (b[0], a[1])]
    rows = {k: np.zeros(V, dtype=np.float64) for k in ("none", "s1", "s2")}
    if need_both:
        rows["both"] = np.zeros(V, dtype=np.float64)
    for g1, g2 in pairs:
        rows["none"][display(rule, np.array(g1), np.array(g2), rround)] += 0.25
        n1 = np.clip(g1 + offs, 0, 1000)
        np.add.at(rows["s1"], display(rule, n1, np.full_like(n1, g2), rround), 0.25 * kp)
        n2 = np.clip(g2 + offs, 0, 1000)
        np.add.at(rows["s2"], display(rule, np.full_like(n2, g1), n2, rround), 0.25 * kp)
        if need_both:
            d = display(rule, n1[:, None], n2[None, :], rround)
            rows["both"] += 0.25 * np.bincount(d.ravel(), weights=np.outer(kp, kp).ravel(), minlength=V)
    return rows


class TestTraitRowsEquivalence:
    """Verify C++ trait_rows matches Python within tolerance."""

    @pytest.fixture()
    def kern(self):
        from citrus_genetics.core.model import kernel
        return kernel("uniform", 150)

    @pytest.mark.parametrize("rule", ["mean", "min", "max", "g1"])
    @pytest.mark.parametrize("rround", ["halfup", "floor"])
    def test_trait_rows_basic(self, kern, rule, rround):
        from citrus_genetics.core._native import native_trait_rows

        a = (400, 600)
        b = (350, 550)
        offs, kp = kern

        native = native_trait_rows(rule, a, b, offs, kp, rround, False)
        python = _python_trait_rows(rule, a, b, kern, rround, need_both=False)

        for key in ("none", "s1", "s2"):
            np.testing.assert_allclose(
                native[key], python[key],
                atol=1e-14, rtol=0,
                err_msg=f"trait_rows[{key}] mismatch for rule={rule}, rround={rround}",
            )

    def test_trait_rows_with_both(self, kern):
        from citrus_genetics.core._native import native_trait_rows

        a = (400, 600)
        b = (350, 550)
        offs, kp = kern

        native = native_trait_rows("mean", a, b, offs, kp, "halfup", True)
        python = _python_trait_rows("mean", a, b, kern, "halfup", need_both=True)

        for key in ("none", "s1", "s2", "both"):
            np.testing.assert_allclose(
                native[key], python[key],
                atol=1e-14, rtol=0,
                err_msg=f"trait_rows[{key}] mismatch (need_both=True)",
            )

    @pytest.mark.parametrize("a,b", [
        ((0, 0), (0, 0)),
        ((1000, 1000), (1000, 1000)),
        ((0, 1000), (500, 500)),
        ((123, 877), (456, 544)),
    ])
    def test_trait_rows_boundary(self, kern, a, b):
        from citrus_genetics.core._native import native_trait_rows

        offs, kp = kern
        native = native_trait_rows("mean", a, b, offs, kp, "halfup", False)
        python = _python_trait_rows("mean", a, b, kern, "halfup", need_both=False)

        for key in ("none", "s1", "s2"):
            np.testing.assert_allclose(
                native[key], python[key],
                atol=1e-14, rtol=0,
                err_msg=f"boundary test a={a} b={b} key={key}",
            )

    def test_trait_rows_probability_sums(self, kern):
        """Verify probability vectors sum to ~1.0."""
        from citrus_genetics.core._native import native_trait_rows

        offs, kp = kern
        result = native_trait_rows("mean", (400, 600), (350, 550), offs, kp, "halfup", False)

        for key in ("none", "s1", "s2"):
            total = np.sum(result[key])
            assert abs(total - 1.0) < 1e-10, f"{key} probabilities sum to {total}, expected ~1.0"

    def test_determinism(self, kern):
        """Repeated calls produce identical results."""
        from citrus_genetics.core._native import native_trait_rows

        offs, kp = kern
        a, b = (400, 600), (350, 550)

        r1 = native_trait_rows("mean", a, b, offs, kp, "halfup", False)
        r2 = native_trait_rows("mean", a, b, offs, kp, "halfup", False)

        for key in ("none", "s1", "s2"):
            np.testing.assert_array_equal(r1[key], r2[key])
