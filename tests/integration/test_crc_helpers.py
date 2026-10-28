"""Tests for CRC24A integration helpers."""

import pytest

from integration.crc_helpers import (
    append_crc24a,
    check_crc24a,
    crc_to_bits,
)
from kernels.kernel1_crc24a.crc24a_reference import crc24a


def test_crc_to_bits_returns_24_msb_first_bits():
    bits = crc_to_bits(0xCDE703)

    assert len(bits) == 24
    assert bits == [
        (0xCDE703 >> shift) & 1
        for shift in range(23, -1, -1)
    ]


def test_append_crc24a_preserves_payload_and_adds_24_bits():
    payload = [1, 0, 1, 1, 0, 0, 1, 0] * 5

    codeword = append_crc24a(payload)

    assert codeword[:len(payload)] == payload
    assert len(codeword) == len(payload) + 24
    assert codeword[-24:] == crc_to_bits(crc24a(payload))


def test_appended_crc_passes_check():
    payload = [1, 0, 1, 1, 0, 0, 1, 0] * 7

    codeword = append_crc24a(payload)

    assert check_crc24a(codeword)


def test_modified_payload_fails_check():
    codeword = append_crc24a([1, 0, 1, 1, 0, 0, 1, 0] * 7)
    codeword[0] ^= 1

    assert not check_crc24a(codeword)


def test_too_short_codeword_fails_check():
    assert not check_crc24a([1, 0, 1])


def test_invalid_bits_fail_crc_check():
    assert not check_crc24a([0, 1, 2, 0])


@pytest.mark.parametrize("value", [-1, 1 << 24, True, 1.5])
def test_crc_to_bits_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        crc_to_bits(value)
