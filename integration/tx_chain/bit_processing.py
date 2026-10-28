"""Transmitter bit processing for the simplified PHY integration."""

from integration.crc_helpers import append_crc24a
from integration.modulation_helpers import modulate_bits
from kernels.kernel2_scrambling.scrambling_reference import scramble_bits


def transmit_bits(
    payload_bits: list[int],
    n_rnti: int,
    n_id: int,
    modulation: str = "QPSK",
    q: int = 0,
) -> tuple[list[int], list[int], list[complex]]:
    """Append CRC, scramble the codeword, and map it to QAM symbols.

    Returns:
        codeword_bits: Payload followed by CRC24A bits.
        scrambled_bits: Scrambled codeword bits.
        symbols: Complex modulation symbols.
    """
    codeword_bits = append_crc24a(payload_bits)

    scrambled_bits = scramble_bits(
        bits=codeword_bits,
        n_rnti=n_rnti,
        n_id=n_id,
        q=q,
    )

    symbols = modulate_bits(scrambled_bits, modulation)

    return codeword_bits, scrambled_bits, symbols
