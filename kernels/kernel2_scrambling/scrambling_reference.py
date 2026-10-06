"""
5G NR PDSCH bit scrambling reference implementation.

Reference:
    3GPP TS 38.211
    Section 5.2.1  - Pseudo-random sequence generation
    Section 7.3.1.1 - PDSCH scrambling

This implementation prioritizes readability and correctness.
It is intentionally not optimized for performance.
"""


# Number of bits used by the Gold-sequence initialization offset.
N_C = 1600


def generate_gold_sequence(length: int, c_init: int) -> list[int]:
    """
    Generate the 5G NR pseudo-random Gold sequence.

    Parameters
    ----------
    length : int
        Number of scrambling bits required.

    c_init : int
        Initialization value for the x2 m-sequence.

    Returns
    -------
    list[int]
        Generated scrambling sequence containing only 0 and 1.
    """

    if length < 0:
        raise ValueError("length must be non-negative")

    if c_init < 0 or c_init >= (1 << 31):
        raise ValueError("c_init must fit in 31 bits")

    total_length = N_C + length

    x1 = [0] * total_length
    x2 = [0] * total_length

    # Initialize x1.
    x1[0] = 1

    # Initialize x2 from c_init.
    for i in range(31):
        x2[i] = (c_init >> i) & 1

    # Generate x1 and x2.
    for n in range(total_length - 31):
        x1[n + 31] = x1[n + 3] ^ x1[n]

        x2[n + 31] = (
            x2[n + 3]
            ^ x2[n + 2]
            ^ x2[n + 1]
            ^ x2[n]
        )

    # Generate the Gold sequence after the N_C offset.
    sequence = [
        x1[n + N_C] ^ x2[n + N_C]
        for n in range(length)
    ]

    return sequence


def calculate_c_init(
    n_rnti: int,
    n_id: int,
    q: int = 0,
) -> int:
    """
    Calculate the PDSCH scrambling initialization value.

    c_init = n_RNTI * 2^15 + q * 2^14 + n_ID
    """

    if not 0 <= n_rnti <= 0xFFFF:
        raise ValueError("n_rnti must fit in 16 bits")

    if q not in (0, 1):
        raise ValueError("q must be 0 or 1")

    if not 0 <= n_id <= 1023:
        raise ValueError("n_id must be in the range 0..1023")

    return (
    (n_rnti << 15)
    + (q << 14)
    + n_id
)

def scramble_bits(
    bits: list[int],
    n_rnti: int,
    n_id: int,
    q: int = 0,
) -> list[int]:
    """
    Scramble a sequence of input bits using the 5G NR PDSCH
    scrambling procedure.
    """

    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("input bits must contain only 0 or 1")

    c_init = calculate_c_init(
        n_rnti=n_rnti,
        n_id=n_id,
        q=q,
    )

    scrambling_sequence = generate_gold_sequence(
        length=len(bits),
        c_init=c_init,
    )

    scrambled = [
        bit ^ c
        for bit, c in zip(bits, scrambling_sequence)
    ]

    return scrambled


def main() -> None:
    """
    Simple deterministic demonstration.
    """

    n_rnti = 0x1234
    n_id = 0x0155
    q = 0

    bits = [
        1, 0, 1, 1, 0, 0, 1, 0,
        1, 1, 0, 0, 1, 0, 1, 1,
    ]

    c_init = calculate_c_init(
        n_rnti=n_rnti,
        n_id=n_id,
        q=q,
    )

    scrambling_sequence = generate_gold_sequence(
        length=len(bits),
        c_init=c_init,
    )

    scrambled = scramble_bits(
        bits=bits,
        n_rnti=n_rnti,
        n_id=n_id,
        q=q,
    )

    print("5G NR PDSCH Scrambling Reference")
    print("--------------------------------")
    print(f"n_RNTI : 0x{n_rnti:04X}")
    print(f"n_ID   : 0x{n_id:04X}")
    print(f"q      : {q}")
    print(f"c_init : 0x{c_init:08X}")
    print()
    print("Input bits:")
    print(bits)
    print()
    print("Scrambling sequence:")
    print(scrambling_sequence)
    print()
    print("Scrambled bits:")
    print(scrambled)


if __name__ == "__main__":
    main()
