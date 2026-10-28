import numpy as np
import pytest

from integration.tx_chain.ofdm_transmitter import modulate_resource_grid
from kernels.kernel4_ofdm.ofdm_reference import fft


def test_waveform_shape_and_dtype():
    grid = np.zeros((2, 64, 3), dtype=np.complex128)

    waveform = modulate_resource_grid(grid, cp_length=16)

    assert waveform.shape == (2, 3 * (64 + 16))
    assert waveform.dtype == np.complex128


def test_zero_grid_produces_zero_waveform():
    grid = np.zeros((2, 64, 3), dtype=np.complex128)

    waveform = modulate_resource_grid(grid, cp_length=16)

    np.testing.assert_array_equal(waveform, 0)


def test_cyclic_prefix_matches_end_of_ifft_symbol():
    grid = np.zeros((2, 64, 3), dtype=np.complex128)
    grid[0, 5, 0] = 1 + 2j
    cp_length = 8

    waveform = modulate_resource_grid(grid, cp_length=cp_length)

    first_symbol = waveform[0, :64 + cp_length]
    useful_samples = first_symbol[cp_length:]

    np.testing.assert_allclose(
        first_symbol[:cp_length],
        useful_samples[-cp_length:],
    )


def test_ofdm_modulation_round_trip_without_cp():
    rng = np.random.default_rng(1234)
    grid = (
        rng.standard_normal((2, 64, 3))
        + 1j * rng.standard_normal((2, 64, 3))
    )

    waveform = modulate_resource_grid(grid, cp_length=0)

    for antenna in range(2):
        for symbol_index in range(3):
            start = symbol_index * 64
            recovered = fft(waveform[antenna, start:start + 64])

            np.testing.assert_allclose(
                recovered,
                grid[antenna, :, symbol_index],
                rtol=1e-12,
                atol=1e-12,
            )


@pytest.mark.parametrize("cp_length", [-1, 65, True, 1.5])
def test_invalid_cp_length(cp_length):
    grid = np.zeros((2, 64, 3), dtype=np.complex128)

    with pytest.raises(ValueError):
        modulate_resource_grid(grid, cp_length=cp_length)


@pytest.mark.parametrize(
    "grid",
    [
        np.zeros((64, 3)),
        np.zeros((1, 64, 3)),
        np.zeros((2, 0, 3)),
        np.zeros((2, 64, 0)),
        np.full((2, 64, 3), complex(float("nan"), 0)),
        np.full((2, 64, 3), complex(float("inf"), 0)),
    ],
)
def test_invalid_resource_grid(grid):
    with pytest.raises(ValueError):
        modulate_resource_grid(grid)
