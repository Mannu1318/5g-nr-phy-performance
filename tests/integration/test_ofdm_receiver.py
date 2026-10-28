
import numpy as np
import pytest

from integration.rx_chain.ofdm_receiver import demodulate_waveforms
from integration.tx_chain.ofdm_transmitter import modulate_resource_grid


def test_receiver_recovers_transmitted_resource_grid():
    rng = np.random.default_rng(10)
    grid = (
        rng.standard_normal((2, 64, 3))
        + 1j * rng.standard_normal((2, 64, 3))
    )

    waveform = modulate_resource_grid(grid, cp_length=16)
    recovered = demodulate_waveforms(
        waveform,
        fft_size=64,
        cp_length=16,
    )

    np.testing.assert_allclose(recovered, grid, atol=1e-12)


def test_receiver_output_shape_and_dtype():
    grid = np.zeros((2, 32, 4), dtype=np.complex128)
    waveform = modulate_resource_grid(grid, cp_length=8)

    recovered = demodulate_waveforms(
        waveform,
        fft_size=32,
        cp_length=8,
    )

    assert recovered.shape == (2, 32, 4)
    assert recovered.dtype == np.complex128


def test_receiver_handles_zero_cyclic_prefix():
    grid = np.ones((2, 16, 2), dtype=np.complex128)
    waveform = modulate_resource_grid(grid, cp_length=0)

    recovered = demodulate_waveforms(
        waveform,
        fft_size=16,
        cp_length=0,
    )

    np.testing.assert_allclose(recovered, grid, atol=1e-12)


def test_receiver_handles_cp_equal_to_fft_size():
    grid = np.ones((2, 8, 2), dtype=np.complex128)
    waveform = modulate_resource_grid(grid, cp_length=8)

    recovered = demodulate_waveforms(
        waveform,
        fft_size=8,
        cp_length=8,
    )

    np.testing.assert_allclose(recovered, grid, atol=1e-12)


@pytest.mark.parametrize(
    "waveforms",
    [
        np.ones(16),
        np.ones((1, 16)),
        np.ones((3, 16)),
        np.empty((2, 0)),
        np.array([[1, np.inf], [1, 2]]),
        np.array([[1, np.nan], [1, 2]]),
    ],
)
def test_invalid_waveforms_raise(waveforms):
    with pytest.raises(ValueError):
        demodulate_waveforms(waveforms, fft_size=4, cp_length=1)


@pytest.mark.parametrize("fft_size", [0, -1, 2.5, True])
def test_invalid_fft_size_raises(fft_size):
    with pytest.raises(ValueError):
        demodulate_waveforms(
            np.ones((2, 16)),
            fft_size=fft_size,
            cp_length=0,
        )


@pytest.mark.parametrize("cp_length", [-1, 5, 1.5, True])
def test_invalid_cp_length_raises(cp_length):
    with pytest.raises(ValueError):
        demodulate_waveforms(
            np.ones((2, 16)),
            fft_size=4,
            cp_length=cp_length,
        )


def test_waveform_length_must_contain_complete_symbols():
    with pytest.raises(ValueError, match="divisible"):
        demodulate_waveforms(
            np.ones((2, 17)),
            fft_size=4,
            cp_length=1,
        )
