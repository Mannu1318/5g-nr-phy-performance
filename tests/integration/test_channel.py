
import numpy as np
import pytest

from integration.channel import apply_mimo_channel


def test_identity_channel_preserves_waveforms():
    tx = np.array(
        [[1 + 2j, 3 - 1j], [2 - 1j, -1 + 4j]],
        dtype=np.complex128,
    )
    received = apply_mimo_channel(tx, np.eye(2))

    np.testing.assert_allclose(received, tx)


def test_channel_matrix_mixes_transmit_antennas():
    tx = np.array(
        [[1 + 0j, 2 + 1j], [3 - 1j, -1 + 2j]],
        dtype=np.complex128,
    )
    channel = np.array(
        [[1 + 0j, 2 + 0j], [0 + 1j, 1 - 1j]],
        dtype=np.complex128,
    )

    received = apply_mimo_channel(tx, channel)

    np.testing.assert_allclose(received, channel @ tx)


def test_zero_noise_matches_no_noise_result():
    tx = np.ones((2, 8), dtype=np.complex128)
    channel = np.array([[1, 0.5], [0.25, 1]], dtype=np.complex128)

    without_noise = apply_mimo_channel(tx, channel)
    with_zero_noise = apply_mimo_channel(
        tx, channel, noise_variance=0.0,
        rng=np.random.default_rng(42),
    )

    np.testing.assert_allclose(with_zero_noise, without_noise)


def test_awgn_is_reproducible_with_same_seed():
    tx = np.ones((2, 100), dtype=np.complex128)
    channel = np.eye(2, dtype=np.complex128)

    received_a = apply_mimo_channel(
        tx, channel, noise_variance=0.2,
        rng=np.random.default_rng(123),
    )
    received_b = apply_mimo_channel(
        tx, channel, noise_variance=0.2,
        rng=np.random.default_rng(123),
    )

    np.testing.assert_array_equal(received_a, received_b)


def test_awgn_has_approximately_requested_noise_power():
    tx = np.zeros((2, 100_000), dtype=np.complex128)
    noise_variance = 0.4

    received = apply_mimo_channel(
        tx,
        np.eye(2, dtype=np.complex128),
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
        apply_mimo_channel(tx, np.eye(2))


@pytest.mark.parametrize(
    "channel",
    [
        np.eye(3),
        np.ones((2, 3)),
        np.array([[1, np.inf], [0, 1]]),
        np.array([[1, np.nan], [0, 1]]),
    ],
)
def test_invalid_channel_matrix_raises(channel):
    with pytest.raises(ValueError):
        apply_mimo_channel(np.ones((2, 8)), channel)


@pytest.mark.parametrize(
    "noise_variance",
    [-1.0, np.inf, -np.inf, np.nan, 1 + 2j, True, "0.1"],
)
def test_invalid_noise_variance_raises(noise_variance):
    with pytest.raises(ValueError):
        apply_mimo_channel(
            np.ones((2, 8)),
            np.eye(2),
            noise_variance=noise_variance,
        )
