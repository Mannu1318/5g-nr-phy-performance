import numpy as np
import pytest

from integration.channel_profiles import build_multipath_profile


def test_profile_shape_and_delay_placement():
    taps, metadata = build_multipath_profile(
        delays_samples=[0, 2, 5],
        tap_powers_db=[0, -3, -6],
        seed=123,
    )

    assert taps.shape == (6, 2, 2)
    assert taps.dtype == np.complex128
    assert np.any(taps[0] != 0)
    assert np.all(taps[1] == 0)
    assert np.any(taps[2] != 0)
    assert np.all(taps[3:5] == 0)
    assert np.any(taps[5] != 0)
    assert metadata["delays_samples"] == [0, 2, 5]
    assert metadata["num_tap_slots"] == 6


def test_profile_is_reproducible_for_same_seed():
    first, first_metadata = build_multipath_profile(
        [0, 2, 4], [0, -3, -8], seed=42
    )
    second, second_metadata = build_multipath_profile(
        [0, 2, 4], [0, -3, -8], seed=42
    )

    np.testing.assert_array_equal(first, second)
    assert first_metadata == second_metadata


def test_different_seeds_produce_different_profiles():
    first, _ = build_multipath_profile([0, 1], [0, -3], seed=1)
    second, _ = build_multipath_profile([0, 1], [0, -3], seed=2)

    assert not np.array_equal(first, second)


def test_normalized_configured_powers_sum_to_one():
    _, metadata = build_multipath_profile(
        [0, 1, 3], [0, -3, -8], seed=7, normalize_power=True
    )

    assert sum(metadata["configured_tap_powers"]) == pytest.approx(1.0)
    assert metadata["normalize_power"] is True


def test_unnormalized_powers_are_relative_to_strongest_tap():
    _, metadata = build_multipath_profile(
        [0, 1, 2], [0, -10, -20], seed=7, normalize_power=False
    )

    np.testing.assert_allclose(
        metadata["configured_tap_powers"],
        [1.0, 0.1, 0.01],
        rtol=1e-12,
    )
    assert metadata["total_configured_power"] == pytest.approx(1.11)
    assert metadata["normalize_power"] is False


def test_single_tap_at_nonzero_delay_has_leading_zero_slots():
    taps, metadata = build_multipath_profile(
        [3], [0], seed=5
    )

    assert taps.shape == (4, 2, 2)
    assert np.all(taps[:3] == 0)
    assert np.any(taps[3] != 0)
    assert metadata["delays_samples"] == [3]


def test_global_numpy_random_state_is_not_modified():
    np.random.seed(9876)
    expected_first = np.random.random()
    expected_second = np.random.random()

    np.random.seed(9876)
    actual_first = np.random.random()
    build_multipath_profile([0, 2], [0, -4], seed=11)
    actual_second = np.random.random()

    assert actual_first == expected_first
    assert actual_second == expected_second


def test_input_sequences_are_not_modified():
    delays = [0, 2, 4]
    powers = [0.0, -3.0, -8.0]
    original_delays = delays.copy()
    original_powers = powers.copy()

    build_multipath_profile(delays, powers, seed=3)

    assert delays == original_delays
    assert powers == original_powers


@pytest.mark.parametrize(
    ("delays", "powers", "seed", "normalize"),
    [
        ([], [], 1, True),
        ([[0, 1]], [0, -3], 1, True),
        ([0, 1], [0], 1, True),
        ([0, True], [0, -3], 1, True),
        ([0, 1.5], [0, -3], 1, True),
        ([-1], [0], 1, True),
        ([1, 1], [0, -3], 1, True),
        ([2, 1], [0, -3], 1, True),
        ([0], [np.nan], 1, True),
        ([0], [np.inf], 1, True),
        ([0], [1 + 0j], 1, True),
        ([0], [True], 1, True),
        ([0], [0], -1, True),
        ([0], [0], True, True),
        ([0], [0], 1.5, True),
        ([0], [0], 1, 1),
    ],
)
def test_invalid_inputs_raise_value_error(delays, powers, seed, normalize):
    with pytest.raises(ValueError):
        build_multipath_profile(
            delays,
            powers,
            seed=seed,
            normalize_power=normalize,
        )


def test_metadata_reports_realized_energy_for_each_configured_tap():
    taps, metadata = build_multipath_profile(
        [0, 2], [0, -3], seed=15
    )

    expected = [
        float(np.sum(np.abs(taps[delay]) ** 2))
        for delay in [0, 2]
    ]
    np.testing.assert_allclose(
        metadata["realized_tap_energies"], expected
    )
    assert metadata["total_realized_energy"] == pytest.approx(
        float(np.sum(np.abs(taps) ** 2))
    )
