"""Receiver bit processing for the simplified PHY integration."""

from numpy.typing import NDArray
import numpy as np

from integration.crc_helpers import check_crc24a
from integration.modulation_helpers import demodulate_symbols
from kernels.kernel2_scrambling.scrambling_reference import scramble_bits


def receive_bits(
    detected_symbols: NDArray[np.complexfloating],
    n_rnti: int,
    n_id: int,
    modulation: str = "QPSK",
    q: int = 0,
) -> list[dict[str, object]]:
    """Demap, descramble, and verify CRC for two detected MIMO streams.

    Args:
        detected_symbols:
            Array shaped (2, num_data_symbols, num_data_bins).
            Each stream contains symbols in transmitter ordering.
        n_rnti: PDSCH RNTI used by the transmitter.
        n_id: Scrambling identity used by the transmitter.
        modulation: Modulation scheme, such as QPSK.
        q: Codeword index used for scrambling.

    Returns:
        One result dictionary per stream, containing descrambled bits,
        recovered payload bits, and CRC status.

    Note:
        The payload length is inferred from the recovered codeword length.
        CRC24A occupies the final 24 bits.
    """
    symbols = np.asarray(detected_symbols, dtype=np.complex128)

    if symbols.ndim != 3 or symbols.shape[0] != 2:
        raise ValueError(
            "detected_symbols must have shape "
            "(2, num_data_symbols, num_data_bins)"
        )

    if not np.all(np.isfinite(symbols)):
        raise ValueError("detected_symbols must contain only finite values")

    results: list[dict[str, object]] = []

    for stream_index in range(2):
        stream_symbols = symbols[stream_index].reshape(-1).tolist()

        scrambled_bits = demodulate_symbols(
            stream_symbols,
            modulation,
        )

        # PDSCH scrambling is XOR-based, so the same operation reverses it.
        codeword_bits = scramble_bits(
            bits=scrambled_bits,
            n_rnti=n_rnti,
            n_id=n_id,
            q=q,
        )

        if len(codeword_bits) < 24:
            raise ValueError(
                "Recovered codeword must contain at least 24 CRC bits"
            )

        payload_bits = codeword_bits[:-24]
        crc_valid = check_crc24a(codeword_bits)

        results.append(
            {
                "stream_index": stream_index,
                "payload_bits": payload_bits,
                "codeword_bits": codeword_bits,
                "crc_valid": crc_valid,
            }
        )

    return results
