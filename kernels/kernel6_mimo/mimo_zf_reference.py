"""Python reference implementation of 2x2 MIMO Zero-Forcing detection."""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import NDArray


# Public status values shared conceptually with the future C implementation.
OK: Final[str] = "OK"
INVALID_SHAPE: Final[str] = "INVALID_SHAPE"
NONFINITE_INPUT: Final[str] = "NONFINITE_INPUT"
SINGULAR_CHANNEL: Final[str] = "SINGULAR_CHANNEL"
NEAR_SINGULAR_CHANNEL: Final[str] = "NEAR_SINGULAR_CHANNEL"
NUMERICAL_FAILURE: Final[str] = "NUMERICAL_FAILURE"

NEAR_SINGULAR_THRESHOLD: Final[float] = 1e-12
STATUS_DTYPE: Final[str] = "<U32"

ComplexArray = NDArray[np.complex128]


def _nan_estimate() -> ComplexArray:
    """Return two complex NaNs for an unsuccessful single-pair operation."""
    return np.full(2, complex(np.nan, np.nan), dtype=np.complex128)


def _detect_one(
    channel: ComplexArray,
    received: ComplexArray,
) -> tuple[ComplexArray, str]:
    """Perform one validated 2x2 ZF detection operation."""

    if not np.all(np.isfinite(channel)) or not np.all(np.isfinite(received)):
        return _nan_estimate(), NONFINITE_INPUT

    # Normalize before evaluating the determinant metric.
    # A complex magnitude can overflow even when both components are finite.
    with np.errstate(over="ignore", invalid="ignore"):
        scale = float(np.max(np.abs(channel)))

    if not np.isfinite(scale):
        return _nan_estimate(), NUMERICAL_FAILURE

    if scale == 0.0:
        return _nan_estimate(), SINGULAR_CHANNEL

    normalized = channel / scale

    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        determinant = np.linalg.det(normalized)
        frobenius_squared = float(np.sum(np.abs(normalized) ** 2))
        rho = float(np.abs(determinant) / frobenius_squared)

    if not np.isfinite(rho):
        return _nan_estimate(), NUMERICAL_FAILURE

    if rho <= NEAR_SINGULAR_THRESHOLD:
        return _nan_estimate(), NEAR_SINGULAR_CHANNEL

    # Solve H*x_hat = y directly; do not explicitly construct H inverse.
    try:
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            estimate = np.linalg.solve(channel, received)
    except np.linalg.LinAlgError:
        return _nan_estimate(), NUMERICAL_FAILURE
    except (ValueError, FloatingPointError):
        return _nan_estimate(), NUMERICAL_FAILURE

    estimate = np.asarray(estimate, dtype=np.complex128)

    if estimate.shape != (2,) or not np.all(np.isfinite(estimate)):
        return _nan_estimate(), NUMERICAL_FAILURE

    return estimate, OK


def zf_detect_single(
    H: NDArray[np.complexfloating] | list,
    y: NDArray[np.complexfloating] | list,
) -> tuple[ComplexArray, str]:
    """Estimate two transmitted symbols from one 2x2 channel matrix.

    Parameters
    ----------
    H:
        Channel matrix with shape (2, 2).
    y:
        Received complex vector with shape (2,).

    Returns
    -------
    x_hat, status:
        A complex128 vector of shape (2) and a status string.
        On failure, x_hat contains complex NaNs.
    """
    try:
        channel = np.asarray(H, dtype=np.complex128)
        received = np.asarray(y, dtype=np.complex128)
    except (TypeError, ValueError, OverflowError):
        return _nan_estimate(), INVALID_SHAPE

    if channel.shape != (2, 2) or received.shape != (2,):
        return _nan_estimate(), INVALID_SHAPE

    return _detect_one(channel, received)


def zf_detect_batch(
    H: NDArray[np.complexfloating] | list,
    y: NDArray[np.complexfloating] | list,
) -> tuple[ComplexArray, NDArray[np.str_]]:
    """Estimate symbol pairs independently using one channel matrix per pair.

    Parameters
    ----------
    H:
        Channel matrices with shape (N, 2, 2).
    y:
        Received vectors with shape (N, 2).

    Returns
    -------
    x_hat, statuses:
        x_hat has shape (N, 2), and statuses has shape (N,).
        Failed pairs contain complex NaNs and their own failure status.

        If the batch-level input shapes are invalid, returns an empty
        estimate array and a one-element status array containing
        INVALID_SHAPE.
    """
    try:
        channels = np.asarray(H, dtype=np.complex128)
        received = np.asarray(y, dtype=np.complex128)
    except (TypeError, ValueError, OverflowError):
        return (
            np.empty((0, 2), dtype=np.complex128),
            np.asarray([INVALID_SHAPE], dtype=STATUS_DTYPE),
        )

    if (
        channels.ndim != 3
        or channels.shape[1:] != (2, 2)
        or received.ndim != 2
        or received.shape[1:] != (2,)
        or channels.shape[0] != received.shape[0]
    ):
        return (
            np.empty((0, 2), dtype=np.complex128),
            np.asarray([INVALID_SHAPE], dtype=STATUS_DTYPE),
        )

    count = channels.shape[0]
    estimates = np.full(
        (count, 2),
        complex(np.nan, np.nan),
        dtype=np.complex128,
    )
    statuses = np.empty(count, dtype=STATUS_DTYPE)

    for index in range(count):
        estimate, status = _detect_one(channels[index], received[index])
        estimates[index] = estimate
        statuses[index] = status

    return estimates, statuses
