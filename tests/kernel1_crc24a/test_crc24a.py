from kernels.kernel1_crc24a.crc24a_reference import crc24a


def bytes_to_bits(data):
    """Convert bytes to bits, MSB first."""

    bits = []

    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    return bits


def test_crc24a_123456789():
    data = b"123456789"
    bits = bytes_to_bits(data)

    result = crc24a(bits)

    assert result == 0xCDE703
