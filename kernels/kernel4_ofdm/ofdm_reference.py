
"""Python reference implementation for Kernel 4: OFDM FFT/IFFT."""

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt


ComplexArray = npt.NDArray[np.complex128]


def _as_complex_array(samples: Sequence[complex] | npt.NDArray) -> ComplexArray:
    """Convert a one-dimensional input sequence to complex128."""
    array = np.asarray(samples, dtype=np.complex128)

    if array.ndim != 1:
        raise ValueError("Input samples must be a one-dimensional sequence.")

    return array


def fft(samples: Sequence[complex] | npt.NDArray) -> ComplexArray:
    """Compute the unnormalized forward FFT of time-domain samples."""
    array = _as_complex_array(samples)

    if array.size == 0:
        raise ValueError("FFT input must not be empty.")

    return np.fft.fft(array)


def ifft(symbols: Sequence[complex] | npt.NDArray) -> ComplexArray:
    """Compute the normalized inverse FFT of frequency-domain symbols."""
    array = _as_complex_array(symbols)

    if array.size == 0:
        raise ValueError("IFFT input must not be empty.")

    return np.fft.ifft(array)

def map_subcarriers(
    symbols: Sequence[complex] | npt.NDArray,
    bin_indices: Sequence[int],
    fft_size: int,
) -> ComplexArray:
    """Place symbols into specified FFT bins; initialize other bins to zero."""
    symbol_array = _as_complex_array(symbols)
    bins = np.asarray(bin_indices)

    if not isinstance(fft_size, (int, np.integer)) or isinstance(fft_size, (bool, np.bool_)):
        raise ValueError("FFT size must be a positive integer.")

    if fft_size <= 0:
        raise ValueError("FFT size must be a positive integer.")

    if bins.ndim != 1:
        raise ValueError("Bin indices must be a one-dimensional sequence.")

    if not np.issubdtype(bins.dtype, np.integer) or np.issubdtype(bins.dtype, np.bool_):
        raise ValueError("Bin indices must be integers.")

    if symbol_array.size != bins.size:
        raise ValueError("The number of symbols must match the number of bin indices.")

    if np.any(bins < 0) or np.any(bins >= fft_size):
        raise ValueError("Bin indices must be between 0 and fft_size - 1.")

    if np.unique(bins).size != bins.size:
        raise ValueError("Duplicate bin indices are not allowed.")

    output = np.zeros(fft_size, dtype=np.complex128)
    output[bins] = symbol_array
    return output


def extract_subcarriers(
    spectrum: Sequence[complex] | npt.NDArray,
    bin_indices: Sequence[int],
) -> ComplexArray:
    """Extract frequency-domain values from specified FFT bins."""
    spectrum_array = _as_complex_array(spectrum)
    bins = np.asarray(bin_indices)

    if bins.ndim != 1:
        raise ValueError("Bin indices must be a one-dimensional sequence.")

    if not np.issubdtype(bins.dtype, np.integer) or np.issubdtype(bins.dtype, np.bool_):
        raise ValueError("Bin indices must be integers.")

    if np.any(bins < 0) or np.any(bins >= spectrum_array.size):
        raise ValueError("Bin indices are outside the spectrum.")

    if np.unique(bins).size != bins.size:
        raise ValueError("Duplicate bin indices are not allowed.")

    return spectrum_array[bins].copy()

def add_cyclic_prefix(
    samples: Sequence[complex] | npt.NDArray,
    cp_length: int,
) -> ComplexArray:
    """Prepend a cyclic prefix copied from the end of an OFDM symbol."""
    sample_array = _as_complex_array(samples)

    if not isinstance(cp_length, (int, np.integer)) or isinstance(cp_length, (bool, np.bool_)):
        raise ValueError("CP length must be a non-negative integer.")

    if cp_length < 0 or cp_length > sample_array.size:
        raise ValueError("CP length must be between 0 and the symbol length.")

    if cp_length == 0:
        return sample_array.copy()

    return np.concatenate((sample_array[-cp_length:], sample_array))


def remove_cyclic_prefix(
    received_samples: Sequence[complex] | npt.NDArray,
    cp_length: int,
    useful_length: int,
) -> ComplexArray:
    """Remove the CP and return exactly useful_length samples."""
    received_array = _as_complex_array(received_samples)

    if not isinstance(cp_length, (int, np.integer)) or isinstance(cp_length, (bool, np.bool_)):
        raise ValueError("CP length must be a non-negative integer.")

    if not isinstance(useful_length, (int, np.integer)) or isinstance(useful_length, (bool, np.bool_)):
        raise ValueError("Useful length must be a non-negative integer.")

    if cp_length < 0:
        raise ValueError("CP length must be non-negative.")

    if useful_length < 0:
        raise ValueError("Useful length must be non-negative.")

    if received_array.size < cp_length + useful_length:
        raise ValueError("Input does not contain enough samples for CP removal.")

    return received_array[cp_length:cp_length + useful_length].copy()
