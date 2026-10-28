"""Resource-grid construction for the simplified 2x2 MIMO PHY."""

import numpy as np


def build_mimo_resource_grid(
    data_symbols: list[list[complex]] | np.ndarray,
    fft_size: int = 64,
    num_ofdm_symbols: int = 3,
    pilot_value: complex = 1.0 + 0.0j,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build a resource grid with orthogonal pilots and independent data streams.

    Args:
        data_symbols: Two data streams, one per transmit antenna.
        fft_size: Number of FFT bins.
        num_ofdm_symbols: Total OFDM symbols, including two pilot symbols.
        pilot_value: Nonzero pilot symbol.

    Returns:
        resource_grid: Array shaped (2, fft_size, num_ofdm_symbols).
        pilot_bins: FFT-bin indices reserved for pilots.
        data_bins: FFT-bin indices reserved for data.
    """
    if (
        not isinstance(fft_size, int)
        or isinstance(fft_size, bool)
        or fft_size < 4
    ):
        raise ValueError("fft_size must be an integer >= 4")

    if (
        not isinstance(num_ofdm_symbols, int)
        or isinstance(num_ofdm_symbols, bool)
        or num_ofdm_symbols < 3
    ):
        raise ValueError("num_ofdm_symbols must be an integer >= 3")

    if not np.isscalar(pilot_value) or not np.isfinite(pilot_value):
        raise ValueError("pilot_value must be a finite scalar")

    if pilot_value == 0:
        raise ValueError("pilot_value must be nonzero")

    streams = np.asarray(data_symbols, dtype=np.complex128)

    if streams.ndim != 2 or streams.shape[0] != 2:
        raise ValueError(
            "data_symbols must contain two one-dimensional streams"
        )

    if not np.all(np.isfinite(streams)):
        raise ValueError("data_symbols must contain only finite values")

    # Odd bins carry pilots; even bins carry data. Bin 0 is unused.
    pilot_bins = np.arange(1, fft_size, 2, dtype=np.int64)
    data_bins = np.arange(2, fft_size, 2, dtype=np.int64)

    data_symbols_per_antenna = data_bins.size * (num_ofdm_symbols - 2)

    if streams.shape[1] > data_symbols_per_antenna:
        raise ValueError(
            f"Each stream can contain at most {data_symbols_per_antenna} "
            f"symbols, but received {streams.shape[1]}"
        )

    grid = np.zeros(
        (2, fft_size, num_ofdm_symbols),
        dtype=np.complex128,
    )

    # Orthogonal pilot transmissions let the receiver estimate each TX-to-RX link.
    grid[0, pilot_bins, 0] = pilot_value
    grid[1, pilot_bins, 1] = pilot_value

    # Fill data positions independently for each transmit antenna.
    for antenna in range(2):
        stream = streams[antenna]
        capacity = data_symbols_per_antenna

        data_matrix = np.zeros(capacity, dtype=np.complex128)
        data_matrix[:stream.size] = stream

        grid[antenna, data_bins, 2:] = data_matrix.reshape(
            num_ofdm_symbols - 2,
            data_bins.size,
        ).T

    return grid, pilot_bins, data_bins
