"""Tests for modulation helpers used in PHY integration."""

import pytest

from integration.modulation_helpers import (
    get_bits_per_symbol,
    modulate_bits,
    demodulate_symbols,
)


@pytest.mark.parametrize(
    ("modulation", "bits_per_symbol"),
    [
        ("QPSK", 2),
        ("16QAM", 4),
        ("64QAM", 6),
        ("256QAM", 8),
    ],
)
def test_get_bits_per_symbol(modulation, bits_per_symbol):
    assert get_bits_per_symbol(modulation) == bits_per_symbol


@pytest.mark.parametrize(
    ("modulation", "bits"),
    [
        ("QPSK", [0, 0, 0, 1, 1, 0, 1, 1]),
        ("16QAM", [0, 0, 0, 1, 1, 0, 1, 1]),
        ("64QAM", [0, 0, 0, 1, 1, 0]),
        ("256QAM", [0, 0, 0, 1, 1, 0, 1, 1]),
    ],
)
def test_noise_free_modulation_round_trip(modulation, bits):
    symbols = modulate_bits(bits, modulation)
    recovered_bits = demodulate_symbols(symbols, modulation)

    assert recovered_bits == bits


@pytest.mark.parametrize(
    ("modulation", "bits"),
    [
        ("QPSK", [0]),
        ("16QAM", [0, 1]),
        ("64QAM", [0, 1, 0, 1]),
        ("256QAM", [0, 1, 0, 1, 0, 1]),
    ],
)
def test_rejects_invalid_bit_count(modulation, bits):
    with pytest.raises(ValueError):
        modulate_bits(bits, modulation)


def test_rejects_unsupported_modulation():
    with pytest.raises(ValueError):
        modulate_bits([0, 1], "BPSK")


def test_rejects_unsupported_modulation_for_demap():
    with pytest.raises(ValueError):
        demodulate_symbols([], "BPSK")


def test_modulation_name_is_case_insensitive():
    bits = [0, 0, 0, 1]

    symbols = modulate_bits(bits, "qpsk")

    assert demodulate_symbols(symbols, "QPSK") == bits
