"""Correctness tests for the experimental 2x2 MIMO MMSE detector."""

import numpy as np
import pytest

from integration.rx_chain.mmse_detector import detect_mmse_symbols


def test_identity_channel_recovers_symbols_at_zero_noise():
    transmitted = np.array(
        [1.0 + 0.5j, -0.25 + 1.0j], dtype=np.complex128
    )
    received = np.zeros((2, 8, 3), dtype=np.complex128)
    received[:, 2, 2] = transmitted

    channels = np.eye(2, dtype=np.complex128)[:, :, None]
    detected = detect_mmse_symbols(
        received, channels, np.array([2]), noise_variance=0.0
    )

    assert detected.shape == (2, 1, 1)
    np.testing.assert_allclose(
        detected[:, 0, 0], transmitted, atol=1e-12, rtol=1e-12
    )


def test_complex_channel_matches_mmse_normal_equation():
    channel = np.array(
        [
            [1.0 + 0.5j, 0.25 - 0.75j],
            [-0.5 + 0.25j, 1.5 + 0.5j],
        ],
        dtype=np.complex128,
    )
    received_vector = np.array(
        [0.75 + 0.25j, -0.5 + 1.0j], dtype=np.complex128
    )
    noise_variance = 0.001
    regularization = 8 * noise_variance

    received = np.zeros((2, 8, 3), dtype=np.complex128)
    received[:, 3, 2] = received_vector

    detected = detect_mmse_symbols(
        received,
        channel[:, :, None],
        np.array([3]),
        noise_variance=noise_variance,
    )

    expected = np.linalg.solve(
        channel.conj().T @ channel
        + regularization * np.eye(2),
        channel.conj().T @ received_vector,
    )
    np.testing.assert_allclose(
        detected[:, 0, 0], expected, atol=1e-12, rtol=1e-12
    )


def test_zero_noise_matches_direct_zf_solution():
    channel = np.array(
        [[1.0 + 0.2j, 0.3 - 0.1j], [-0.2 + 0.4j, 1.2 + 0.1j]],
        dtype=np.complex128,
    )
    transmitted = np.array(
        [1.0 - 0.5j, -0.25 + 0.75j], dtype=np.complex128
    )
    received_vector = channel @ transmitted

    received = np.zeros((2, 8, 3), dtype=np.complex128)
    received[:, 4, 2] = received_vector

    detected = detect_mmse_symbols(
        received,
        channel[:, :, None],
        np.array([4]),
        noise_variance=0.0,
    )

    expected = np.linalg.solve(channel, received_vector)
    np.testing.assert_allclose(
        detected[:, 0, 0], expected, atol=1e-12, rtol=1e-12
    )


def test_positive_regularization_handles_singular_channel():
    channel = np.array(
        [[1.0, 2.0], [2.0, 4.0]], dtype=np.complex128
    )
    received_vector = np.array([1.0 + 0.5j, 2.0 + 1.0j])

    received = np.zeros((2, 8, 3), dtype=np.complex128)
    received[:, 1, 2] = received_vector

    detected = detect_mmse_symbols(
        received,
        channel[:, :, None],
        np.array([1]),
        noise_variance=0.001,
    )

    assert detected.shape == (2, 1, 1)
    assert np.all(np.isfinite(detected))


def test_output_shape_and_finite_values_for_multiple_bins():
    rng = np.random.default_rng(1234)
    received = rng.standard_normal((2, 8, 4)) + 1j * rng.standard_normal(
        (2, 8, 4)
    )
    channels = np.repeat(
        np.eye(2, dtype=np.complex128)[:, :, None], 3, axis=2
    )

    detected = detect_mmse_symbols(
        received,
        channels,
        np.array([1, 3, 5]),
        noise_variance=0.0005,
    )

    assert detected.shape == (2, 2, 3)
    assert np.all(np.isfinite(detected))


@pytest.mark.parametrize(
    ("noise_variance", "symbol_energy"),
    [
        (-0.1, 1.0),
        (np.nan, 1.0),
        (np.inf, 1.0),
        (0.001, 0.0),
        (0.001, -1.0),
        (0.001, np.inf),
    ],
)
def test_invalid_noise_variance_or_symbol_energy_is_rejected(
    noise_variance, symbol_energy
):
    received = np.zeros((2, 8, 3), dtype=np.complex128)
    channels = np.repeat(
        np.eye(2, dtype=np.complex128)[:, :, None], 2, axis=2
    )

    with pytest.raises(ValueError):
        detect_mmse_symbols(
            received,
            channels,
            np.array([1, 2]),
            noise_variance=noise_variance,
            symbol_energy=symbol_energy,
        )


def test_invalid_received_grid_shape_is_rejected():
    with pytest.raises(ValueError, match="received_grid"):
        detect_mmse_symbols(
            np.zeros((3, 8, 3)),
            np.zeros((2, 2, 1)),
            np.array([1]),
            noise_variance=0.001,
        )


def test_invalid_channel_shape_is_rejected():
    with pytest.raises(ValueError, match="channel_estimates"):
        detect_mmse_symbols(
            np.zeros((2, 8, 3)),
            np.zeros((2, 3, 1)),
            np.array([1]),
            noise_variance=0.001,
        )


@pytest.mark.parametrize(
    "data_bins",
    [
        np.array([], dtype=int),
        np.array([1.5]),
        np.array([-1]),
        np.array([8]),
        np.array([1, 1]),
    ],
)
def test_invalid_data_bins_are_rejected(data_bins):
    with pytest.raises(ValueError):
        detect_mmse_symbols(
            np.zeros((2, 8, 3)),
            np.repeat(np.eye(2, dtype=np.complex128)[:, :, None],
                      len(data_bins), axis=2),
            data_bins,
            noise_variance=0.001,
        )


def test_nonfinite_received_samples_are_rejected():
    received = np.zeros((2, 8, 3), dtype=np.complex128)
    received[0, 1, 2] = np.nan

    with pytest.raises(ValueError, match="received_grid"):
        detect_mmse_symbols(
            received,
            np.eye(2, dtype=np.complex128)[:, :, None],
            np.array([1]),
            noise_variance=0.001,
        )


def test_nonfinite_channel_estimates_are_rejected():
    channel = np.eye(2, dtype=np.complex128)[:, :, None]
    channel[0, 0, 0] = np.inf

    with pytest.raises(ValueError, match="channel_estimates"):
        detect_mmse_symbols(
            np.zeros((2, 8, 3)),
            channel,
            np.array([1]),
            noise_variance=0.001,
        )


def test_invalid_first_data_symbol_is_rejected():
    with pytest.raises(ValueError, match="first_data_symbol"):
        detect_mmse_symbols(
            np.zeros((2, 8, 3)),
            np.eye(2, dtype=np.complex128)[:, :, None],
            np.array([1]),
            noise_variance=0.001,
            first_data_symbol=3,
        )


def test_invalid_first_data_symbol_is_rejected():
    with pytest.raises(ValueError, match="first_data_symbol"):
        detect_mmse_symbols(
            np.zeros((2, 8, 3)),
            np.eye(2, dtype=np.complex128)[:, :, None],
            np.array([1]),
            noise_variance=0.001,
            first_data_symbol=3,
        )
