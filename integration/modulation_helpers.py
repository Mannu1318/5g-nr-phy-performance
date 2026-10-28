"""Modulation and demodulation helpers for PHY integration."""

from kernels.kernel3_qam.qam_reference import (
    qpsk_map,
    qpsk_demap,
    qam16_map,
    qam16_demap,
    qam64_map,
    qam64_demap,
    qam256_map,
    qam256_demap,
)


_MODULATION_FUNCTIONS = {
    "QPSK": (qpsk_map, qpsk_demap, 2),
    "16QAM": (qam16_map, qam16_demap, 4),
    "64QAM": (qam64_map, qam64_demap, 6),
    "256QAM": (qam256_map, qam256_demap, 8),
}


def get_bits_per_symbol(modulation: str) -> int:
    """Return the number of bits per symbol for a modulation scheme."""
    try:
        return _MODULATION_FUNCTIONS[modulation.upper()][2]
    except (AttributeError, KeyError):
        raise ValueError(
            f"Unsupported modulation: {modulation!r}. "
            f"Choose one of {', '.join(_MODULATION_FUNCTIONS)}."
        ) from None


def modulate_bits(bits: list[int], modulation: str) -> list[complex]:
    """Map bits to complex symbols using an existing QAM kernel."""
    try:
        mapper = _MODULATION_FUNCTIONS[modulation.upper()][0]
    except (AttributeError, KeyError):
        raise ValueError(f"Unsupported modulation: {modulation!r}.") from None

    if len(bits) % get_bits_per_symbol(modulation) != 0:
        raise ValueError(
            f"Bit count must be divisible by "
            f"{get_bits_per_symbol(modulation)} for {modulation.upper()}."
        )

    return mapper(bits)


def demodulate_symbols(
    symbols: list[complex],
    modulation: str,
) -> list[int]:
    """Hard-decision demodulation using an existing QAM kernel."""
    try:
        demapper = _MODULATION_FUNCTIONS[modulation.upper()][1]
    except (AttributeError, KeyError):
        raise ValueError(f"Unsupported modulation: {modulation!r}.") from None

    return demapper(symbols)
