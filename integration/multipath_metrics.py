"""Metric calculations for reproducible MIMO multipath experiments."""

import numpy as np


def summarize_outcomes(trial_payloads, outcomes):
    """Summarize BER, PER, CRC, and exact recovery across trial outcomes.

    Each outcome is either a successful simulation result dictionary or
    None for a receiver failure. Failed trials count as packet errors and
    unsuccessful CRC/exact recovery, but contribute no fabricated bits to BER.
    """
    if len(trial_payloads) != len(outcomes) or not outcomes:
        raise ValueError("trial_payloads and outcomes must have equal nonzero length")

    num_trials = len(outcomes)
    num_streams = 2
    bit_errors = np.zeros(num_streams, dtype=np.int64)
    compared_bits = np.zeros(num_streams, dtype=np.int64)
    packet_errors = np.zeros(num_streams, dtype=np.int64)
    crc_packet_errors = np.zeros(num_streams, dtype=np.int64)
    crc_successes = np.zeros(num_streams, dtype=np.int64)
    payload_exact = np.zeros(num_streams, dtype=np.int64)
    codeword_exact = np.zeros(num_streams, dtype=np.int64)

    joint_bit_errors = 0
    joint_compared_bits = 0
    joint_packet_errors = 0
    joint_crc_packet_errors = 0
    joint_crc_successes = 0
    joint_payload_exact = 0
    joint_codeword_exact = 0
    failed_trials = 0

    for payloads, outcome in zip(trial_payloads, outcomes):
        if len(payloads) != num_streams:
            raise ValueError("each trial must contain exactly two payloads")

        if outcome is None:
            failed_trials += 1
            packet_errors += 1
            crc_packet_errors += 1
            joint_packet_errors += 1
            joint_crc_packet_errors += 1
            continue

        recovered = outcome["recovered_payloads"]
        crc_valid = outcome["crc_valid"]
        receiver_results = outcome["receiver_results"]
        transmitted_codewords = outcome["transmitted_codewords"]

        stream_exact_this_trial = []
        stream_crc_this_trial = []
        stream_codeword_exact_this_trial = []

        for stream in range(num_streams):
            transmitted = np.asarray(payloads[stream], dtype=np.int8)
            received = np.asarray(recovered[stream], dtype=np.int8)

            if received.shape != transmitted.shape:
                raise ValueError(
                    f"stream {stream} returned a payload with an unexpected shape"
                )

            errors = int(np.count_nonzero(transmitted != received))
            bit_errors[stream] += errors
            compared_bits[stream] += transmitted.size

            exact = errors == 0
            crc_ok = bool(crc_valid[stream])
            codeword_ok = (
                receiver_results[stream]["codeword_bits"]
                == transmitted_codewords[stream]
            )

            payload_exact[stream] += exact
            crc_successes[stream] += crc_ok
            crc_packet_errors[stream] += not crc_ok
            codeword_exact[stream] += codeword_ok

            if not exact:
                packet_errors[stream] += 1

            stream_exact_this_trial.append(exact)
            stream_crc_this_trial.append(crc_ok)
            stream_codeword_exact_this_trial.append(codeword_ok)

        joint_bit_errors += int(np.sum(
            [
                np.count_nonzero(
                    np.asarray(payloads[s], dtype=np.int8)
                    != np.asarray(recovered[s], dtype=np.int8)
                )
                for s in range(num_streams)
            ]
        ))
        joint_compared_bits += sum(len(payload) for payload in payloads)

        joint_crc_successes += all(stream_crc_this_trial)
        joint_crc_packet_errors += not all(stream_crc_this_trial)
        joint_payload_exact += all(stream_exact_this_trial)
        joint_codeword_exact += all(stream_codeword_exact_this_trial)

        if not all(stream_exact_this_trial):
            joint_packet_errors += 1

    def conditional_ber(errors, bits):
        return float(errors / bits) if bits else None

    return {
        "trials": num_trials,
        "failed_trials": failed_trials,
        "receiver_failure_rate": failed_trials / num_trials,
        "stream0_bit_errors": int(bit_errors[0]),
        "stream1_bit_errors": int(bit_errors[1]),
        "stream0_compared_bits": int(compared_bits[0]),
        "stream1_compared_bits": int(compared_bits[1]),
        "stream0_ber_conditional": conditional_ber(
            bit_errors[0], compared_bits[0]
        ),
        "stream1_ber_conditional": conditional_ber(
            bit_errors[1], compared_bits[1]
        ),
        "joint_bit_errors": joint_bit_errors,
        "joint_compared_bits": joint_compared_bits,
        "joint_ber_conditional": conditional_ber(
            joint_bit_errors, joint_compared_bits
        ),
        "stream0_packet_error_rate": packet_errors[0] / num_trials,
        "stream1_packet_error_rate": packet_errors[1] / num_trials,
        "joint_packet_error_rate": joint_packet_errors / num_trials,
        "stream0_crc_packet_error_rate": crc_packet_errors[0] / num_trials,
        "stream1_crc_packet_error_rate": crc_packet_errors[1] / num_trials,
        "joint_crc_packet_error_rate": joint_crc_packet_errors / num_trials,
        "stream0_crc_success_rate": crc_successes[0] / num_trials,
        "stream1_crc_success_rate": crc_successes[1] / num_trials,
        "joint_crc_success_rate": joint_crc_successes / num_trials,
        "stream0_payload_exact_rate": payload_exact[0] / num_trials,
        "stream1_payload_exact_rate": payload_exact[1] / num_trials,
        "joint_payload_exact_rate": joint_payload_exact / num_trials,
        "stream0_codeword_exact_rate": codeword_exact[0] / num_trials,
        "stream1_codeword_exact_rate": codeword_exact[1] / num_trials,
        "joint_codeword_exact_rate": joint_codeword_exact / num_trials,
    }
