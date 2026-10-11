"""Native acceleration dispatch.

Attempts to import the C++/CUDA extension. Falls back to pure Python
implementations from model.py if the extension is not available.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_NATIVE_AVAILABLE = False
_CUDA_AVAILABLE = False
_HAS_AVX2 = False

try:
    from citrus_genetics.core._citrus_native import (  # type: ignore[import-not-found]
        child_lik as native_child_lik,
        has_avx2 as _has_avx2,
        has_cuda as _has_cuda,
        cuda_device_name as _cuda_device_name,
        loglik as native_loglik,
        scan_parent as native_scan_parent,
        trait_rows as native_trait_rows,
    )

    _NATIVE_AVAILABLE = True
    _HAS_AVX2 = _has_avx2()
    _CUDA_AVAILABLE = _has_cuda()

    features = []
    if _HAS_AVX2:
        features.append("AVX2")
    if _CUDA_AVAILABLE:
        features.append(f"CUDA ({_cuda_device_name()})")
    if not features:
        features.append("scalar")

    logger.info("Native acceleration: C++ (%s)", " + ".join(features))

except ImportError:
    logger.info("Native acceleration: not available, using pure Python")

    # Define stubs so imports don't fail
    def native_trait_rows(*args, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001, ANN002, ANN003
        raise NotImplementedError

    def native_child_lik(*args, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001, ANN002, ANN003
        raise NotImplementedError

    def native_loglik(*args, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001, ANN002, ANN003
        raise NotImplementedError

    def native_scan_parent(*args, **kwargs):  # type: ignore[no-untyped-def]  # noqa: ARG001, ANN002, ANN003
        raise NotImplementedError


def is_native_available() -> bool:
    """Check if native C++ acceleration is available."""
    return _NATIVE_AVAILABLE


def is_cuda_available() -> bool:
    """Check if CUDA GPU acceleration is available."""
    return _CUDA_AVAILABLE


def has_avx2() -> bool:
    """Check if AVX2 SIMD is available."""
    return _HAS_AVX2
