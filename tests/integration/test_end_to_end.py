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

def test_single_tap_multipath_matches_flat_fading():
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

    flat_result = simulate_mimo_link(
        payloads=payloads,
        channel_matrix=channel,
    )

    multipath_result = simulate_mimo_link(
        payloads=payloads,
        channel_taps=channel[None, :, :],
    )

    assert multipath_result["recovered_payloads"] == flat_result["recovered_payloads"]
    assert multipath_result["crc_valid"] == flat_result["crc_valid"]

    np.testing.assert_allclose(
        multipath_result["received_grid"],
        flat_result["received_grid"],
        rtol=1e-12,
        atol=1e-12,
    )


def test_rejects_both_channel_matrix_and_channel_taps():
    payloads = [
        [(index * 7 + 0) % 2 for index in range(38)],
        [(index * 7 + 1) % 2 for index in range(38)],
    ]

    channel = np.eye(2, dtype=np.complex128)

    try:
        simulate_mimo_link(
            payloads=payloads,
            channel_matrix=channel,
            channel_taps=channel[None, :, :],
        )
    except ValueError as exc:
        assert "either" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError when both channel forms are supplied")


def test_rejects_missing_channel_matrix_and_channel_taps():
    payloads = [
        [(index * 7 + 0) % 2 for index in range(38)],
        [(index * 7 + 1) % 2 for index in range(38)],
    ]

    try:
        simulate_mimo_link(payloads=payloads)
    except ValueError as exc:
        assert "channel" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError when neither channel form is supplied")

def test_two_tap_multipath_link_recovers_both_payloads():
    """A mild frequency-selective channel should recover both streams."""
    payloads = [
        [(index * 7 + 0) % 2 for index in range(38)],
        [(index * 7 + 1) % 2 for index in range(38)],
    ]

    first_tap = np.array(
        [
            [1.0 + 0.0j, 0.2 + 0.1j],
            [0.1 - 0.1j, 1.2 + 0.0j],
        ],
        dtype=np.complex128,
    )

    # A weak delayed path, one sample after the main path.
    second_tap = 0.02 * first_tap
    channel_taps = np.stack([first_tap, second_tap])

    result = simulate_mimo_link(
        payloads=payloads,
        channel_taps=channel_taps,
        modulation="QPSK",
        fft_size=64,
        cp_length=16,
        num_ofdm_symbols=3,
        noise_variance=0.0,
    )

    assert result["recovered_payloads"] == payloads
    assert result["crc_valid"] == [True, True]
