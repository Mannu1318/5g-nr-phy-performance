"""Tests for the Kernel 4 OFDM Python reference implementation."""

import numpy as np
import pytest

from kernels.kernel4_ofdm.ofdm_reference import (
    add_cyclic_prefix,
    extract_subcarriers,
    fft,
    ifft,
    map_subcarriers,
    remove_cyclic_prefix,
)


def test_fft_ifft_round_trip():
    samples = np.array(
        [1 + 2j, 3 - 1j, -2 + 0.5j, 4 + 0j],
        dtype=np.complex128,
    )

    recovered = ifft(fft(samples))

    np.testing.assert_allclose(recovered, samples, rtol=1e-12, atol=1e-12)


def test_fft_impulse_input():
    samples = np.array([1, 0, 0, 0], dtype=np.complex128)

    expected = np.ones(4, dtype=np.complex128)

    np.testing.assert_allclose(fft(samples), expected, atol=1e-12)


def test_ifft_constant_frequency_input():
    symbols = np.array([4, 0, 0, 0], dtype=np.complex128)

    expected = np.array([1, 1, 1, 1], dtype=np.complex128)

    np.testing.assert_allclose(ifft(symbols), expected, atol=1e-12)
@pytest.mark.parametrize("size", [64, 128, 256, 512, 1024, 2048])
def test_fft_ifft_supported_sizes(size):
    rng = np.random.default_rng(42)
    samples = (
        rng.standard_normal(size)
        + 1j * rng.standard_normal(size)
    )

    recovered = ifft(fft(samples))

    np.testing.assert_allclose(
        recovered,
        samples,
        rtol=1e-12,
        atol=1e-12,
    )
def test_map_subcarriers_places_symbols_in_correct_bins():
    symbols = np.array([1 + 2j, 3 - 1j, -2 + 0.5j])
    bins = [1, 4, 6]

    result = map_subcarriers(symbols, bins, fft_size=8)

    expected = np.zeros(8, dtype=np.complex128)
    expected[bins] = symbols

    np.testing.assert_array_equal(result, expected)


def test_map_and_extract_subcarriers_round_trip():
    symbols = np.array([1 + 2j, 3 - 1j, -2 + 0.5j])
    bins = [1, 4, 6]

    spectrum = map_subcarriers(symbols, bins, fft_size=8)
    recovered = extract_subcarriers(spectrum, bins)

    np.testing.assert_array_equal(recovered, symbols)


def test_map_subcarriers_leaves_unassigned_bins_zero():
    symbols = np.array([2 + 3j, 4 - 1j])

    result = map_subcarriers(symbols, [2, 5], fft_size=8)

    unassigned_bins = [0, 1, 3, 4, 6, 7]
    np.testing.assert_array_equal(
        result[unassigned_bins],
        np.zeros(len(unassigned_bins), dtype=np.complex128),
    )

def test_add_cyclic_prefix():
    samples = np.array([10, 20, 30, 40], dtype=np.complex128)

    result = add_cyclic_prefix(samples, cp_length=2)

    expected = np.array([30, 40, 10, 20, 30, 40], dtype=np.complex128)

    np.testing.assert_array_equal(result, expected)


def test_remove_cyclic_prefix():
    received = np.array([30, 40, 10, 20, 30, 40], dtype=np.complex128)

    result = remove_cyclic_prefix(
        received,
        cp_length=2,
        useful_length=4,
    )

    expected = np.array([10, 20, 30, 40], dtype=np.complex128)

    np.testing.assert_array_equal(result, expected)


def test_zero_length_cyclic_prefix():
    samples = np.array([1, 2, 3, 4], dtype=np.complex128)

    result = add_cyclic_prefix(samples, cp_length=0)

    np.testing.assert_array_equal(result, samples)


def test_cyclic_prefix_round_trip():
    samples = np.array([1 + 1j, 2 + 2j, 3 + 3j, 4 + 4j])

    with_prefix = add_cyclic_prefix(samples, cp_length=2)
    recovered = remove_cyclic_prefix(
        with_prefix,
        cp_length=2,
        useful_length=len(samples),
    )

    np.testing.assert_array_equal(recovered, samples)
def test_fft_rejects_empty_input():
    with pytest.raises(ValueError):
        fft([])


def test_ifft_rejects_empty_input():
    with pytest.raises(ValueError):
        ifft([])


def test_fft_rejects_multidimensional_input():
    with pytest.raises(ValueError):
        fft([[1, 2], [3, 4]])


def test_map_subcarriers_rejects_out_of_range_bins():
    with pytest.raises(ValueError):
        map_subcarriers([1 + 1j], [8], fft_size=8)


def test_map_subcarriers_rejects_duplicate_bins():
    with pytest.raises(ValueError):
        map_subcarriers([1 + 1j, 2 + 2j], [2, 2], fft_size=8)


def test_map_subcarriers_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        map_subcarriers([1 + 1j, 2 + 2j], [1], fft_size=8)


def test_add_cyclic_prefix_rejects_negative_length():
    with pytest.raises(ValueError):
        add_cyclic_prefix([1, 2, 3, 4], cp_length=-1)


def test_remove_cyclic_prefix_rejects_insufficient_samples():
    with pytest.raises(ValueError):
        remove_cyclic_prefix(
            [1, 2, 3],
            cp_length=2,
            useful_length=4,
        )
def test_map_subcarriers_rejects_zero_fft_size():
    with pytest.raises(ValueError):
        map_subcarriers([], [], fft_size=0)


def test_map_subcarriers_rejects_non_integer_fft_size():
    with pytest.raises(ValueError):
        map_subcarriers([], [], fft_size=8.5)


def test_map_subcarriers_rejects_multidimensional_bins():
    with pytest.raises(ValueError):
        map_subcarriers([1 + 1j, 2 + 2j], [[0, 1]], fft_size=8)


def test_map_subcarriers_rejects_non_integer_bins():
    with pytest.raises(ValueError):
        map_subcarriers([1 + 1j], [1.5], fft_size=8)


def test_extract_subcarriers_rejects_multidimensional_bins():
    with pytest.raises(ValueError):
        extract_subcarriers(np.zeros(8), [[1, 2]])


def test_extract_subcarriers_rejects_non_integer_bins():
    with pytest.raises(ValueError):
        extract_subcarriers(np.zeros(8), [1.5])


def test_extract_subcarriers_rejects_out_of_range_bins():
    with pytest.raises(ValueError):
        extract_subcarriers(np.zeros(8), [8])


def test_extract_subcarriers_rejects_duplicate_bins():
    with pytest.raises(ValueError):
        extract_subcarriers(np.zeros(8), [2, 2])
def test_add_cyclic_prefix_rejects_non_integer_length():
    with pytest.raises(ValueError):
        add_cyclic_prefix([1, 2, 3, 4], cp_length=1.5)


def test_add_cyclic_prefix_rejects_length_greater_than_symbol():
    with pytest.raises(ValueError):
        add_cyclic_prefix([1, 2, 3, 4], cp_length=5)


def test_remove_cyclic_prefix_rejects_non_integer_cp_length():
    with pytest.raises(ValueError):
        remove_cyclic_prefix([1, 2, 3, 4], cp_length=1.5, useful_length=2)


def test_remove_cyclic_prefix_rejects_non_integer_useful_length():
    with pytest.raises(ValueError):
        remove_cyclic_prefix([1, 2, 3, 4], cp_length=1, useful_length=2.5)


def test_remove_cyclic_prefix_rejects_negative_useful_length():
    with pytest.raises(ValueError):
        remove_cyclic_prefix([1, 2, 3, 4], cp_length=1, useful_length=-1)
def test_remove_cyclic_prefix_rejects_negative_cp_length():
    with pytest.raises(ValueError):
        remove_cyclic_prefix(
            [1, 2, 3, 4],
            cp_length=-1,
            useful_length=2,
        )
