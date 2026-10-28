
"""Pilot-based channel estimation for the simplified 2x2 MIMO receiver."""

import numpy as np

from kernels.kernel5_channel_estimation.channel_estimation_reference import (
    estimate_channel,
)


def estimate_mimo_channel(
    received_grid: np.ndarray,
    pilot_bins: np.ndarray,
    data_bins: np.ndarray,
    pilot_value: complex = 1.0 + 0.0j,
) -> np.ndarray:
    """Estimate all four TX-to-RX channels at data subcarrier positions.

    The transmitter sends orthogonal pilots:
      - TX antenna 0 sends pilots in OFDM symbol 0.
      - TX antenna 1 sends pilots in OFDM symbol 1.

    Assumes the channel is constant across the two pilot symbols.

    Args:
        received_grid: Array shaped (2, fft_size, num_ofdm_symbols).
        pilot_bins: Increasing FFT-bin indices used for pilots.
        data_bins: FFT-bin indices where channel estimates are needed.
        pilot_value: Known, nonzero transmitted pilot value.

    Returns:
        Complex array shaped (2, 2, len(data_bins)).
        Axes are [receive antenna, transmit antenna, data-bin index].
    """
    grid = np.asarray(received_grid, dtype=np.complex128)
    pilots = np.asarray(pilot_bins)
    data = np.asarray(data_bins)

    if grid.ndim != 3 or grid.shape[0] != 2 or grid.shape[1] == 0:
        raise ValueError(
            "received_grid must have shape (2, fft_size, num_ofdm_symbols)"
        )

    if grid.shape[2] < 2:
        raise ValueError("received_grid must contain at least two pilot symbols")

    if not np.all(np.isfinite(grid)):
        raise ValueError("received_grid must contain only finite values")

    if (
        not isinstance(pilot_value, (int, float, complex, np.number))
        or not np.isfinite(pilot_value)
        or pilot_value == 0
    ):
        raise ValueError("pilot_value must be finite and nonzero")

    for indices, name in ((pilots, "pilot_bins"), (data, "data_bins")):
        if indices.ndim != 1 or indices.size == 0:
            raise ValueError(f"{name} must be a non-empty one-dimensional array")
        if indices.dtype.kind not in "iu":
            raise ValueError(f"{name} must contain integer indices")
        if np.any(indices < 0) or np.any(indices >= grid.shape[1]):
            raise ValueError(f"{name} contains indices outside the FFT grid")

    if pilots.size > 1 and np.any(np.diff(pilots) <= 0):
        raise ValueError("pilot_bins must be strictly increasing and unique")

    if np.unique(data).size != data.size:
        raise ValueError("data_bins must not contain duplicate indices")

    if np.any(data < pilots[0]) or np.any(data > pilots[-1]):
        raise ValueError("data_bins must lie within the pilot-bin range")

    estimates = np.empty((2, 2, data.size), dtype=np.complex128)

    for rx_antenna in range(2):
        for tx_antenna in range(2):
            pilot_symbol_index = tx_antenna

            received_pilots = grid[
                rx_antenna, pilots, pilot_symbol_index
            ]

            estimates[rx_antenna, tx_antenna] = estimate_channel(
                pilot_symbols=np.full(
                    pilots.size, pilot_value, dtype=np.complex128
                ),
                received_pilots=received_pilots,
                pilot_indices=pilots,
                estimate_indices=data,
            )

    return estimates
