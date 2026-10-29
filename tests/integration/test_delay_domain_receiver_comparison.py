import csv
import json

import numpy as np

from scripts.compare_delay_domain_receiver import (
    run_experiment,
    write_outputs,
)


def test_noise_free_receiver_comparison_is_deterministic():
    first_rows, first_metadata, first_taps = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )
    second_rows, second_metadata, second_taps = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    assert first_rows == second_rows
    assert first_metadata == second_metadata
    np.testing.assert_array_equal(first_taps, second_taps)


def test_noise_free_delay_domain_receiver_recovers_codewords():
    rows, _, _ = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    assert len(rows) == 1
    row = rows[0]

    assert row["noise_variance"] == 0.0
    assert row["trials"] == 2
    assert row["kernel5_receiver_failures"] == 0
    assert row["delay_domain_receiver_failures"] == 0

    assert row["delay_domain_joint_crc_rate"] == 1.0
    assert row["delay_domain_joint_payload_exact_rate"] == 1.0
    assert row["delay_domain_joint_codeword_exact_rate"] == 1.0

    # Rates use all transmitted trials, not only successful receiver trials.
    for estimator in ("kernel5", "delay_domain"):
        assert row[f"{estimator}_rate_denominator"] == row["trials"]
        assert row[f"{estimator}_joint_packet_error_rate"] == 0.0
        assert row[f"{estimator}_joint_ber_conditional"] == 0.0
        assert row[f"{estimator}_joint_compared_bits"] == 2 * 38 * 2

    assert row["delay_domain_joint_crc_packet_error_rate"] == 0.0

    assert (
        row["delay_domain_mean_nmse"]
        < row["kernel5_mean_nmse"]
    )


def test_experiment_writes_isolated_outputs(tmp_path):
    rows, profile_metadata, channel_taps = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    write_outputs(rows, profile_metadata, channel_taps, tmp_path)

    csv_path = tmp_path / "receiver_comparison.csv"
    profile_path = tmp_path / "receiver_comparison_profile.json"
    report_path = tmp_path / "receiver_comparison_report.md"

    assert csv_path.is_file()
    assert profile_path.is_file()
    assert report_path.is_file()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        saved_rows = list(csv.DictReader(handle))

    assert len(saved_rows) == 1
    assert float(saved_rows[0]["noise_variance"]) == 0.0

    with profile_path.open(encoding="utf-8") as handle:
        saved_profile = json.load(handle)

    assert saved_profile
    report = report_path.read_text(encoding="utf-8")
    assert "delay_domain" in report
    assert "kernel5" in report
    assert "BER and Packet Error Rates" in report
    assert "Joint PER" in report
    assert "all transmitted trials" in report

    for estimator in ("kernel5", "delay_domain"):
        assert int(saved_rows[0][f"{estimator}_rate_denominator"]) == 2
        assert f"{estimator}_joint_ber_conditional" in saved_rows[0]
        assert f"{estimator}_joint_packet_error_rate" in saved_rows[0]
        assert f"{estimator}_joint_crc_packet_error_rate" in saved_rows[0]
