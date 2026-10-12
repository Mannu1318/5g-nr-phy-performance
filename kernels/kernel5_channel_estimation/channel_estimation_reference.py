"""Python reference for LS channel estimation with linear interpolation."""

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt


def estimate_channel(
    pilot_symbols: Sequence[complex] | npt.NDArray[np.complexfloating],
    received_pilots: Sequence[complex] | npt.NDArray[np.complexfloating],
    pilot_indices: Sequence[int] | npt.NDArray[np.integer],
    estimate_indices: Sequence[int] | npt.NDArray[np.integer],
) -> npt.NDArray[np.complex128]:
    """Estimate a frequency-domain channel from known pilot observations.

    Args:
        pilot_symbols: Known, nonzero transmitted pilot symbols.
        received_pilots: Received pilot observations, including any noise.
        pilot_indices: Strictly increasing pilot subcarrier indices.
        estimate_indices: Requested subcarrier indices, in output order.

    Returns:
        A one-dimensional complex128 array containing the channel estimates.

    Raises:
        ValueError: If array dimensions, lengths, values, or indices are invalid.
        TypeError: If an index array contains non-integer values.
    """

    def as_complex_vector(values: object, name: str) -> npt.NDArray[np.complex128]:
        try:
            array = np.asarray(values)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a one-dimensional numeric sequence") from exc

        if array.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")

        if array.dtype.kind not in "iufc":
            raise ValueError(f"{name} must contain numeric values")

        result = np.asarray(array, dtype=np.complex128)

        if not np.all(np.isfinite(result)):
            raise ValueError(f"{name} must contain only finite values")

        return result

    def as_index_vector(values: object, name: str) -> npt.NDArray[np.int64]:
        try:
            array = np.asarray(values)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a one-dimensional integer sequence") from exc

        if array.ndim != 1:
            raise ValueError(f"{name} must be one-dimensional")

        # NumPy gives an empty Python list a float dtype; accept it as an
        # empty integer index vector so the function can validate it properly.
        if array.size == 0:
            return np.asarray([], dtype=np.int64)

        if array.dtype.kind not in "iu":
            raise TypeError(f"{name} must contain integers (booleans are not accepted)")

        if array.dtype.kind == "u" and array.size:
            if np.any(array > np.iinfo(np.int64).max):
                raise ValueError(f"{name} contains an index outside the supported range")

        return np.asarray(array, dtype=np.int64)

    pilots = as_complex_vector(pilot_symbols, "pilot_symbols")
    received = as_complex_vector(received_pilots, "received_pilots")
    pilot_k = as_index_vector(pilot_indices, "pilot_indices")
    estimate_k = as_index_vector(estimate_indices, "estimate_indices")

    if pilots.size == 0:
        raise ValueError("At least one pilot is required")

    if not (pilots.size == received.size == pilot_k.size):
        raise ValueError(
            "pilot_symbols, received_pilots, and pilot_indices must have equal lengths"
        )

    if np.any(pilots == 0):
        raise ValueError("Pilot symbols must be nonzero")

    if np.any(pilot_k < 0) or np.any(estimate_k < 0):
        raise ValueError("Subcarrier indices must be nonnegative")

    if pilot_k.size > 1 and np.any(np.diff(pilot_k) <= 0):
        raise ValueError("pilot_indices must be strictly increasing and unique")

    if estimate_k.size == 0:
        return np.empty(0, dtype=np.complex128)

    # A single pilot supports an estimate only at its own position.
    if pilot_k.size == 1 and np.any(estimate_k != pilot_k[0]):
        raise ValueError("A single pilot supports estimates only at its own index")

    if np.any(estimate_k < pilot_k[0]) or np.any(estimate_k > pilot_k[-1]):
        raise ValueError("Requested indices must lie within the pilot range")

    # LS estimates at the known pilot positions.
    pilot_estimates = received / pilots

    if pilot_k.size == 1:
        return np.full(estimate_k.size, pilot_estimates[0], dtype=np.complex128)

    # Linear interpolation is applied independently to the real and imaginary parts.
    real_part = np.interp(estimate_k, pilot_k, pilot_estimates.real)
    imag_part = np.interp(estimate_k, pilot_k, pilot_estimates.imag)

    return np.asarray(real_part + 1j * imag_part, dtype=np.complex128)
