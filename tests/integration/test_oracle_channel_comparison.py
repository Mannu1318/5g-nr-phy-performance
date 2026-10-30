import csv
import json

import numpy as np

from scripts.compare_oracle_channel_receiver import (
    METHODS,
    run_experiment,
    write_outputs,
)
from scripts import compare_delay_domain_receiver as base
from scripts import compare_oracle_channel_receiver as oracle_comparison


def test_oracle_comparison_is_deterministic():
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


def test_noise_free_oracle_recovers_both_codewords():
    rows, _, _ = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    assert len(rows) == 1
    row = rows[0]

    assert row["noise_variance"] == 0.0
    assert row["trials"] == 2

    assert row["oracle_mean_nmse"] < 1e-25
    assert row["oracle_receiver_failures"] == 0

    for metric in (
        "joint_crc_rate",
        "joint_payload_exact_rate",
        "joint_codeword_exact_rate",
    ):
        assert row[f"oracle_{metric}"] == 1.0

    assert row["oracle_joint_ber_conditional"] == 0.0
    assert row["oracle_joint_packet_error_rate"] == 0.0

    for name in METHODS:
        assert row[f"{name}_rate_denominator"] == 2
        assert row[f"{name}_receiver_failures"] == 0


def test_oracle_comparison_writes_isolated_outputs(tmp_path):
    rows, profile_metadata, channel_taps = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    write_outputs(
        rows,
        profile_metadata,
        channel_taps,
        tmp_path,
    )

    csv_path = tmp_path / "oracle_comparison.csv"
    profile_path = tmp_path / "oracle_comparison_profile.json"
    report_path = tmp_path / "oracle_comparison_report.md"

    assert csv_path.is_file()
    assert profile_path.is_file()
    assert report_path.is_file()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        saved_rows = list(csv.DictReader(handle))

    assert len(saved_rows) == 1
    assert float(saved_rows[0]["noise_variance"]) == 0.0

    with profile_path.open(encoding="utf-8") as handle:
        saved_profile = json.load(handle)

    assert saved_profile["experiment"] == "oracle_channel_comparison"
    assert saved_profile["noise_variances"] == [0.0]

    report = report_path.read_text(encoding="utf-8")
    assert "kernel5" in report
    assert "delay_domain" in report
    assert "oracle" in report
    assert "Oracle does not remove AWGN" in report
    assert "all transmitted trials" in report

    for name in METHODS:
        assert int(saved_rows[0][f"{name}_rate_denominator"]) == 2
        assert f"{name}_joint_ber_conditional" in saved_rows[0]
        assert f"{name}_joint_packet_error_rate" in saved_rows[0]


def test_oracle_frequency_response_matches_independent_reference():
    fft_size = base.FFT_SIZE
    bins = np.array([0, 3, 11, 27, 45, 63], dtype=np.int64)

    channel_taps = np.zeros((9, 2, 2), dtype=np.complex128)
    channel_taps[0] = np.array(
        [[1.0 + 0.2j, 0.1 - 0.3j],
         [0.2 + 0.1j, 0.8 - 0.2j]]
    )
    channel_taps[3] = np.array(
        [[0.2 - 0.1j, -0.1 + 0.05j],
         [0.05 + 0.1j, 0.15 + 0.2j]]
    )
    channel_taps[8] = np.array(
        [[-0.05 + 0.1j, 0.03 + 0.02j],
         [0.1 - 0.05j, -0.08 + 0.04j]]
    )

    delays = np.arange(channel_taps.shape[0])
    exponentials = np.exp(
        -2j * np.pi * np.outer(bins, delays) / fft_size
    )
    expected = np.einsum(
        "dij,kd->ijk",
        channel_taps,
        exponentials,
    )

    actual = base.true_frequency_response(channel_taps, bins)

    assert actual.shape == (2, 2, bins.size)
    np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-13)


def test_all_methods_receive_identical_grid_within_each_trial(monkeypatch):
    received_grids = []
    original_evaluate = base.evaluate_estimator

    def recording_evaluate(received_grid, *args, **kwargs):
        received_grids.append(received_grid)
        return original_evaluate(received_grid, *args, **kwargs)

    monkeypatch.setattr(
        oracle_comparison.base,
        "evaluate_estimator",
        recording_evaluate,
    )

    run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    assert len(received_grids) == 2 * len(METHODS)

    for trial_index in range(2):
        trial_grids = received_grids[
            trial_index * len(METHODS):
            (trial_index + 1) * len(METHODS)
        ]

        assert trial_grids[0] is trial_grids[1]
        assert trial_grids[1] is trial_grids[2]
