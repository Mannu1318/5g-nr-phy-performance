"""Unit tests for the Kernel 5 Python channel-estimation reference."""

import numpy as np
import pytest

from kernels.kernel5_channel_estimation.channel_estimation_reference import (
    estimate_channel,
)


def test_constant_channel_is_recovered():
    pilot_symbols = np.array([1 + 0j, 1 + 0j, 1 + 0j])
    channel = 0.7 - 0.4j
    received = pilot_symbols * channel
    pilot_indices = [2, 6, 10]
    estimate_indices = list(range(2, 11))

    actual = estimate_channel(
        pilot_symbols, received, pilot_indices, estimate_indices
    )

    np.testing.assert_allclose(actual, channel, rtol=1e-12, atol=1e-12)


def test_linear_complex_channel_is_interpolated():
    pilot_indices = np.array([0, 4, 8])
    estimate_indices = np.arange(9)
    pilot_symbols = np.array([1 + 0j, 1 + 0j, 1 + 0j])

    # Both real and imaginary parts vary linearly with subcarrier index.
    def channel_at(k):
        return (0.2 + 0.1 * k) + 1j * (0.5 - 0.05 * k)

    received = np.array([channel_at(k) for k in pilot_indices])

    actual = estimate_channel(
        pilot_symbols, received, pilot_indices, estimate_indices
    )
    expected = np.array([channel_at(k) for k in estimate_indices])

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def test_ls_estimates_are_correct_at_pilot_positions():
    pilot_symbols = np.array([1 + 1j, 2 - 1j, -1 + 2j])
    expected_channel = np.array([0.5 + 0.2j, -0.3 + 0.7j, 1.1 - 0.4j])
    received = pilot_symbols * expected_channel
    pilot_indices = [1, 5, 9]

    actual = estimate_channel(
        pilot_symbols, received, pilot_indices, pilot_indices
    )

    np.testing.assert_allclose(
        actual, expected_channel, rtol=1e-12, atol=1e-12
    )


def test_requested_output_order_is_preserved():
    pilot_symbols = [1 + 0j, 1 + 0j]
    received = [1 + 0j, 5 + 2j]

    actual = estimate_channel(
        pilot_symbols, received, [2, 6], [6, 3, 2, 5]
    )

    expected = np.array([5 + 2j, 2 + 0.5j, 1 + 0j, 4 + 1.5j])
    np.testing.assert_allclose(actual, expected)


def test_single_pilot_at_its_own_position():
    actual = estimate_channel([2 + 0j], [3 + 4j], [7], [7, 7])

    np.testing.assert_allclose(actual, [1.5 + 2j, 1.5 + 2j])


def test_empty_estimate_request_returns_empty_array():
    actual = estimate_channel([1 + 0j], [2 + 3j], [4], [])

    assert actual.shape == (0,)
    assert actual.dtype == np.complex128


def test_output_dtype_is_complex128():
    actual = estimate_channel([1 + 0j, 1 + 0j], [1 + 1j, 2 + 2j], [0, 2], [0, 1, 2])

    assert actual.dtype == np.complex128


@pytest.mark.parametrize(
    ("pilot_symbols", "received", "pilot_indices", "estimate_indices"),
    [
        ([], [], [], [0]),
        ([1 + 0j, 1 + 0j], [1 + 0j], [0, 2], [0]),
        ([1 + 0j, 1 + 0j], [1 + 0j, 2 + 0j], [0], [0]),
        ([1 + 0j, 1 + 0j], [1 + 0j, 2 + 0j], [2, 2], [2]),
        ([1 + 0j, 1 + 0j], [1 + 0j, 2 + 0j], [3, 1], [2]),
        ([0 + 0j], [1 + 0j], [0], [0]),
        ([1 + 0j], [1 + 0j], [0], [-1]),
        ([1 + 0j, 1 + 0j], [1 + 0j, 2 + 0j], [2, 4], [1]),
        ([1 + 0j], [complex(np.nan, 0)], [0], [0]),
        ([complex(np.inf, 0)], [1 + 0j], [0], [0]),
    ],
)
def test_invalid_inputs_raise_value_error(
    pilot_symbols, received, pilot_indices, estimate_indices
):
    with pytest.raises(ValueError):
        estimate_channel(
            pilot_symbols, received, pilot_indices, estimate_indices
        )


@pytest.mark.parametrize(
    ("pilot_indices", "estimate_indices"),
    [
        ([0.0, 2.0], [0, 1]),
        ([0, 2], [1.5]),
        ([True, False], [0]),
    ],
)
def test_non_integer_indices_are_rejected(pilot_indices, estimate_indices):
    with pytest.raises(TypeError):
        estimate_channel(
            [1 + 0j] * len(pilot_indices),
            [1 + 0j] * len(pilot_indices),
            pilot_indices,
            estimate_indices,
        )


def test_non_one_dimensional_input_is_rejected():
    with pytest.raises(ValueError, match="one-dimensional"):
        estimate_channel(
            [[1 + 0j, 1 + 0j]],
            [1 + 0j, 1 + 0j],
            [0, 2],
            [0, 1],
        )


def test_single_pilot_cannot_estimate_other_subcarriers():
    with pytest.raises(ValueError, match="single pilot"):
        estimate_channel([1 + 0j], [2 + 0j], [3], [2])


def test_received_noise_changes_the_ls_estimate():
    # A deterministic noise sample demonstrates the LS estimator's response
    # to noise without relying on a random statistical threshold.
    pilot = 1 + 0j
    received = 0.8 + 0.1j
    actual = estimate_channel([pilot], [received], [4], [4])

    np.testing.assert_allclose(actual, [0.8 + 0.1j])
