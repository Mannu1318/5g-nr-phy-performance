"""End-to-end tests for the simplified 2x2 MIMO PHY link."""

import numpy as np

from integration.simulation import simulate_mimo_link


def test_noise_free_link_recovers_both_payloads_and_crc():
    """Both streams should be recovered exactly over an invertible channel."""
    payloads = [
        [(index * 7 + 0) % 2 for index in range(38)],
        [(index * 7 + 1) % 2 for index in range(38)],
    ]

    channel = np.array(
        [
            [1.0 + 0.0j, 0.2 + 0.1j],
            [0.1 - 0.1j, 1.2 + 0.0j],
        ],
        dtype=np.complex128,
    )

    result = simulate_mimo_link(
        payloads=payloads,
        channel_matrix=channel,
        modulation="QPSK",
        fft_size=64,
        cp_length=16,
        num_ofdm_symbols=3,
        noise_variance=0.0,
    )

    assert result["recovered_payloads"] == payloads
    assert result["crc_valid"] == [True, True]

    estimates = result["channel_estimates"]
    for data_bin_index in range(estimates.shape[2]):
        np.testing.assert_allclose(
            estimates[:, :, data_bin_index],
            channel,
            rtol=1e-10,
            atol=1e-10,
        )


def test_rejects_payload_count_other_than_two():
    channel = np.eye(2, dtype=np.complex128)

    try:
        simulate_mimo_link(
            payloads=[ [0, 1, 0] ],
            channel_matrix=channel,
        )
    except ValueError as exc:
        assert "exactly two" in str(exc)
    else:
        raise AssertionError("Expected ValueError for one payload")
