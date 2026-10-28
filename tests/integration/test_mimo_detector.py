"""Tests for integrated MIMO Zero-Forcing symbol detection."""

import numpy as np
import pytest

from integration.rx_chain.mimo_detector import detect_mimo_symbols

def test_recovers_two_streams_through_known_channel():
    """ZF should recover transmitted symbols for a well-conditioned channel."""
    channel = np.array(
        [
            [1.0 + 0.0j, 0.2 + 0.1j],
            [0.1 - 0.1j, 1.2 + 0.0j],
        ],
        dtype=np.complex128,
    )

    # Four positions per stream: two OFDM symbols x two data bins.
    transmitted = np.array(
        [
            [1 + 1j, -1 + 1j, 1 - 1j, -1 - 1j],
            [-1 - 1j, 1 - 1j, -1 + 1j, 1 + 1j],
        ],
        dtype=np.complex128,
    )

    fft_size = 8
    num_symbols = 3
    data_bins = np.array([2, 4], dtype=np.int64)
    grid = np.zeros((2, fft_size, num_symbols), dtype=np.complex128)

    for symbol_index in range(2):
        for bin_index, fft_bin in enumerate(data_bins):
            position = symbol_index * len(data_bins) + bin_index
            grid[:, fft_bin, symbol_index + 1] = (
                channel @ transmitted[:, position]
            )

    estimates = np.repeat(
        channel[:, :, np.newaxis], len(data_bins), axis=2
    )

    detected = detect_mimo_symbols(
        received_grid=grid,
        channel_estimates=estimates,
        data_bins=data_bins,
        first_data_symbol=1,
    )

    assert detected.shape == (2, 2, 2)
    np.testing.assert_allclose(
        detected.reshape(2, -1),
        transmitted,
        rtol=1e-12,
        atol=1e-12,
    )

def test_rejects_invalid_received_grid_shape():
    with pytest.raises(ValueError, match="received_grid"):
        detect_mimo_symbols(
            received_grid=np.zeros((1, 8, 3), dtype=np.complex128),
            channel_estimates=np.ones((2, 2, 2), dtype=np.complex128),
            data_bins=np.array([2, 4]),
        )


def test_rejects_channel_estimate_shape_mismatch():
    with pytest.raises(ValueError, match="channel_estimates"):
        detect_mimo_symbols(
            received_grid=np.zeros((2, 8, 3), dtype=np.complex128),
            channel_estimates=np.ones((2, 2, 3), dtype=np.complex128),
            data_bins=np.array([2, 4]),
        )


def test_rejects_out_of_range_data_bins():
    with pytest.raises(ValueError, match="outside the FFT grid"):
        detect_mimo_symbols(
            received_grid=np.zeros((2, 8, 3), dtype=np.complex128),
            channel_estimates=np.ones((2, 2, 1), dtype=np.complex128),
            data_bins=np.array([8]),
        )


def test_rejects_nonfinite_channel_estimates():
    estimates = np.ones((2, 2, 2), dtype=np.complex128)
    estimates[0, 0, 0] = np.nan

    with pytest.raises(ValueError, match="finite"):
        detect_mimo_symbols(
            received_grid=np.zeros((2, 8, 3), dtype=np.complex128),
            channel_estimates=estimates,
            data_bins=np.array([2, 4]),
        )


def test_rejects_singular_channel():
    singular_channel = np.array(
        [[1.0 + 0.0j, 1.0 + 0.0j],
         [1.0 + 0.0j, 1.0 + 0.0j]],
        dtype=np.complex128,
    )

    estimates = np.repeat(
        singular_channel[:, :, np.newaxis], 2, axis=2
    )

    with pytest.raises(ValueError, match="MIMO ZF detection failed"):
        detect_mimo_symbols(
            received_grid=np.ones((2, 8, 3), dtype=np.complex128),
            channel_estimates=estimates,
            data_bins=np.array([2, 4]),
        )
