import numpy as np
import pytest

from integration.tx_chain.resource_grid import build_mimo_resource_grid


def test_grid_shape_and_dtype():
    streams = [[1 + 1j, 2 + 2j], [3 + 3j, 4 + 4j]]

    grid, pilot_bins, data_bins = build_mimo_resource_grid(streams)

    assert grid.shape == (2, 64, 3)
    assert grid.dtype == np.complex128
    assert pilot_bins.dtype == np.int64
    assert data_bins.dtype == np.int64


def test_pilot_bins_and_data_bins_are_disjoint():
    streams = [[], []]

    grid, pilot_bins, data_bins = build_mimo_resource_grid(streams)

    assert len(set(pilot_bins) & set(data_bins)) == 0
    assert 0 not in pilot_bins
    assert 0 not in data_bins
    assert np.all(pilot_bins % 2 == 1)
    assert np.all(data_bins % 2 == 0)


def test_pilots_are_orthogonal_in_time():
    grid, pilot_bins, _ = build_mimo_resource_grid([[], []])

    # TX0 sends pilots in OFDM symbol 0, TX1 in symbol 1.
    assert np.all(grid[0, pilot_bins, 0] == 1 + 0j)
    assert np.all(grid[1, pilot_bins, 1] == 1 + 0j)

    assert np.all(grid[1, :, 0] == 0)
    assert np.all(grid[0, :, 1] == 0)


def test_independent_data_streams_are_mapped_separately():
    stream0 = [1 + 1j, 2 + 2j]
    stream1 = [3 + 3j, 4 + 4j]

    grid, _, data_bins = build_mimo_resource_grid([stream0, stream1])

    assert grid[0, data_bins[0], 2] == stream0[0]
    assert grid[0, data_bins[1], 2] == stream0[1]

    assert grid[1, data_bins[0], 2] == stream1[0]
    assert grid[1, data_bins[1], 2] == stream1[1]


def test_unused_data_positions_are_zero_padded():
    stream0 = [1 + 1j]
    stream1 = [2 + 2j]

    grid, _, data_bins = build_mimo_resource_grid([stream0, stream1])

    assert grid[0, data_bins[0], 2] == stream0[0]
    assert grid[1, data_bins[0], 2] == stream1[0]
    assert np.all(grid[0, data_bins[1:], 2] == 0)
    assert np.all(grid[1, data_bins[1:], 2] == 0)


def test_custom_fft_and_ofdm_sizes():
    streams = [[1 + 0j], [0 + 1j]]

    grid, pilot_bins, data_bins = build_mimo_resource_grid(
        streams,
        fft_size=16,
        num_ofdm_symbols=4,
    )

    assert grid.shape == (2, 16, 4)
    assert len(pilot_bins) == 8
    assert len(data_bins) == 7


@pytest.mark.parametrize("fft_size", [0, 1, 2, 3, -4, True, 64.0])
def test_invalid_fft_size(fft_size):
    with pytest.raises(ValueError):
        build_mimo_resource_grid([[], []], fft_size=fft_size)


@pytest.mark.parametrize("num_symbols", [0, 1, 2, -3, True, 3.0])
def test_invalid_ofdm_symbol_count(num_symbols):
    with pytest.raises(ValueError):
        build_mimo_resource_grid([[], []], num_ofdm_symbols=num_symbols)


@pytest.mark.parametrize("pilot", [0, 0j, float("inf"), complex(float("nan"), 0)])
def test_invalid_pilot_value(pilot):
    with pytest.raises(ValueError):
        build_mimo_resource_grid([[], []], pilot_value=pilot)


@pytest.mark.parametrize(
    "streams",
    [
        [],
        [1 + 1j, 2 + 2j],
        [[1 + 1j]],
        [[1 + 1j], [2 + 2j], [3 + 3j]],
        [[1 + 1j], [complex(float("nan"), 0)]],
        [[1 + 1j], [complex(float("inf"), 0)]],
    ],
)
def test_invalid_data_streams(streams):
    with pytest.raises(ValueError):
        build_mimo_resource_grid(streams)


def test_rejects_streams_that_exceed_grid_capacity():
    streams = [[1 + 0j] * 33, [1 + 0j] * 33]

    with pytest.raises(ValueError, match="at most"):
        build_mimo_resource_grid(streams)
