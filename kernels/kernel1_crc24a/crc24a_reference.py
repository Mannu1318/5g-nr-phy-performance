"""Reference implementation of CRC24A for the 5G NR PHY study."""

CRC24A_POLY = 0x864CFB
CRC24A_WIDTH = 24
CRC24A_MASK = (1 << CRC24A_WIDTH) - 1

def crc24a(bits):
    """Compute CRC24A using systematic polynomial division."""

    bits = list(bits)

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Input bits must contain only 0 or 1.")

    # Append L zero bits for the systematic CRC calculation.
    work = bits + [0] * CRC24A_WIDTH

    # Generator polynomial including the leading x^24 term.
    generator = (1 << CRC24A_WIDTH) | CRC24A_POLY

    # Perform polynomial division over GF(2).
    for i in range(len(bits)):
        if work[i]:
            for j in range(CRC24A_WIDTH + 1):
                work[i + j] ^= (generator >> (CRC24A_WIDTH - j)) & 1

    # The final 24 bits are the CRC parity bits.
    crc = 0
    for bit in work[-CRC24A_WIDTH:]:
        crc = (crc << 1) | bit

    return crc

if __name__ == "__main__":
    data = b"123456789"

    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    result = crc24a(bits)

    print(f"CRC24A: 0x{result:06X}")
