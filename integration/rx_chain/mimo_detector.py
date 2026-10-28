"""MIMO Zero-Forcing detection for the integrated PHY receiver."""

import numpy as np
from numpy.typing import NDArray

from kernels.kernel6_mimo.mimo_zf_reference import (
    OK,
    zf_detect_batch,
)


def detect_mimo_symbols(
    received_grid: NDArray[np.complexfloating],
    channel_estimates: NDArray[np.complexfloating],
    data_bins: NDArray[np.integer],
    first_data_symbol: int = 2,
) -> NDArray[np.complex128]:
    """Detect two transmitted symbol streams using 2x2 MIMO ZF.

    Args:
        received_grid:
            Received frequency-domain grid, shape (2, fft_size, num_symbols).
        channel_estimates:
            Estimated channel matrices, shape (2, 2, len(data_bins)).
            Axes are [receive antenna, transmit antenna, data-bin index].
        data_bins:
            FFT-bin indices carrying data.
        first_data_symbol:
            Index of the first OFDM symbol carrying data.

    Returns:
        Detected symbols with shape (2, num_data_symbols, len(data_bins)).
        The first axis identifies the transmitted stream. Symbol ordering
        matches the resource-grid transmitter.

    Raises:
        ValueError: If inputs are invalid or any ZF detection fails.
    """
    grid = np.asarray(received_grid, dtype=np.complex128)
    estimates = np.asarray(channel_estimates, dtype=np.complex128)
    bins = np.asarray(data_bins)

    if grid.ndim != 3 or grid.shape[0] != 2:
        raise ValueError(
            "received_grid must have shape (2, fft_size, num_symbols)"
        )

    if not np.all(np.isfinite(grid)):
        raise ValueError("received_grid must contain only finite values")

    if (
        estimates.ndim != 3
        or estimates.shape[:2] != (2, 2)
        or estimates.shape[2] != bins.size
    ):
        raise ValueError(
            "channel_estimates must have shape (2, 2, len(data_bins))"
        )

    if not np.all(np.isfinite(estimates)):
        raise ValueError("channel_estimates must contain only finite values")

    if bins.ndim != 1 or bins.size == 0:
        raise ValueError("data_bins must be a non-empty one-dimensional array")

    if bins.dtype.kind not in "iu":
        raise ValueError("data_bins must contain integer indices")

    if np.any(bins < 0) or np.any(bins >= grid.shape[1]):
        raise ValueError("data_bins contains indices outside the FFT grid")

    if (
        not isinstance(first_data_symbol, (int, np.integer))
        or isinstance(first_data_symbol, (bool, np.bool_))
        or first_data_symbol < 0
        or first_data_symbol >= grid.shape[2]
    ):
        raise ValueError("first_data_symbol is outside the OFDM grid")

    if np.unique(bins).size != bins.size:
        raise ValueError("data_bins must not contain duplicate indices")

    num_data_symbols = grid.shape[2] - first_data_symbol
    num_bins = bins.size
    num_pairs = num_data_symbols * num_bins

    # Prepare one 2x2 channel matrix and one received vector per
    # (OFDM data symbol, data subcarrier) pair.
    channels = np.empty((num_pairs, 2, 2), dtype=np.complex128)
    received = np.empty((num_pairs, 2), dtype=np.complex128)

    pair_index = 0
    for symbol_index in range(first_data_symbol, grid.shape[2]):
        for bin_index, fft_bin in enumerate(bins):
            channels[pair_index] = estimates[:, :, bin_index]
            received[pair_index] = grid[:, fft_bin, symbol_index]
            pair_index += 1

    detected, statuses = zf_detect_batch(channels, received)

    if statuses.size != num_pairs or not np.all(statuses == OK):
        failures = (
            statuses[statuses != OK].tolist()
            if statuses.size == num_pairs
            else statuses.tolist()
        )
        raise ValueError(f"MIMO ZF detection failed: {failures}")

    # Batch order is symbol first, then subcarrier. Restore the layout
    # expected by the transmitter: [stream, data symbol, data bin].
    detected = detected.reshape(num_data_symbols, num_bins, 2)

    return np.transpose(detected, (2, 0, 1)).copy()
