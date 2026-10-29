"""Experimental delay-domain least-squares channel estimation.

This module is isolated from the production receiver and Kernel 5.
It assumes a discrete, integer-delay channel model with known pilot
symbols and a configurable maximum delay.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


ComplexVector = Sequence[complex] | npt.NDArray[np.complexfloating]
IndexVector = Sequence[int] | npt.NDArray[np.integer]


@dataclass(frozen=True)
class DelayDomainDiagnostics:
    """Numerical diagnostics for a delay-domain channel estimate.

    Attributes:
        frequency_response: Estimated channel response at requested FFT bins.
        channel_taps: Estimated channel taps for delays 0 through max_delay_samples.
        residual_norm: Euclidean norm of the least-squares residual vector.
        condition_number: Two-norm condition number of the design matrix.
    """

    frequency_response: npt.NDArray[np.complex128]
    channel_taps: npt.NDArray[np.complex128]
    residual_norm: float
    condition_number: float


def _as_complex_vector(
    values: object,
    name: str,
) -> npt.NDArray[np.complex128]:
    """Convert a one-dimensional numeric sequence to finite complex128 values."""
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be a one-dimensional numeric sequence"
        ) from exc

    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")

    if array.dtype.kind not in "iufc":
        raise ValueError(f"{name} must contain numeric values")

    result = np.asarray(array, dtype=np.complex128)

    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite values")

    return result


def _as_index_vector(
    values: object,
    name: str,
) -> npt.NDArray[np.int64]:
    """Validate and convert a one-dimensional integer index sequence."""
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be a one-dimensional integer sequence"
        ) from exc

    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")

    # Empty Python lists default to float dtype in NumPy.
    if array.size == 0:
        return np.asarray([], dtype=np.int64)

    if array.dtype.kind not in "iu":
        raise TypeError(
            f"{name} must contain integers (booleans are not accepted)"
        )

    if array.dtype.kind == "u" and np.any(array > np.iinfo(np.int64).max):
        raise ValueError(f"{name} contains an index outside the supported range")

    return np.asarray(array, dtype=np.int64)


def _as_positive_integer(value: object, name: str) -> int:
    """Validate a positive integer scalar, excluding booleans."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")

    result = int(value)

    if result <= 0:
        raise ValueError(f"{name} must be positive")

    return result


def _as_nonnegative_integer(value: object, name: str) -> int:
    """Validate a nonnegative integer scalar, excluding booleans."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise TypeError(f"{name} must be an integer")

    result = int(value)

    if result < 0:
        raise ValueError(f"{name} must be nonnegative")

    return result


def _estimate(
    pilot_symbols: ComplexVector,
    received_pilots: ComplexVector,
    pilot_indices: IndexVector,
    estimate_indices: IndexVector,
    fft_size: int,
    max_delay_samples: int,
) -> DelayDomainDiagnostics:
    """Validate inputs, solve the LS problem, and compute diagnostics."""
    pilots = _as_complex_vector(pilot_symbols, "pilot_symbols")
    received = _as_complex_vector(received_pilots, "received_pilots")
    pilot_k = _as_index_vector(pilot_indices, "pilot_indices")
    estimate_k = _as_index_vector(estimate_indices, "estimate_indices")

    n_fft = _as_positive_integer(fft_size, "fft_size")
    max_delay = _as_nonnegative_integer(
        max_delay_samples, "max_delay_samples"
    )

    if max_delay >= n_fft:
        raise ValueError("max_delay_samples must be smaller than fft_size")

    if pilots.size == 0:
        raise ValueError("At least one pilot is required")

    if not (pilots.size == received.size == pilot_k.size):
        raise ValueError(
            "pilot_symbols, received_pilots, and pilot_indices "
            "must have equal lengths"
        )

    if np.any(pilots == 0):
        raise ValueError("Pilot symbols must be nonzero")

    if np.unique(pilot_k).size != pilot_k.size:
        raise ValueError("pilot_indices must be unique")

    if np.any(pilot_k < 0) or np.any(pilot_k >= n_fft):
        raise ValueError("pilot_indices must be within [0, fft_size)")

    if np.any(estimate_k < 0) or np.any(estimate_k >= n_fft):
        raise ValueError("estimate_indices must be within [0, fft_size)")

    if estimate_k.size == 0:
        return DelayDomainDiagnostics(
            frequency_response=np.empty(0, dtype=np.complex128),
            channel_taps=np.empty(0, dtype=np.complex128),
            residual_norm=float("nan"),
            condition_number=float("nan"),
        )


    tap_count = max_delay + 1

    if pilot_k.size < tap_count:
        raise ValueError(
            "The pilot observations are insufficient for the requested "
            "delay model"
        )

    # Remove known pilot modulation to obtain noisy channel observations.
    observed_response = received / pilots

    # A[p, ell] = exp(-j * 2*pi * pilot_k[p] * ell / fft_size).
    delays = np.arange(tap_count, dtype=np.float64)
    design_matrix = np.exp(
        -2j * np.pi * np.outer(pilot_k.astype(np.float64), delays) / n_fft
    ).astype(np.complex128)

    # Reject rank-deficient systems rather than returning an ambiguous solution.
    if np.linalg.matrix_rank(design_matrix) < tap_count:
        raise ValueError("The delay-domain design matrix is rank-deficient")

    channel_taps, _, rank, singular_values = np.linalg.lstsq(
        design_matrix,
        observed_response,
        rcond=None,
    )

    if rank < tap_count:
        raise ValueError("The delay-domain design matrix is rank-deficient")

    if not np.all(np.isfinite(channel_taps)):
        raise ValueError("Least-squares estimation produced nonfinite channel taps")

    residual = design_matrix @ channel_taps - observed_response
    residual_norm = float(np.linalg.norm(residual))

    # A full-rank matrix has a finite condition number in ordinary finite cases.
    condition_number = float(np.linalg.cond(design_matrix))

    if singular_values.size and singular_values[-1] <= 0:
        raise ValueError("The delay-domain design matrix is rank-deficient")

    estimate_delays = np.arange(tap_count, dtype=np.float64)
    estimate_matrix = np.exp(
        -2j
        * np.pi
        * np.outer(estimate_k.astype(np.float64), estimate_delays)
        / n_fft
    )

    frequency_response = np.asarray(
        estimate_matrix @ channel_taps,
        dtype=np.complex128,
    )

    return DelayDomainDiagnostics(
        frequency_response=frequency_response,
        channel_taps=np.asarray(channel_taps, dtype=np.complex128),
        residual_norm=residual_norm,
        condition_number=condition_number,
    )


def estimate_channel_delay_domain(
    pilot_symbols: ComplexVector,
    received_pilots: ComplexVector,
    pilot_indices: IndexVector,
    estimate_indices: IndexVector,
    fft_size: int,
    max_delay_samples: int,
) -> npt.NDArray[np.complex128]:
    """Estimate a frequency-domain channel using delay-domain least squares.

    Args:
        pilot_symbols: Known, nonzero transmitted pilot symbols.
        received_pilots: Received pilot observations, including possible noise.
        pilot_indices: Unique pilot subcarrier indices; order need not be sorted.
        estimate_indices: Requested subcarrier indices, in output order.
        fft_size: Positive FFT size.
        max_delay_samples: Maximum modeled integer delay, inclusive.

    Returns:
        A one-dimensional complex128 channel-response vector in requested order.

    Raises:
        TypeError: If indices or integer scalar parameters have invalid types.
        ValueError: If inputs are invalid or the delay model is rank-deficient.
    """
    return _estimate(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples,
    ).frequency_response


def estimate_channel_delay_domain_diagnostics(
    pilot_symbols: ComplexVector,
    received_pilots: ComplexVector,
    pilot_indices: IndexVector,
    estimate_indices: IndexVector,
    fft_size: int,
    max_delay_samples: int,
) -> DelayDomainDiagnostics:
    """Return the estimate together with taps and least-squares diagnostics.

    The residual norm is ||A h_hat - z||_2, where z is the received pilot
    vector divided by the known pilot symbols. The condition number is the
    two-norm condition number of the pilot design matrix.
    """
    return _estimate(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples,
    )
