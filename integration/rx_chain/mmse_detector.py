"""Experimental linear MMSE detector reference for 2x2 MIMO."""

import numpy as np
from numpy.typing import NDArray


def detect_mmse_symbols(
    received_grid: NDArray[np.complexfloating],
    channel_estimates: NDArray[np.complexfloating],
    data_bins: NDArray[np.integer],
    noise_variance: float,
    first_data_symbol: int = 2,
    symbol_energy: float = 1.0,
) -> NDArray[np.complex128]:
    """Detect two spatial streams using a linear MMSE detector.

    The received frequency-domain noise variance is assumed to be
    ``fft_size * noise_variance``. This follows the project's unnormalised
    forward FFT convention when ``noise_variance`` is the time-domain
    complex AWGN variance.

    Args:
        received_grid: Array shaped (2, fft_size, num_ofdm_symbols).
        channel_estimates: Array shaped (2, 2, num_data_bins).
        data_bins: Integer indices of the data subcarriers.
        noise_variance: Time-domain complex AWGN variance; must be finite
            and non-negative.
        first_data_symbol: First OFDM symbol containing data.
        symbol_energy: Average transmitted symbol energy; must be positive.

    Returns:
        Detected symbols shaped (2, num_data_symbols, num_data_bins).

    Raises:
        ValueError: If an input has an invalid shape or value.
        numpy.linalg.LinAlgError: If a detector solve fails.
        FloatingPointError: If detection produces non-finite values.
    """
    grid = np.asarray(received_grid, dtype=np.complex128)
    channels = np.asarray(channel_estimates, dtype=np.complex128)
    bins_input = np.asarray(data_bins)

    if grid.ndim != 3 or grid.shape[0] != 2:
        raise ValueError(
            "received_grid must have shape (2, fft_size, num_ofdm_symbols)"
        )

    if not np.all(np.isfinite(grid)):
        raise ValueError("received_grid must contain only finite values")

    if channels.ndim != 3 or channels.shape[:2] != (2, 2):
        raise ValueError(
            "channel_estimates must have shape (2, 2, num_data_bins)"
        )

    if not np.all(np.isfinite(channels)):
        raise ValueError("channel_estimates must contain only finite values")

    if bins_input.ndim != 1 or not np.issubdtype(
        bins_input.dtype, np.integer
    ):
        raise ValueError("data_bins must be a one-dimensional integer array")

    bins = bins_input.astype(np.int64, copy=False)

    if bins.size == 0:
        raise ValueError("data_bins must not be empty")

    if channels.shape[2] != bins.size:
        raise ValueError(
            "channel_estimates third dimension must match data_bins length"
        )

    if np.any(bins < 0) or np.any(bins >= grid.shape[1]):
        raise ValueError("data_bins contains an out-of-range subcarrier index")

    if np.unique(bins).size != bins.size:
        raise ValueError("data_bins must not contain duplicate indices")

    if (
        isinstance(first_data_symbol, (bool, np.bool_))
        or not isinstance(first_data_symbol, (int, np.integer))
        or first_data_symbol < 0
        or first_data_symbol >= grid.shape[2]
    ):
        raise ValueError("first_data_symbol must identify a valid OFDM symbol")

    try:
        variance = float(noise_variance)
        energy = float(symbol_energy)
    except (TypeError, ValueError) as exc:
        raise ValueError("noise_variance and symbol_energy must be numeric") from exc

    if not np.isfinite(variance) or variance < 0.0:
        raise ValueError("noise_variance must be finite and non-negative")

    if not np.isfinite(energy) or energy <= 0.0:
        raise ValueError("symbol_energy must be finite and positive")

    frequency_noise_variance = grid.shape[1] * variance
    regularization = frequency_noise_variance / energy

    num_data_symbols = grid.shape[2] - first_data_symbol
    detected = np.empty(
        (2, num_data_symbols, bins.size), dtype=np.complex128
    )
    identity = np.eye(2, dtype=np.complex128)

    for symbol_offset, symbol_index in enumerate(
        range(first_data_symbol, grid.shape[2])
    ):
        for bin_index, subcarrier in enumerate(bins):
            channel = channels[:, :, bin_index]
            received = grid[:, subcarrier, symbol_index]

            try:
                if regularization == 0.0:
                    # At zero noise, MMSE reduces exactly to ZF.
                    estimate = np.linalg.solve(channel, received)
                else:
                    gram = channel.conj().T @ channel
                    rhs = channel.conj().T @ received
                    estimate = np.linalg.solve(
                        gram + regularization * identity, rhs
                    )
            except np.linalg.LinAlgError:
                raise

            if not np.all(np.isfinite(estimate)):
                raise FloatingPointError(
                    "MMSE detection produced non-finite output"
                )

            detected[:, symbol_offset, bin_index] = estimate

    return detected
