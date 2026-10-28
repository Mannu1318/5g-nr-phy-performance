"""Flat-fading and static multipath 2x2 MIMO channels with optional complex AWGN."""
"""Flat-fading 2x2 MIMO channel with optional complex AWGN."""

import numpy as np


def apply_mimo_channel(
    tx_waveforms: np.ndarray,
    channel_matrix: np.ndarray,
    noise_variance: float = 0.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Apply a static 2x2 MIMO channel and optional complex AWGN.

    Args:
        tx_waveforms: Array shaped (2, num_samples).
        channel_matrix: Complex channel matrix shaped (2, 2).
            Rows represent receive antennas; columns represent transmit antennas.
        noise_variance: Expected complex noise power E[|w|^2] per sample.
        rng: Optional NumPy random generator for reproducible noise.

    Returns:
        Received waveforms shaped (2, num_samples).
    """
    tx = np.asarray(tx_waveforms, dtype=np.complex128)
    channel = np.asarray(channel_matrix, dtype=np.complex128)

    if tx.ndim != 2 or tx.shape[0] != 2 or tx.shape[1] == 0:
        raise ValueError(
            "tx_waveforms must have shape (2, num_samples), "
            "with num_samples > 0"
        )

    if channel.shape != (2, 2):
        raise ValueError("channel_matrix must have shape (2, 2)")

    if not np.all(np.isfinite(tx)):
        raise ValueError("tx_waveforms must contain only finite values")

    if not np.all(np.isfinite(channel)):
        raise ValueError("channel_matrix must contain only finite values")

    if (
        not np.isscalar(noise_variance)
        or isinstance(noise_variance, (bool, np.bool_))
        or not np.isreal(noise_variance)
        or not np.isfinite(noise_variance)
        or noise_variance < 0
    ):
        raise ValueError("noise_variance must be a finite non-negative number")

    # y[n] = H @ x[n], with rows as RX antennas and columns as TX antennas.
    rx = channel @ tx

    if noise_variance > 0:
        if rng is None:
            rng = np.random.default_rng()

        noise_scale = np.sqrt(noise_variance / 2.0)
        noise = noise_scale * (
            rng.standard_normal(rx.shape)
            + 1j * rng.standard_normal(rx.shape)
        )
        rx = rx + noise

    return rx


def apply_mimo_multipath_channel(
    tx_waveforms: np.ndarray,
    channel_taps: np.ndarray,
    noise_variance: float = 0.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Apply a causal static 2x2 MIMO multipath channel and optional AWGN.

    Args:
        tx_waveforms: Array shaped (2, num_samples).
        channel_taps: Complex array shaped (num_taps, 2, 2).
            channel_taps[l] is the channel matrix at delay l.
        noise_variance: Expected complex noise power E[|w|^2] per sample.
        rng: Optional NumPy random generator for reproducible noise.

    Returns:
        Received waveforms shaped (2, num_samples). No trailing
        convolution tail is appended.
    """
    tx = np.asarray(tx_waveforms, dtype=np.complex128)
    taps = np.asarray(channel_taps, dtype=np.complex128)

    if tx.ndim != 2 or tx.shape[0] != 2 or tx.shape[1] == 0:
        raise ValueError(
            "tx_waveforms must have shape (2, num_samples), "
            "with num_samples > 0"
        )

    if not np.all(np.isfinite(tx)):
        raise ValueError("tx_waveforms must contain only finite values")

    if (
        taps.ndim != 3
        or taps.shape[0] == 0
        or taps.shape[1:] != (2, 2)
    ):
        raise ValueError(
            "channel_taps must have shape (num_taps, 2, 2), "
            "with num_taps > 0"
        )

    if not np.all(np.isfinite(taps)):
        raise ValueError("channel_taps must contain only finite values")

    if not np.any(taps):
        raise ValueError("channel_taps must contain at least one non-zero value")

    if (
        not np.isscalar(noise_variance)
        or isinstance(noise_variance, (bool, np.bool_))
        or not np.isreal(noise_variance)
        or not np.isfinite(noise_variance)
        or noise_variance < 0
    ):
        raise ValueError("noise_variance must be a finite non-negative number")

    num_samples = tx.shape[1]
    rx = np.zeros((2, num_samples), dtype=np.complex128)

    # Apply causal matrix convolution across the entire waveform.
    # Samples before time zero are treated as zero.
    for delay, channel_matrix in enumerate(taps):
        if delay >= num_samples:
            break

        rx[:, delay:] += channel_matrix @ tx[:, : num_samples - delay]

    if noise_variance > 0:
        if rng is None:
            rng = np.random.default_rng()

        noise_scale = np.sqrt(noise_variance / 2.0)
        noise = noise_scale * (
            rng.standard_normal(rx.shape)
            + 1j * rng.standard_normal(rx.shape)
        )
        rx += noise

    return rx
