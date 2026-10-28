
"""End-to-end simplified 2x2 MIMO PHY simulation."""

import numpy as np

from integration.channel import apply_mimo_channel
from integration.rx_chain.bit_processing import receive_bits
from integration.rx_chain.channel_estimator import estimate_mimo_channel
from integration.rx_chain.mimo_detector import detect_mimo_symbols
from integration.rx_chain.ofdm_receiver import demodulate_waveforms
from integration.tx_chain.bit_processing import transmit_bits
from integration.tx_chain.ofdm_transmitter import modulate_resource_grid
from integration.tx_chain.resource_grid import build_mimo_resource_grid


def simulate_mimo_link(
    payloads: list[list[int]],
    channel_matrix: np.ndarray,
    n_rnti: int = 0x1234,
    n_id: int = 0x155,
    modulation: str = "QPSK",
    q: int = 0,
    fft_size: int = 64,
    cp_length: int = 16,
    num_ofdm_symbols: int = 3,
    noise_variance: float = 0.0,
    rng: np.random.Generator | None = None,
) -> dict[str, object]:
    """Transmit two payloads through a flat-fading 2x2 MIMO link.

    This is a simplified educational link simulation, not a complete
    standards-compliant 5G NR physical-layer implementation.
    """
    if len(payloads) != 2:
        raise ValueError("payloads must contain exactly two payload bit lists")

    if not isinstance(fft_size, int) or isinstance(fft_size, bool):
        raise ValueError("fft_size must be an integer")
    if not isinstance(num_ofdm_symbols, int) or isinstance(num_ofdm_symbols, bool):
        raise ValueError("num_ofdm_symbols must be an integer")

    # Transmitter: CRC -> scrambling -> QAM mapping.
    codewords = []
    scrambled_streams = []
    symbol_streams = []

    for payload in payloads:
        codeword, scrambled, symbols = transmit_bits(
            payload_bits=payload,
            n_rnti=n_rnti,
            n_id=n_id,
            modulation=modulation,
            q=q,
        )
        codewords.append(codeword)
        scrambled_streams.append(scrambled)
        symbol_streams.append(symbols)

    if len(symbol_streams[0]) != len(symbol_streams[1]):
        raise ValueError("Both payloads must produce equal symbol counts")

    # The current resource grid uses a fixed capacity. To avoid treating
    # padding as real data, this first version requires full data capacity.
    data_bins_count = len(range(2, fft_size, 2))
    data_capacity = data_bins_count * (num_ofdm_symbols - 2)

    if len(symbol_streams[0]) != data_capacity:
        raise ValueError(
            "Each payload must map to exactly the available data-symbol "
            f"capacity ({data_capacity} symbols); got "
            f"{len(symbol_streams[0])} and {len(symbol_streams[1])}. "
            "For QPSK with fft_size=64 and num_ofdm_symbols=3, use "
            "38 payload bits per stream (24 CRC bits are added)."
        )

    resource_grid, pilot_bins, data_bins = build_mimo_resource_grid(
        data_symbols=symbol_streams,
        fft_size=fft_size,
        num_ofdm_symbols=num_ofdm_symbols,
    )

    tx_waveforms = modulate_resource_grid(
        resource_grid,
        cp_length=cp_length,
    )

    # Channel: static 2x2 flat fading with optional complex AWGN.
    rx_waveforms = apply_mimo_channel(
        tx_waveforms=tx_waveforms,
        channel_matrix=channel_matrix,
        noise_variance=noise_variance,
        rng=rng,
    )

    # Receiver: CP removal -> FFT -> pilot channel estimation -> ZF.
    received_grid = demodulate_waveforms(
        rx_waveforms=rx_waveforms,
        fft_size=fft_size,
        cp_length=cp_length,
    )

    channel_estimates = estimate_mimo_channel(
        received_grid=received_grid,
        pilot_bins=pilot_bins,
        data_bins=data_bins,
    )

    detected_symbols = detect_mimo_symbols(
        received_grid=received_grid,
        channel_estimates=channel_estimates,
        data_bins=data_bins,
        first_data_symbol=2,
    )

    receiver_results = receive_bits(
        detected_symbols=detected_symbols,
        n_rnti=n_rnti,
        n_id=n_id,
        modulation=modulation,
        q=q,
    )

    return {
        "transmitted_payloads": [list(payload) for payload in payloads],
        "transmitted_codewords": codewords,
        "transmitted_scrambled_bits": scrambled_streams,
        "transmitted_symbols": symbol_streams,
        "received_grid": received_grid,
        "channel_estimates": channel_estimates,
        "detected_symbols": detected_symbols,
        "receiver_results": receiver_results,
        "recovered_payloads": [
            result["payload_bits"] for result in receiver_results
        ],
        "crc_valid": [
            result["crc_valid"] for result in receiver_results
        ],
    }
