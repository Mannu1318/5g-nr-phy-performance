"""CRC24A helpers for the end-to-end PHY integration."""

from kernels.kernel1_crc24a.crc24a_reference import (
    CRC24A_WIDTH,
    crc24a,
)


def crc_to_bits(crc_value: int) -> list[int]:
    """Convert a CRC integer to bits, most-significant bit first."""
    if not isinstance(crc_value, int) or isinstance(crc_value, bool):
        raise ValueError("CRC value must be an integer.")

    if not 0 <= crc_value < (1 << CRC24A_WIDTH):
        raise ValueError("CRC value does not fit in 24 bits.")

    return [
        (crc_value >> shift) & 1
        for shift in range(CRC24A_WIDTH - 1, -1, -1)
    ]


def append_crc24a(payload_bits: list[int]) -> list[int]:
    """Append CRC24A parity bits to a payload."""
    payload = list(payload_bits)
    crc_bits = crc_to_bits(crc24a(payload))
    return payload + crc_bits


def check_crc24a(codeword_bits: list[int]) -> bool:
    """Check whether a payload-plus-CRC bit sequence is valid."""
    codeword = list(codeword_bits)

    if len(codeword) < CRC24A_WIDTH:
        return False

    payload = codeword[:-CRC24A_WIDTH]
    received_crc_bits = codeword[-CRC24A_WIDTH:]

    if any(bit not in (0, 1) for bit in codeword):
        return False

    received_crc = 0
    for bit in received_crc_bits:
        received_crc = (received_crc << 1) | bit

    return crc24a(payload) == received_crc
