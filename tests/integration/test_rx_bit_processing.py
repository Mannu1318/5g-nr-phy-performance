"""Tests for integrated receiver bit processing."""

import numpy as np
import pytest

from integration.crc_helpers import append_crc24a
from integration.modulation_helpers import modulate_bits
from integration.rx_chain.bit_processing import receive_bits
from kernels.kernel2_scrambling.scrambling_reference import scramble_bits


@pytest.mark.parametrize("stream_index", [0, 1])
def test_recovers_payload_and_valid_crc(stream_index):
    payload = [
        (index * 7 + stream_index) % 2
        for index in range(40)
    ]
    codeword = append_crc24a(payload)

    scrambled = scramble_bits(
        bits=codeword,
        n_rnti=0x1234,
        n_id=0x155,
        q=0,
    )
    symbols = modulate_bits(scrambled, "QPSK")

    # Fill the selected stream; the other stream is independent.
    detected = np.zeros((2, 1, len(symbols)), dtype=np.complex128)
    detected[stream_index, 0, :] = symbols

    results = receive_bits(
        detected_symbols=detected,
        n_rnti=0x1234,
        n_id=0x155,
        modulation="QPSK",
        q=0,
    )

    assert results[stream_index]["payload_bits"] == payload
    assert results[stream_index]["crc_valid"] is True


def test_rejects_invalid_detected_symbol_shape():
    with pytest.raises(ValueError, match="detected_symbols"):
        receive_bits(
            detected_symbols=np.zeros((1, 1, 32), dtype=np.complex128),
            n_rnti=0x1234,
            n_id=0x155,
        )


def test_rejects_nonfinite_detected_symbols():
    detected = np.zeros((2, 1, 32), dtype=np.complex128)
    detected[0, 0, 0] = complex(np.nan, 0.0)

    with pytest.raises(ValueError, match="finite"):
        receive_bits(
            detected_symbols=detected,
            n_rnti=0x1234,
            n_id=0x155,
        )
