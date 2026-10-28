"""Tests for multipath experiment outcome metrics."""

import pytest

from integration.multipath_metrics import summarize_outcomes


def successful_outcome(payloads, *, flip_stream0_bit=False, crc_valid=True):
    recovered = [list(payload) for payload in payloads]

    if flip_stream0_bit:
        recovered[0][0] ^= 1

    codewords = [
        list(payload) + [0] * 24
        for payload in payloads
    ]

    receiver_results = [
        {
            "payload_bits": recovered[stream],
            "codeword_bits": list(codewords[stream]),
            "crc_valid": crc_valid,
        }
        for stream in range(2)
    ]

    return {
        "recovered_payloads": recovered,
        "crc_valid": [crc_valid, crc_valid],
        "receiver_results": receiver_results,
        "transmitted_codewords": codewords,
    }


def test_perfect_trials_have_zero_ber_and_no_packet_errors():
    payloads = [[0, 1, 0, 1], [1, 0, 1, 0]]
    metrics = summarize_outcomes(
        [payloads],
        [successful_outcome(payloads)],
    )

    assert metrics["stream0_ber_conditional"] == 0.0
    assert metrics["stream1_ber_conditional"] == 0.0
    assert metrics["joint_ber_conditional"] == 0.0
    assert metrics["joint_packet_error_rate"] == 0.0
    assert metrics["joint_crc_success_rate"] == 1.0
    assert metrics["joint_payload_exact_rate"] == 1.0
    assert metrics["joint_codeword_exact_rate"] == 1.0


def test_crc_failure_with_exact_payload_counts_as_crc_packet_error():
    payloads = [[0, 1, 0, 1], [1, 0, 1, 0]]
    outcome = successful_outcome(payloads)

    # Model a CRC-bit error while leaving the recovered payload unchanged.
    outcome["receiver_results"][0]["codeword_bits"][-1] ^= 1
    outcome["receiver_results"][0]["crc_valid"] = False
    outcome["crc_valid"][0] = False

    metrics = summarize_outcomes([payloads], [outcome])

    assert metrics["stream0_packet_error_rate"] == 0.0
    assert metrics["stream0_crc_packet_error_rate"] == 1.0
    assert metrics["stream1_crc_packet_error_rate"] == 0.0
    assert metrics["joint_packet_error_rate"] == 0.0
    assert metrics["joint_crc_packet_error_rate"] == 1.0


def test_payload_bit_error_increases_ber_and_packet_error_rate():
    payloads = [[0, 1, 0, 1], [1, 0, 1, 0]]
    metrics = summarize_outcomes(
        [payloads],
        [successful_outcome(payloads, flip_stream0_bit=True)],
    )

    assert metrics["stream0_bit_errors"] == 1
    assert metrics["stream0_compared_bits"] == 4
    assert metrics["stream0_ber_conditional"] == pytest.approx(0.25)
    assert metrics["stream0_packet_error_rate"] == 1.0
    assert metrics["stream1_packet_error_rate"] == 0.0
    assert metrics["joint_packet_error_rate"] == 1.0
    assert metrics["joint_payload_exact_rate"] == 0.0


def test_receiver_failure_counts_as_packet_error_but_not_ber_bits():
    payloads = [[0, 1, 0, 1], [1, 0, 1, 0]]
    metrics = summarize_outcomes(
        [payloads, payloads],
        [successful_outcome(payloads), None],
    )

    assert metrics["failed_trials"] == 1
    assert metrics["receiver_failure_rate"] == 0.5
    assert metrics["stream0_compared_bits"] == 4
    assert metrics["stream1_compared_bits"] == 4
    assert metrics["stream0_ber_conditional"] == 0.0
    assert metrics["joint_packet_error_rate"] == 0.5
    assert metrics["stream0_crc_packet_error_rate"] == 0.5
    assert metrics["stream1_crc_packet_error_rate"] == 0.5
    assert metrics["joint_crc_packet_error_rate"] == 0.5
    assert metrics["joint_crc_success_rate"] == 0.5
    assert metrics["joint_payload_exact_rate"] == 0.5
    assert metrics["joint_codeword_exact_rate"] == 0.5


def test_ber_is_none_if_every_receiver_trial_fails():
    payloads = [[0, 1], [1, 0]]
    metrics = summarize_outcomes([payloads], [None])

    assert metrics["stream0_ber_conditional"] is None
    assert metrics["stream1_ber_conditional"] is None
    assert metrics["joint_ber_conditional"] is None
    assert metrics["joint_packet_error_rate"] == 1.0
    assert metrics["joint_crc_success_rate"] == 0.0


def test_mismatched_trial_counts_are_rejected():
    with pytest.raises(ValueError, match="equal nonzero length"):
        summarize_outcomes([[[0], [1]]], [])
