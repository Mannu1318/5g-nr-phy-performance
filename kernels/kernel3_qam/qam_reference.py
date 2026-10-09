"""
5G NR QPSK reference mapper and demapper.

This module is the first stage of Kernel 3:
QAM Mapping and Demapping.
"""

import math


QPSK = 4


def qpsk_map(bits):
    """
    Map binary bits to normalized QPSK symbols.

    Two input bits produce one complex symbol.

    Mapping:

        00 -> (+1 + j)/sqrt(2)
        01 -> (+1 - j)/sqrt(2)
        10 -> (-1 + j)/sqrt(2)
        11 -> (-1 - j)/sqrt(2)
    """

    if len(bits) % 2 != 0:
        raise ValueError("QPSK input length must be even")

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Input bits must contain only 0 or 1")

    normalization = 1.0 / math.sqrt(2.0)

    symbols = []

    for i in range(0, len(bits), 2):
        b0 = bits[i]
        b1 = bits[i + 1]

        i_component = 1 - 2 * b0
        q_component = 1 - 2 * b1

        symbol = complex(
            i_component * normalization,
            q_component * normalization,
        )

        symbols.append(symbol)

    return symbols


def qpsk_demap(symbols):
    """
    Hard-decision QPSK demapper.

    Determines the bit value from the sign of
    the I and Q components.
    """

    bits = []

    for symbol in symbols:

        if symbol.real >= 0:
            b0 = 0
        else:
            b0 = 1

        if symbol.imag >= 0:
            b1 = 0
        else:
            b1 = 1

        bits.append(b0)
        bits.append(b1)

    return bits

def qam16_map(bits):
    """
    Map binary bits to normalized 16-QAM symbols.

    Four input bits produce one complex symbol.
    """

    if len(bits) % 4 != 0:
        raise ValueError("16-QAM input length must be divisible by 4")

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Input bits must contain only 0 or 1")

    normalization = 1.0 / math.sqrt(10.0)

    symbols = []

    for i in range(0, len(bits), 4):

        b0 = bits[i]
        b1 = bits[i + 1]
        b2 = bits[i + 2]
        b3 = bits[i + 3]

        if b0 == 0 and b2 == 0:
            i_level = 3
        elif b0 == 0 and b2 == 1:
            i_level = 1
        elif b0 == 1 and b2 == 0:
            i_level = -3
        else:
            i_level = -1

        if b1 == 0 and b3 == 0:
            q_level = 3
        elif b1 == 0 and b3 == 1:
            q_level = 1
        elif b1 == 1 and b3 == 0:
            q_level = -3
        else:
            q_level = -1

        symbol = complex(
            i_level * normalization,
            q_level * normalization,
        )

        symbols.append(symbol)

    return symbols

def qam16_demap(symbols):
    """
    Hard-decision 16-QAM demapper.

    Converts each received complex symbol
    back into four binary bits.
    """

    normalization = 1.0 / math.sqrt(10.0)

    bits = []

    for symbol in symbols:

        # Remove the 16-QAM normalization.
        i_value = symbol.real / normalization
        q_value = symbol.imag / normalization

        # Recover the two I bits.
        if i_value >= 2:
            i_bits = [0, 0]
        elif i_value >= 0:
            i_bits = [0, 1]
        elif i_value >= -2:
            i_bits = [1, 1]
        else:
            i_bits = [1, 0]

        # Recover the two Q bits.
        if q_value >= 2:
            q_bits = [0, 0]
        elif q_value >= 0:
            q_bits = [0, 1]
        elif q_value >= -2:
            q_bits = [1, 1]
        else:
            q_bits = [1, 0]

        # Reconstruct the original bit order:
        # b0, b1, b2, b3
        bits.extend([
            i_bits[0],
            q_bits[0],
            i_bits[1],
            q_bits[1],
        ])

    return bits

def qam64_map(bits):
    """
    Map binary bits to normalized 64-QAM symbols.

    Six input bits produce one complex symbol.

    Bit arrangement:

        I -> b0, b2, b4
        Q -> b1, b3, b5

    Amplitude mapping:

        000 -> +7
        001 -> +5
        010 -> +3
        011 -> +1
        100 -> -7
        101 -> -5
        110 -> -3
        111 -> -1

    Normalization:

        1 / sqrt(42)
    """

    if len(bits) % 6 != 0:
        raise ValueError("64-QAM input length must be divisible by 6")

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Input bits must contain only 0 or 1")

    normalization = 1.0 / math.sqrt(42.0)

    symbols = []

    for i in range(0, len(bits), 6):

        b0 = bits[i]
        b1 = bits[i + 1]
        b2 = bits[i + 2]
        b3 = bits[i + 3]
        b4 = bits[i + 4]
        b5 = bits[i + 5]

        # I component: b0, b2, b4
        if b0 == 0 and b2 == 0 and b4 == 0:
            i_level = 7
        elif b0 == 0 and b2 == 0 and b4 == 1:
            i_level = 5
        elif b0 == 0 and b2 == 1 and b4 == 0:
            i_level = 3
        elif b0 == 0 and b2 == 1 and b4 == 1:
            i_level = 1
        elif b0 == 1 and b2 == 0 and b4 == 0:
            i_level = -7
        elif b0 == 1 and b2 == 0 and b4 == 1:
            i_level = -5
        elif b0 == 1 and b2 == 1 and b4 == 0:
            i_level = -3
        else:
            i_level = -1

        # Q component: b1, b3, b5
        if b1 == 0 and b3 == 0 and b5 == 0:
            q_level = 7
        elif b1 == 0 and b3 == 0 and b5 == 1:
            q_level = 5
        elif b1 == 0 and b3 == 1 and b5 == 0:
            q_level = 3
        elif b1 == 0 and b3 == 1 and b5 == 1:
            q_level = 1
        elif b1 == 1 and b3 == 0 and b5 == 0:
            q_level = -7
        elif b1 == 1 and b3 == 0 and b5 == 1:
            q_level = -5
        elif b1 == 1 and b3 == 1 and b5 == 0:
            q_level = -3
        else:
            q_level = -1

        symbol = complex(
            i_level * normalization,
            q_level * normalization,
        )

        symbols.append(symbol)

    return symbols

def qam64_demap(symbols):
    """
    Hard-decision 64-QAM demapper.

    Converts each received complex symbol
    back into six binary bits.
    """

    normalization = 1.0 / math.sqrt(42.0)

    bits = []

    for symbol in symbols:

        # Remove the 64-QAM normalization.
        i_value = symbol.real / normalization
        q_value = symbol.imag / normalization

        # Recover the three I bits.
        if i_value >= 6:
            i_bits = [0, 0, 0]
        elif i_value >= 4:
            i_bits = [0, 0, 1]
        elif i_value >= 2:
            i_bits = [0, 1, 0]
        elif i_value >= 0:
            i_bits = [0, 1, 1]
        elif i_value >= -2:
            i_bits = [1, 1, 1]
        elif i_value >= -4:
            i_bits = [1, 1, 0]
        elif i_value >= -6:
            i_bits = [1, 0, 1]
        else:
            i_bits = [1, 0, 0]

        # Recover the three Q bits.
        if q_value >= 6:
            q_bits = [0, 0, 0]
        elif q_value >= 4:
            q_bits = [0, 0, 1]
        elif q_value >= 2:
            q_bits = [0, 1, 0]
        elif q_value >= 0:
            q_bits = [0, 1, 1]
        elif q_value >= -2:
            q_bits = [1, 1, 1]
        elif q_value >= -4:
            q_bits = [1, 1, 0]
        elif q_value >= -6:
            q_bits = [1, 0, 1]
        else:
            q_bits = [1, 0, 0]

        # Reconstruct the original bit order:
        # b0, b1, b2, b3, b4, b5
        bits.extend([
            i_bits[0],
            q_bits[0],
            i_bits[1],
            q_bits[1],
            i_bits[2],
            q_bits[2],
        ])

    return bits

def qam256_map(bits):
    """
    Map binary bits to normalized 256-QAM symbols.

    Eight input bits produce one complex symbol.

    Bit arrangement:

        I -> b0, b2, b4, b6
        Q -> b1, b3, b5, b7

    Amplitude levels:

        -15, -13, -11, -9, -7, -5, -3, -1,
        +1, +3, +5, +7, +9, +11, +13, +15

    Normalization:

        1 / sqrt(170)
    """

    if len(bits) % 8 != 0:
        raise ValueError("256-QAM input length must be divisible by 8")

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("Input bits must contain only 0 or 1")

    normalization = 1.0 / math.sqrt(170.0)

    symbols = []

    for i in range(0, len(bits), 8):

        b0 = bits[i]
        b1 = bits[i + 1]
        b2 = bits[i + 2]
        b3 = bits[i + 3]
        b4 = bits[i + 4]
        b5 = bits[i + 5]
        b6 = bits[i + 6]
        b7 = bits[i + 7]

        # I component: b0, b2, b4, b6
        if b0 == 0 and b2 == 0 and b4 == 0 and b6 == 0:
            i_level = 15
        elif b0 == 0 and b2 == 0 and b4 == 0 and b6 == 1:
            i_level = 13
        elif b0 == 0 and b2 == 0 and b4 == 1 and b6 == 0:
            i_level = 11
        elif b0 == 0 and b2 == 0 and b4 == 1 and b6 == 1:
            i_level = 9
        elif b0 == 0 and b2 == 1 and b4 == 0 and b6 == 0:
            i_level = 7
        elif b0 == 0 and b2 == 1 and b4 == 0 and b6 == 1:
            i_level = 5
        elif b0 == 0 and b2 == 1 and b4 == 1 and b6 == 0:
            i_level = 3
        elif b0 == 0 and b2 == 1 and b4 == 1 and b6 == 1:
            i_level = 1
        elif b0 == 1 and b2 == 0 and b4 == 0 and b6 == 0:
            i_level = -15
        elif b0 == 1 and b2 == 0 and b4 == 0 and b6 == 1:
            i_level = -13
        elif b0 == 1 and b2 == 0 and b4 == 1 and b6 == 0:
            i_level = -11
        elif b0 == 1 and b2 == 0 and b4 == 1 and b6 == 1:
            i_level = -9
        elif b0 == 1 and b2 == 1 and b4 == 0 and b6 == 0:
            i_level = -7
        elif b0 == 1 and b2 == 1 and b4 == 0 and b6 == 1:
            i_level = -5
        elif b0 == 1 and b2 == 1 and b4 == 1 and b6 == 0:
            i_level = -3
        else:
            i_level = -1

        # Q component: b1, b3, b5, b7
        if b1 == 0 and b3 == 0 and b5 == 0 and b7 == 0:
            q_level = 15
        elif b1 == 0 and b3 == 0 and b5 == 0 and b7 == 1:
            q_level = 13
        elif b1 == 0 and b3 == 0 and b5 == 1 and b7 == 0:
            q_level = 11
        elif b1 == 0 and b3 == 0 and b5 == 1 and b7 == 1:
            q_level = 9
        elif b1 == 0 and b3 == 1 and b5 == 0 and b7 == 0:
            q_level = 7
        elif b1 == 0 and b3 == 1 and b5 == 0 and b7 == 1:
            q_level = 5
        elif b1 == 0 and b3 == 1 and b5 == 1 and b7 == 0:
            q_level = 3
        elif b1 == 0 and b3 == 1 and b5 == 1 and b7 == 1:
            q_level = 1
        elif b1 == 1 and b3 == 0 and b5 == 0 and b7 == 0:
            q_level = -15
        elif b1 == 1 and b3 == 0 and b5 == 0 and b7 == 1:
            q_level = -13
        elif b1 == 1 and b3 == 0 and b5 == 1 and b7 == 0:
            q_level = -11
        elif b1 == 1 and b3 == 0 and b5 == 1 and b7 == 1:
            q_level = -9
        elif b1 == 1 and b3 == 1 and b5 == 0 and b7 == 0:
            q_level = -7
        elif b1 == 1 and b3 == 1 and b5 == 0 and b7 == 1:
            q_level = -5
        elif b1 == 1 and b3 == 1 and b5 == 1 and b7 == 0:
            q_level = -3
        else:
            q_level = -1

        symbol = complex(
            i_level * normalization,
            q_level * normalization,
        )

        symbols.append(symbol)

    return symbols

def qam256_demap(symbols):
    """
    Hard-decision 256-QAM demapper.

    Converts each received complex symbol
    back into eight binary bits.
    """

    normalization = 1.0 / math.sqrt(170.0)

    bits = []

    for symbol in symbols:

        # Remove the 256-QAM normalization.
        i_value = symbol.real / normalization
        q_value = symbol.imag / normalization

        # Recover the four I bits.
        if i_value >= 14:
            i_bits = [0, 0, 0, 0]
        elif i_value >= 12:
            i_bits = [0, 0, 0, 1]
        elif i_value >= 10:
            i_bits = [0, 0, 1, 0]
        elif i_value >= 8:
            i_bits = [0, 0, 1, 1]
        elif i_value >= 6:
            i_bits = [0, 1, 0, 0]
        elif i_value >= 4:
            i_bits = [0, 1, 0, 1]
        elif i_value >= 2:
            i_bits = [0, 1, 1, 0]
        elif i_value >= 0:
            i_bits = [0, 1, 1, 1]
        elif i_value >= -2:
            i_bits = [1, 1, 1, 1]
        elif i_value >= -4:
            i_bits = [1, 1, 1, 0]
        elif i_value >= -6:
            i_bits = [1, 1, 0, 1]
        elif i_value >= -8:
            i_bits = [1, 1, 0, 0]
        elif i_value >= -10:
            i_bits = [1, 0, 1, 1]
        elif i_value >= -12:
            i_bits = [1, 0, 1, 0]
        elif i_value >= -14:
            i_bits = [1, 0, 0, 1]
        else:
            i_bits = [1, 0, 0, 0]

        # Recover the four Q bits.
        if q_value >= 14:
            q_bits = [0, 0, 0, 0]
        elif q_value >= 12:
            q_bits = [0, 0, 0, 1]
        elif q_value >= 10:
            q_bits = [0, 0, 1, 0]
        elif q_value >= 8:
            q_bits = [0, 0, 1, 1]
        elif q_value >= 6:
            q_bits = [0, 1, 0, 0]
        elif q_value >= 4:
            q_bits = [0, 1, 0, 1]
        elif q_value >= 2:
            q_bits = [0, 1, 1, 0]
        elif q_value >= 0:
            q_bits = [0, 1, 1, 1]
        elif q_value >= -2:
            q_bits = [1, 1, 1, 1]
        elif q_value >= -4:
            q_bits = [1, 1, 1, 0]
        elif q_value >= -6:
            q_bits = [1, 1, 0, 1]
        elif q_value >= -8:
            q_bits = [1, 1, 0, 0]
        elif q_value >= -10:
            q_bits = [1, 0, 1, 1]
        elif q_value >= -12:
            q_bits = [1, 0, 1, 0]
        elif q_value >= -14:
            q_bits = [1, 0, 0, 1]
        else:
            q_bits = [1, 0, 0, 0]

        # Reconstruct the original bit order:
        # b0, b1, b2, b3, b4, b5, b6, b7
        bits.extend([
            i_bits[0],
            q_bits[0],
            i_bits[1],
            q_bits[1],
            i_bits[2],
            q_bits[2],
            i_bits[3],
            q_bits[3],
        ])

    return bits



if __name__ == "__main__":

    test_bits = [
        0, 0,
        0, 1,
        1, 0,
        1, 1,
    ]

    symbols = qpsk_map(test_bits)
    recovered_bits = qpsk_demap(symbols)

    print("Input bits:")
    print(test_bits)

    print("\nQPSK symbols:")
    for symbol in symbols:
        print(symbol)

    print("\nRecovered bits:")
    print(recovered_bits)

    print("\nCorrect:", recovered_bits == test_bits)
if __name__ == "__main__":

    test_bits = [
        0, 0, 0, 0,
        0, 0, 0, 1,
        0, 0, 1, 0,
        0, 0, 1, 1,
    ]

    symbols = qam16_map(test_bits)

    print("Input bits:")
    print(test_bits)

    print("\n16-QAM symbols:")
    for symbol in symbols:
        print(symbol)
if __name__ == "__main__":

    test_bits = [
        0, 0, 0, 0,
        0, 0, 0, 1,
        0, 0, 1, 0,
        0, 0, 1, 1,
        0, 1, 0, 0,
        0, 1, 0, 1,
        0, 1, 1, 0,
        0, 1, 1, 1,
        1, 0, 0, 0,
        1, 0, 0, 1,
        1, 0, 1, 0,
        1, 0, 1, 1,
        1, 1, 0, 0,
        1, 1, 0, 1,
        1, 1, 1, 0,
        1, 1, 1, 1,
    ]

    symbols = qam16_map(test_bits)

    recovered_bits = qam16_demap(symbols)

    print("Input bits:")
    print(test_bits)

    print("\n16-QAM symbols:")
    for symbol in symbols:
        print(symbol)

    print("\nRecovered bits:")
    print(recovered_bits)

    print("\nCorrect:", recovered_bits == test_bits)
if __name__ == "__main__":

    test_bits = [
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 1,
        0, 0, 1, 0, 0, 0,
        1, 1, 1, 1, 1, 1,
    ]

    symbols = qam64_map(test_bits)

    print("Input bits:")
    print(test_bits)

    print("\n64-QAM symbols:")
    for symbol in symbols:
        print(symbol)
if __name__ == "__main__":

    test_bits = []

    for value in range(64):
        test_bits.extend([
            (value >> 5) & 1,
            (value >> 4) & 1,
            (value >> 3) & 1,
            (value >> 2) & 1,
            (value >> 1) & 1,
            value & 1,
        ])

    symbols = qam64_map(test_bits)
    recovered_bits = qam64_demap(symbols)

    print("Input bits:")
    print(test_bits)

    print("\nNumber of symbols:")
    print(len(symbols))

    print("\nRecovered bits:")
    print(recovered_bits)

    print("\nCorrect:", recovered_bits == test_bits)
