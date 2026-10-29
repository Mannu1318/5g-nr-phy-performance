import numpy as np
import pytest

from integration.experimental.delay_domain_channel_estimator import (
    estimate_channel_delay_domain,
    estimate_channel_delay_domain_diagnostics,
)


def make_channel_response(fft_size, channel_taps, indices):
    """Generate a frequency response using the negative-exponential convention."""
    indices = np.asarray(indices, dtype=np.float64)
    taps = np.asarray(channel_taps, dtype=np.complex128)
    delays = np.arange(taps.size, dtype=np.float64)

    matrix = np.exp(
        -2j * np.pi * np.outer(indices, delays) / fft_size
    )

    return np.asarray(matrix @ taps, dtype=np.complex128)


def make_pilot_observations(fft_size, channel_taps, pilot_indices, pilot_symbols):
    """Synthesize noiseless received pilot observations."""
    response = make_channel_response(
        fft_size, channel_taps, pilot_indices
    )
    return np.asarray(pilot_symbols, dtype=np.complex128) * response


def test_recovers_correctly_specified_channel_exactly():
    fft_size = 64
    pilot_indices = np.array([1, 5, 9, 13, 17, 21, 25, 29], dtype=np.int64)
    estimate_indices = np.arange(fft_size, dtype=np.int64)
    channel_taps = np.array(
        [1.0 + 0.2j, 0.3 - 0.1j, -0.15 + 0.25j],
        dtype=np.complex128,
    )
    pilot_symbols = np.ones(pilot_indices.size, dtype=np.complex128)

    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=2,
    )

    expected = make_channel_response(
        fft_size, channel_taps, estimate_indices
    )

    assert estimates.shape == (fft_size,)
    assert estimates.dtype == np.complex128
    np.testing.assert_allclose(estimates, expected, atol=1e-12, rtol=1e-12)


def test_uses_negative_exponential_fourier_convention():
    fft_size = 32
    pilot_indices = np.array([0, 3, 7, 12, 18, 24], dtype=np.int64)
    estimate_indices = np.array([2, 9, 17, 29], dtype=np.int64)
    channel_taps = np.array([1.0 + 0.5j, 0.2 - 0.3j], dtype=np.complex128)
    pilot_symbols = np.full(pilot_indices.size, 1.0 + 0.0j)

    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )

    expected = make_channel_response(
        fft_size, channel_taps, estimate_indices
    )

    np.testing.assert_allclose(estimates, expected, atol=1e-12, rtol=1e-12)


def test_supports_unsorted_pilot_and_estimate_indices():
    fft_size = 32
    pilot_indices = np.array([17, 1, 25, 9, 5, 21], dtype=np.int64)
    estimate_indices = np.array([20, 2, 31, 7], dtype=np.int64)
    channel_taps = np.array([0.8 + 0.1j, -0.2 + 0.4j], dtype=np.complex128)
    pilot_symbols = np.array(
        [1 + 0j, 0.5 + 0.5j, -1 + 0j, 1j, 1 + 0j, 0.5 - 0.5j],
        dtype=np.complex128,
    )

    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )

    expected = make_channel_response(
        fft_size, channel_taps, estimate_indices
    )

    np.testing.assert_allclose(estimates, expected, atol=1e-12, rtol=1e-12)


def test_duplicate_requested_indices_are_preserved():
    fft_size = 16
    pilot_indices = np.array([0, 2, 4, 6], dtype=np.int64)
    estimate_indices = np.array([3, 1, 3], dtype=np.int64)
    channel_taps = np.array([1.0 + 0j, 0.2j], dtype=np.complex128)
    pilot_symbols = np.ones(pilot_indices.size, dtype=np.complex128)
    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )

    assert estimates.shape == (3,)
    assert estimates[0] == pytest.approx(estimates[2], abs=1e-12)


def test_empty_estimate_indices_returns_empty_complex_vector():
    fft_size = 16
    pilot_indices = np.array([0, 2, 4], dtype=np.int64)
    channel_taps = np.array([1.0 + 0j], dtype=np.complex128)
    pilot_symbols = np.ones(3, dtype=np.complex128)
    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        [],
        fft_size,
        max_delay_samples=0,
    )

    assert estimates.shape == (0,)
    assert estimates.dtype == np.complex128


def test_empty_estimate_indices_does_not_require_identifiable_delay_model():
    estimates = estimate_channel_delay_domain(
        pilot_symbols=[1],
        received_pilots=[1],
        pilot_indices=[0],
        estimate_indices=[],
        fft_size=8,
        max_delay_samples=2,
    )

    assert estimates.shape == (0,)
    assert estimates.dtype == np.complex128


@pytest.mark.parametrize(
    ("pilots", "received", "pilot_indices", "estimate_indices", "fft_size", "max_delay"),
    [
        ([], [], [], [0], 8, 0),
        ([1, 1], [1], [0, 1], [0], 8, 0),
        ([0, 1], [1, 1], [0, 1], [0], 8, 0),
        ([1, 1], [1, 1], [0, 0], [0], 8, 0),
        ([1, 1], [1, 1], [-1, 1], [0], 8, 0),
        ([1, 1], [1, 1], [0, 8], [0], 8, 0),
        ([1, 1], [1, 1], [0, 1], [-1], 8, 0),
        ([1, 1], [1, 1], [0, 1], [8], 8, 0),
        ([1, 1], [1, 1], [0, 1], [0], 0, 0),
        ([1, 1], [1, 1], [0, 1], [0], 8, 8),
        ([1, 1], [1, 1], [0, 1], [0], 8, -1),
    ],
)



def test_invalid_inputs_raise_value_error(
    pilots, received, pilot_indices, estimate_indices, fft_size, max_delay
):
    with pytest.raises(ValueError):
        estimate_channel_delay_domain(
            pilots,
            received,
            pilot_indices,
            estimate_indices,
            fft_size,
            max_delay,
        )


def test_noninteger_indices_raise_type_error():
    with pytest.raises(TypeError):
        estimate_channel_delay_domain(
            [1, 1],
            [1, 1],
            [0.0, 1.0],
            [0],
            8,
            0,
        )


def test_boolean_fft_size_is_rejected():
    with pytest.raises(TypeError):
        estimate_channel_delay_domain(
            [1, 1],
            [1, 1],
            [0, 1],
            [0],
            True,
            0,
        )


def test_nonfinite_observations_are_rejected():
    with pytest.raises(ValueError):
        estimate_channel_delay_domain(
            [1, 1],
            [1, np.nan],
            [0, 1],
            [0],
            8,
            0,
        )


def test_underdetermined_model_is_rejected():
    with pytest.raises(ValueError, match="insufficient"):
        estimate_channel_delay_domain(
            [1, 1],
            [1, 1],
            [0, 1],
            [0],
            16,
            max_delay_samples=2,
        )


def test_diagnostics_match_main_estimator():
    fft_size = 32
    pilot_indices = np.array([0, 3, 6, 9, 12, 15], dtype=np.int64)
    estimate_indices = np.array([1, 7, 19], dtype=np.int64)
    channel_taps = np.array([1.0 + 0.2j, -0.3 + 0.1j], dtype=np.complex128)
    pilot_symbols = np.ones(pilot_indices.size, dtype=np.complex128)
    received_pilots = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )
    diagnostics = estimate_channel_delay_domain_diagnostics(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )

    np.testing.assert_allclose(
        diagnostics.frequency_response, estimates, atol=1e-12
    )
    np.testing.assert_allclose(
        diagnostics.channel_taps, channel_taps, atol=1e-12
    )
    assert diagnostics.residual_norm < 1e-12
    assert np.isfinite(diagnostics.condition_number)
    assert diagnostics.condition_number >= 1.0


def test_noisy_estimation_has_finite_results_and_positive_residual():
    rng = np.random.default_rng(20261029)
    fft_size = 64
    pilot_indices = np.arange(1, 32, 2, dtype=np.int64)
    estimate_indices = np.arange(fft_size, dtype=np.int64)
    channel_taps = np.array(
        [1.0 + 0.1j, 0.3 - 0.2j, -0.1 + 0.05j],
        dtype=np.complex128,
    )
    pilot_symbols = np.ones(pilot_indices.size, dtype=np.complex128)
    noiseless = make_pilot_observations(
        fft_size, channel_taps, pilot_indices, pilot_symbols
    )
    noise = 0.01 * (
        rng.standard_normal(pilot_indices.size)
        + 1j * rng.standard_normal(pilot_indices.size)
    )
    received_pilots = noiseless + noise

    diagnostics = estimate_channel_delay_domain_diagnostics(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=2,
    )

    assert np.all(np.isfinite(diagnostics.frequency_response))
    assert np.all(np.isfinite(diagnostics.channel_taps))
    assert diagnostics.residual_norm > 0.0

def test_rank_deficient_design_matrix_is_rejected(monkeypatch):
    """Verify the defensive rank check rejects a reported rank loss."""
    monkeypatch.setattr(
        np.linalg,
        "matrix_rank",
        lambda matrix: matrix.shape[1] - 1,
    )

    with pytest.raises(ValueError, match="rank-deficient"):
        estimate_channel_delay_domain(
            pilot_symbols=[1, 1, 1],
            received_pilots=[1, 1, 1],
            pilot_indices=[0, 1, 2],
            estimate_indices=[1, 2],
            fft_size=8,
            max_delay_samples=2,
        )

def test_too_short_delay_support_cannot_recover_full_channel():
    fft_size = 32
    pilot_indices = np.array([0, 2, 4, 6, 8, 10, 12, 14], dtype=np.int64)
    estimate_indices = np.arange(fft_size, dtype=np.int64)

    # The true channel has a tap at delay 2, but the model allows only delays 0 and 1.
    true_taps = np.array([1.0 + 0.0j, 0.2 + 0.1j, 0.6 - 0.2j])
    pilot_symbols = np.ones(pilot_indices.size, dtype=np.complex128)
    received_pilots = make_pilot_observations(
        fft_size, true_taps, pilot_indices, pilot_symbols
    )

    estimates = estimate_channel_delay_domain(
        pilot_symbols,
        received_pilots,
        pilot_indices,
        estimate_indices,
        fft_size,
        max_delay_samples=1,
    )
    true_response = make_channel_response(
        fft_size, true_taps, estimate_indices
    )

    # The fitted model is constrained to two taps and cannot exactly match
    # this three-tap response across all subcarriers.
    assert np.linalg.norm(estimates - true_response) > 1e-3
