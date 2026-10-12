"""Correctness tests for the 2x2 MIMO ZF Python reference."""

import numpy as np
import pytest

from kernels.kernel6_mimo.mimo_zf_reference import (
    INVALID_SHAPE,
    NEAR_SINGULAR_CHANNEL,
    NONFINITE_INPUT,
    NUMERICAL_FAILURE,
    OK,
    SINGULAR_CHANNEL,
    zf_detect_batch,
    zf_detect_single,
)


def assert_recovered(actual, expected, atol=1e-10, rtol=1e-10):
    """Compare recovered complex symbols with the known transmitted values."""
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol)


def test_identity_channel_recovers_complex_symbols():
    H = np.eye(2, dtype=np.complex128)
    x = np.array([1.5 + 0.5j, -2.0 + 1.25j])
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x)


def test_diagonal_channel_recovers_symbols():
    H = np.diag([2.0 + 1.0j, 0.5 - 0.25j])
    x = np.array([1.0 - 2.0j, -0.5 + 3.0j])
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x)


def test_nondiagonal_real_channel_recovers_symbols():
    H = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    x = np.array([2.0, 1.0], dtype=np.complex128)
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x)


def test_complex_channel_recovers_symbols():
    H = np.array(
        [
            [1.0 + 0.5j, 0.25 - 0.75j],
            [-0.5 + 0.25j, 1.5 + 0.5j],
        ],
        dtype=np.complex128,
    )
    x = np.array([0.5 + 1.0j, -1.25 + 0.75j])
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x)


def test_channel_scaled_by_small_finite_factor():
    H = 1e-100 * np.array([[1.0, 0.25], [-0.5, 2.0]], dtype=np.complex128)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j])
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x, atol=1e-9, rtol=1e-9)


def test_channel_scaled_by_large_finite_factor():
    H = 1e100 * np.array([[1.0, 0.25], [-0.5, 2.0]], dtype=np.complex128)
    x = np.array([1.0 + 1.0j, -2.0 + 0.5j])
    y = H @ x

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert_recovered(estimate, x, atol=1e-9, rtol=1e-9)


def test_wrong_single_input_shapes_are_rejected():
    estimate, status = zf_detect_single(np.eye(3), np.ones(3))

    assert status == INVALID_SHAPE
    assert estimate.shape == (2,)
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()


@pytest.mark.parametrize(
    ("H", "y"),
    [
        (np.array([[1.0, 0.0], [0.0, np.nan]]), np.array([1.0, 2.0])),
        (np.eye(2), np.array([1.0, np.inf])),
        (np.array([[1.0 + 1.0j, 0.0], [0.0, np.inf]]), np.ones(2)),
    ],
)
def test_nonfinite_inputs_are_rejected(H, y):
    estimate, status = zf_detect_single(H, y)

    assert status == NONFINITE_INPUT
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()


def test_zero_channel_is_reported_as_singular():
    H = np.zeros((2, 2), dtype=np.complex128)
    y = np.array([1.0 + 1.0j, 2.0 - 1.0j])

    estimate, status = zf_detect_single(H, y)

    assert status == SINGULAR_CHANNEL
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()


def test_rank_deficient_nonzero_channel_is_rejected():
    H = np.array([[1.0, 2.0], [2.0, 4.0]], dtype=np.complex128)
    y = np.array([1.0, 2.0])

    estimate, status = zf_detect_single(H, y)

    assert status == NEAR_SINGULAR_CHANNEL
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()


def test_near_singular_channel_is_rejected():
    H = np.array(
        [[1.0, 1.0], [1.0, 1.0 + 1e-14]],
        dtype=np.complex128,
    )
    y = H @ np.array([1.0, 2.0])

    estimate, status = zf_detect_single(H, y)

    assert status == NEAR_SINGULAR_CHANNEL
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()


def test_batch_recovers_pairs_with_different_channel_matrices():
    H = np.array(
        [
            [[1.0, 0.0], [0.0, 1.0]],
            [[1.0, 1.0], [1.0, -1.0]],
            [
                [1.0 + 0.5j, 0.25 - 0.75j],
                [-0.5 + 0.25j, 1.5 + 0.5j],
            ],
        ],
        dtype=np.complex128,
    )
    x = np.array(
        [
            [1.0 + 1.0j, 2.0 - 1.0j],
            [2.0, -0.5],
            [0.5 + 1.0j, -1.25 + 0.75j],
        ],
        dtype=np.complex128,
    )
    y = np.einsum("nij,nj->ni", H, x)

    estimates, statuses = zf_detect_batch(H, y)

    assert estimates.shape == (3, 2)
    assert statuses.shape == (3,)
    assert statuses.tolist() == [OK, OK, OK]
    assert_recovered(estimates, x)


def test_batch_reports_failure_per_pair_without_losing_valid_pairs():
    H = np.array(
        [
            [[1.0, 0.0], [0.0, 1.0]],
            [[0.0, 0.0], [0.0, 0.0]],
            [[1.0, 1.0], [1.0, 1.0 + 1e-14]],
        ],
        dtype=np.complex128,
    )
    x = np.array(
        [[1.0 + 2.0j, -1.0j], [2.0, 3.0], [1.0, 2.0]],
        dtype=np.complex128,
    )
    y = np.einsum("nij,nj->ni", H, x)

    estimates, statuses = zf_detect_batch(H, y)

    assert statuses.tolist() == [OK, SINGULAR_CHANNEL, NEAR_SINGULAR_CHANNEL]
    assert_recovered(estimates[0], x[0])
    assert np.isnan(estimates[1].real).all()
    assert np.isnan(estimates[1].imag).all()
    assert np.isnan(estimates[2].real).all()
    assert np.isnan(estimates[2].imag).all()


def test_batch_shape_mismatch_returns_batch_level_error():
    H = np.zeros((3, 2, 2), dtype=np.complex128)
    y = np.zeros((2, 2), dtype=np.complex128)

    estimates, statuses = zf_detect_batch(H, y)

    assert estimates.shape == (0, 2)
    assert statuses.tolist() == [INVALID_SHAPE]


def test_empty_batch_returns_empty_outputs():
    H = np.empty((0, 2, 2), dtype=np.complex128)
    y = np.empty((0, 2), dtype=np.complex128)

    estimates, statuses = zf_detect_batch(H, y)

    assert estimates.shape == (0, 2)
    assert statuses.shape == (0,)


def test_noisy_received_samples_produce_finite_estimate():
    H = np.array(
        [[1.0 + 0.25j, 0.2 - 0.1j], [-0.3 + 0.4j, 1.2 + 0.5j]],
        dtype=np.complex128,
    )
    x = np.array([1.0 + 1.0j, -0.5 + 0.25j])
    noise = np.array([1e-3 - 2e-3j, -1.5e-3 + 0.5e-3j])
    y = H @ x + noise

    estimate, status = zf_detect_single(H, y)

    assert status == OK
    assert np.isfinite(estimate.real).all()
    assert np.isfinite(estimate.imag).all()
    # Noise is expected to perturb the estimate; exact recovery is not required.
    assert np.linalg.norm(estimate - x) > 0.0


def test_numerical_failure_status_is_defined():
    # This checks that the public status exists for the C/Python API contract.
    assert NUMERICAL_FAILURE == "NUMERICAL_FAILURE"


def test_finite_components_with_unrepresentable_magnitude_report_numerical_failure():
    huge = complex(1.7e308, 1.7e308)
    H = np.full((2, 2), huge, dtype=np.complex128)
    y = np.array([1.0 + 0.0j, 2.0 + 0.0j])

    assert np.isfinite(H.real).all()
    assert np.isfinite(H.imag).all()

    estimate, status = zf_detect_single(H, y)

    assert status == NUMERICAL_FAILURE
    assert np.isnan(estimate.real).all()
    assert np.isnan(estimate.imag).all()
