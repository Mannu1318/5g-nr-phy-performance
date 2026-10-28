"""Tests for transmitter bit processing."""

import pytest

from integration.tx_chain.bit_processing import transmit_bits
from integration.crc_helpers import check_crc24a
from integration.modulation_helpers import demodulate_symbols
from kernels.kernel2_scrambling.scrambling_reference import scramble_bits


@pytest.mark.parametrize(
    ("modulation", "payload_length"),
    [
        ("QPSK", 16),
        ("16QAM", 16),
        ("64QAM", 18),
        ("256QAM", 16),
    ],
)
def test_transmit_bits_round_trip(modulation, payload_length):
    payload = [i % 2 for i in range(payload_length)]

    codeword, scrambled, symbols = transmit_bits(
        payload_bits=payload,
        n_rnti=0x1234,
        n_id=0x0155,
        modulation=modulation,
    )

    assert codeword[:-24] == payload
    assert len(codeword) == len(payload) + 24
    assert check_crc24a(codeword)

    recovered_scrambled = demodulate_symbols(symbols, modulation)
    assert recovered_scrambled == scrambled

    recovered_codeword = scramble_bits(
        bits=recovered_scrambled,
        n_rnti=0x1234,
        n_id=0x0155,
    )
    assert recovered_codeword == codeword


def test_transmit_bits_returns_expected_number_of_symbols():
    payload = [0, 1] * 8

    codeword, scrambled, symbols = transmit_bits(
        payload_bits=payload,
        n_rnti=0x1234,
        n_id=0x0155,
        modulation="QPSK",
    )

    assert len(scrambled) == len(codeword)
    assert len(symbols) == len(scrambled) // 2


def test_transmit_bits_rejects_unsupported_modulation():
    with pytest.raises(ValueError):
        transmit_bits(
            payload_bits=[0, 1, 0, 1],
            n_rnti=0x1234,
            n_id=0x0155,
            modulation="BPSK",
        )
