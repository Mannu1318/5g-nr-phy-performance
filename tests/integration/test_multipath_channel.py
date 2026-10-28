import numpy as np
import pytest

from integration.channel import (
    apply_mimo_channel,
    apply_mimo_multipath_channel,
)


def test_single_tap_matches_existing_flat_fading_channel():
    tx = np.array(
        [
            [1 + 2j, 3 - 1j, -2 + 0.5j],
            [2 - 1j, -1 + 4j, 0.5 + 3j],
        ],
        dtype=np.complex128,
    )
    channel = np.array(
        [[1 + 0.5j, 0.2 - 0.1j], [0.3 + 0.2j, 1.1 - 0.4j]],
        dtype=np.complex128,
    )

    expected = apply_mimo_channel(tx, channel)
    actual = apply_mimo_multipath_channel(
        tx,
        channel_taps=channel[np.newaxis, :, :],
    )

    np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-13)


def test_two_tap_channel_matches_manual_causal_convolution():
    tx = np.array(
        [
            [1 + 1j, 2 - 1j, 3 + 0j, -1 + 2j],
            [2 + 0j, -1 + 1j, 0.5 - 2j, 4 + 1j],
        ],
        dtype=np.complex128,
    )
    taps = np.array(
        [
            [[1, 0.5j], [0.25, 2]],
            [[0.2, -0.1j], [1j, 0.3]],
        ],
        dtype=np.complex128,
    )

    expected = np.zeros_like(tx)

    for n in range(tx.shape[1]):
        expected[:, n] = taps[0] @ tx[:, n]
        if n >= 1:
            expected[:, n] += taps[1] @ tx[:, n - 1]

    actual = apply_mimo_multipath_channel(tx, taps)

    np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-13)


def test_first_output_sample_uses_only_zero_delay_tap():
    tx = np.array(
        [[1 + 2j, 3 + 4j], [5 - 1j, 2 + 3j]],
        dtype=np.complex128,
    )
    taps = np.array(
        [
            [[1, 2], [3, 4]],
            [[5, 6], [7, 8]],
            [[9, 10], [11, 12]],
        ],
        dtype=np.complex128,
    )

    actual = apply_mimo_multipath_channel(tx, taps)

    np.testing.assert_allclose(actual[:, 0], taps[0] @ tx[:, 0])


def test_output_shape_is_preserved_without_trailing_convolution_tail():
    tx = np.ones((2, 5), dtype=np.complex128)
    taps = np.ones((4, 2, 2), dtype=np.complex128)

    actual = apply_mimo_multipath_channel(tx, taps)

    assert actual.shape == tx.shape


def test_single_tap_zero_noise_is_deterministic():
    tx = np.arange(16, dtype=np.float64).reshape(2, 8).astype(np.complex128)
    taps = np.array([[[1, 0.2], [0.3, 1]]], dtype=np.complex128)

    first = apply_mimo_multipath_channel(tx, taps, noise_variance=0.0)
    second = apply_mimo_multipath_channel(tx, taps, noise_variance=0.0)

    np.testing.assert_array_equal(first, second)


def test_awgn_is_reproducible_with_same_seed():
    tx = np.zeros((2, 256), dtype=np.complex128)
    taps = np.array([np.eye(2)], dtype=np.complex128)

    received_a = apply_mimo_multipath_channel(
        tx,
        taps,
        noise_variance=0.2,
        rng=np.random.default_rng(123),
    )
    received_b = apply_mimo_multipath_channel(
        tx,
        taps,
        noise_variance=0.2,
        rng=np.random.default_rng(123),
    )

    np.testing.assert_array_equal(received_a, received_b)


def test_awgn_has_approximately_requested_complex_noise_power():
    tx = np.zeros((2, 100_000), dtype=np.complex128)
    taps = np.array([np.eye(2)], dtype=np.complex128)
    noise_variance = 0.4

    received = apply_mimo_multipath_channel(
        tx,
        taps,
        noise_variance=noise_variance,
        rng=np.random.default_rng(7),
    )

    measured_power = np.mean(np.abs(received) ** 2)
    assert measured_power == pytest.approx(noise_variance, rel=0.02)


@pytest.mark.parametrize(
    "tx",
    [
        np.ones(8),
        np.ones((3, 8)),
        np.empty((2, 0)),
        np.array([[1, np.inf], [1, 2]]),
        np.array([[1, np.nan], [1, 2]]),
    ],
)
def test_invalid_transmit_waveforms_raise(tx):
    with pytest.raises(ValueError):
        apply_mimo_multipath_channel(tx, np.array([np.eye(2)]))


@pytest.mark.parametrize(
    "taps",
    [
        np.eye(2),
        np.ones((2, 2)),
        np.empty((0, 2, 2)),
        np.ones((2, 3, 2)),
        np.ones((2, 2, 3)),
        np.array([[[1, 0], [0, np.inf]]]),
        np.array([[[1, 0], [0, np.nan]]]),
        np.zeros((2, 2, 2)),
    ],
)
def test_invalid_channel_taps_raise(taps):
    with pytest.raises(ValueError):
        apply_mimo_multipath_channel(np.ones((2, 8)), taps)


@pytest.mark.parametrize(
    "noise_variance",
    [-1.0, np.inf, -np.inf, np.nan, 1 + 2j, True, "0.1"],
)
def test_invalid_noise_variance_raises(noise_variance):
    with pytest.raises(ValueError):
        apply_mimo_multipath_channel(
            np.ones((2, 8)),
            np.array([np.eye(2)]),
            noise_variance=noise_variance,
        )

def test_multipath_frequency_response_matches_tap_fft():
    fft_size = 16

    taps = np.array(
        [
            [[1.0, 0.2j], [0.3, 0.8]],
            [[0.2, 0.1], [-0.15j, 0.25]],
            [[-0.1j, 0.05], [0.1, -0.2]],
        ],
        dtype=np.complex128,
    )

    # Independent reference: FFT along the tap-delay axis.
    padded_taps = np.zeros(
        (fft_size, 2, 2),
        dtype=np.complex128,
    )
    padded_taps[: taps.shape[0]] = taps
    fft_response = np.fft.fft(padded_taps, axis=0)

    # Direct implementation of H[k] = sum_l H_l * exp(-j*2*pi*k*l/N).
    bins = np.arange(fft_size)
    expected_response = np.zeros(
        (fft_size, 2, 2),
        dtype=np.complex128,
    )

    for delay, tap in enumerate(taps):
        phase = np.exp(-2j * np.pi * bins * delay / fft_size)
        expected_response += phase[:, None, None] * tap

    np.testing.assert_allclose(
        fft_response,
        expected_response,
        rtol=1e-13,
        atol=1e-13,
    )

def test_multipath_channel_matches_frequency_response_for_ofdm_tone():
    fft_size = 16
    subcarrier = 3
    num_samples = 4 * fft_size

    taps = np.array(
        [
            [[1.0, 0.2j], [0.3, 0.8]],
            [[0.2, 0.1], [-0.15j, 0.25]],
            [[-0.1j, 0.05], [0.1, -0.2]],
        ],
        dtype=np.complex128,
    )

    # Different complex amplitudes on the two transmit antennas.
    tx_vector = np.array([1.0 + 0.5j, -0.3 + 0.8j])

    n = np.arange(num_samples)
    tone = np.exp(2j * np.pi * subcarrier * n / fft_size)
    tx_waveforms = tx_vector[:, None] * tone[None, :]

    rx_waveforms = apply_mimo_multipath_channel(
        tx_waveforms,
        taps,
        noise_variance=0.0,
    )

    # Calculate the channel frequency response at this subcarrier.
    phase = np.exp(
        -2j * np.pi * subcarrier
        * np.arange(taps.shape[0]) / fft_size
    )

    frequency_response = np.sum(
        taps * phase[:, None, None],
        axis=0,
    )

    expected = (
        frequency_response @ tx_vector
    )[:, None] * tone[None, :]

    # Ignore initial samples affected by zero-valued prehistory.
    first_valid_sample = taps.shape[0] - 1

    np.testing.assert_allclose(
        rx_waveforms[:, first_valid_sample:],
        expected[:, first_valid_sample:],
        rtol=1e-12,
        atol=1e-12,
    )
