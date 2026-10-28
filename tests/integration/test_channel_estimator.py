
import numpy as np
import pytest

from integration.rx_chain.channel_estimator import estimate_mimo_channel


def test_estimates_constant_2x2_channel():
    fft_size = 64
    pilot_bins = np.arange(1, fft_size, 2, dtype=np.int64)
    data_bins = np.arange(2, fft_size - 1, 2, dtype=np.int64)

    channel = np.array(
        [[1 + 0.2j, 0.3 - 0.1j], [-0.2 + 0.4j, 1.2 + 0.1j]],
        dtype=np.complex128,
    )

    grid = np.zeros((2, fft_size, 2), dtype=np.complex128)

    for tx in range(2):
        grid[:, pilot_bins, tx] = channel[:, tx, None]

    estimates = estimate_mimo_channel(grid, pilot_bins, data_bins)

    assert estimates.shape == (2, 2, data_bins.size)

    for rx in range(2):
        for tx in range(2):
            np.testing.assert_allclose(
                estimates[rx, tx],
                channel[rx, tx],
                atol=1e-12,
            )


def test_estimates_channel_with_custom_pilot_value():
    fft_size = 32
    pilot_bins = np.arange(1, fft_size, 2, dtype=np.int64)
    data_bins = np.arange(2, fft_size - 1, 2, dtype=np.int64)
    pilot_value = 2 + 1j

    channel = np.array(
        [[1 + 0j, 0.2j], [0.5, 1 - 0.3j]],
        dtype=np.complex128,
    )

    grid = np.zeros((2, fft_size, 2), dtype=np.complex128)

    for tx in range(2):
        grid[:, pilot_bins, tx] = (
            channel[:, tx, None] * pilot_value
        )

    estimates = estimate_mimo_channel(
        grid, pilot_bins, data_bins, pilot_value=pilot_value
    )

    for rx in range(2):
        for tx in range(2):
            np.testing.assert_allclose(
                estimates[rx, tx],
                channel[rx, tx],
                atol=1e-12,
            )


@pytest.mark.parametrize(
    "grid",
    [
        np.zeros((64, 3)),
        np.zeros((1, 64, 3)),
        np.zeros((2, 64, 1)),
        np.full((2, 64, 3), np.nan),
    ],
)
def test_invalid_received_grid_raises(grid):
    with pytest.raises(ValueError):
        estimate_mimo_channel(
            grid,
            np.array([1, 3, 5]),
            np.array([2, 4]),
        )


@pytest.mark.parametrize("pilot_value", [0, np.nan, np.inf])
def test_invalid_pilot_value_raises(pilot_value):
    grid = np.zeros((2, 8, 2), dtype=np.complex128)

    with pytest.raises(ValueError):
        estimate_mimo_channel(
            grid,
            np.array([1, 3, 5, 7]),
            np.array([2, 4, 6]),
            pilot_value=pilot_value,
        )


def test_unsorted_pilot_bins_raise():
    grid = np.zeros((2, 8, 2), dtype=np.complex128)

    with pytest.raises(ValueError):
        estimate_mimo_channel(
            grid,
            np.array([3, 1, 5, 7]),
            np.array([2, 4, 6]),
        )


def test_out_of_range_data_bins_raise():
    grid = np.zeros((2, 8, 2), dtype=np.complex128)

    with pytest.raises(ValueError):
        estimate_mimo_channel(
            grid,
            np.array([1, 3, 5, 7]),
            np.array([0, 2, 4, 6]),
        )
