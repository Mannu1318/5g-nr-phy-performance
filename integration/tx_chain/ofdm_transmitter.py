
"""OFDM modulation for the simplified 2x2 MIMO transmitter."""

import numpy as np

from kernels.kernel4_ofdm.ofdm_reference import (
    ifft,
    add_cyclic_prefix,
)


def modulate_resource_grid(
    resource_grid: np.ndarray,
    cp_length: int = 16,
) -> np.ndarray:
    """Convert a MIMO frequency-domain resource grid to time-domain waveforms.

    Args:
        resource_grid: Complex array shaped (2, fft_size, num_ofdm_symbols).
        cp_length: Number of cyclic-prefix samples per OFDM symbol.

    Returns:
        Complex array shaped (2, num_ofdm_symbols * (fft_size + cp_length)).
        Each row contains one transmit antenna's concatenated OFDM waveform.
    """
    grid = np.asarray(resource_grid, dtype=np.complex128)

    if grid.ndim != 3 or grid.shape[0] != 2:
        raise ValueError(
            "resource_grid must have shape (2, fft_size, num_ofdm_symbols)"
        )

    if grid.shape[1] == 0 or grid.shape[2] == 0:
        raise ValueError("Resource grid must not have empty dimensions")

    if not np.all(np.isfinite(grid)):
        raise ValueError("Resource grid must contain only finite values")

    if (
        not isinstance(cp_length, (int, np.integer))
        or isinstance(cp_length, (bool, np.bool_))
        or cp_length < 0
        or cp_length > grid.shape[1]
    ):
        raise ValueError("cp_length must be between 0 and fft_size")

    num_antennas, fft_size, num_symbols = grid.shape
    symbol_length = fft_size + cp_length

    waveforms = np.empty(
        (num_antennas, num_symbols * symbol_length),
        dtype=np.complex128,
    )

    for antenna in range(num_antennas):
        ofdm_symbols = []

        for symbol_index in range(num_symbols):
            time_samples = ifft(grid[antenna, :, symbol_index])
            with_cp = add_cyclic_prefix(time_samples, cp_length)
            ofdm_symbols.append(with_cp)

        waveforms[antenna] = np.concatenate(ofdm_symbols)

    return waveforms
