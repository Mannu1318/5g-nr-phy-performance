
"""OFDM demodulation for the simplified 2x2 MIMO receiver."""

import numpy as np

from kernels.kernel4_ofdm.ofdm_reference import (
    fft,
    remove_cyclic_prefix,
)


def demodulate_waveforms(
    rx_waveforms: np.ndarray,
    fft_size: int = 64,
    cp_length: int = 16,
) -> np.ndarray:
    """Convert received time-domain waveforms into a frequency-domain grid.

    Args:
        rx_waveforms: Complex array shaped (2, num_samples).
            Each row contains concatenated OFDM symbols for one RX antenna.
        fft_size: Number of useful samples per OFDM symbol.
        cp_length: Number of cyclic-prefix samples per OFDM symbol.

    Returns:
        Complex resource grid shaped (2, fft_size, num_ofdm_symbols).
    """
    waveforms = np.asarray(rx_waveforms, dtype=np.complex128)

    if (
        waveforms.ndim != 2
        or waveforms.shape[0] != 2
        or waveforms.shape[1] == 0
    ):
        raise ValueError(
            "rx_waveforms must have shape (2, num_samples), "
            "with num_samples > 0"
        )

    if not np.all(np.isfinite(waveforms)):
        raise ValueError("rx_waveforms must contain only finite values")

    if (
        not isinstance(fft_size, (int, np.integer))
        or isinstance(fft_size, (bool, np.bool_))
        or fft_size <= 0
    ):
        raise ValueError("fft_size must be a positive integer")

    if (
        not isinstance(cp_length, (int, np.integer))
        or isinstance(cp_length, (bool, np.bool_))
        or cp_length < 0
        or cp_length > fft_size
    ):
        raise ValueError("cp_length must be between 0 and fft_size")

    symbol_length = fft_size + cp_length

    if waveforms.shape[1] % symbol_length != 0:
        raise ValueError(
            "Waveform length must be divisible by fft_size + cp_length"
        )

    num_ofdm_symbols = waveforms.shape[1] // symbol_length

    resource_grid = np.empty(
        (2, fft_size, num_ofdm_symbols),
        dtype=np.complex128,
    )

    for antenna in range(2):
        for symbol_index in range(num_ofdm_symbols):
            start = symbol_index * symbol_length
            end = start + symbol_length

            received_symbol = waveforms[antenna, start:end]

            useful_samples = remove_cyclic_prefix(
                received_symbol,
                cp_length,
                fft_size,
            )

            resource_grid[antenna, :, symbol_index] = fft(useful_samples)

    return resource_grid
