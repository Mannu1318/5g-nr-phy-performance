import csv
import json

import numpy as np

from scripts.compare_mmse_zf_receiver import (
    METHODS,
    run_experiment,
    write_outputs,
)


def test_mmse_zf_comparison_is_deterministic():
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


def test_noise_free_mmse_and_zf_recover_both_codewords():
    rows, _, _ = run_experiment(
        trials=2,
        noise_variances=[0.0],
    )

    assert len(rows) == 1
    row = rows[0]

    assert row["noise_variance"] == 0.0
    assert row["mmse_regularization_lambda"] == 0.0
    assert row["frequency_domain_noise_variance"] == 0.0
    assert row["trials"] == 2

    for name in METHODS:
        assert row[f"{name}_receiver_failures"] == 0
        assert row[f"{name}_rate_denominator"] == 2
        assert row[f"{name}_joint_crc_rate"] == 1.0
        assert row[f"{name}_joint_payload_exact_rate"] == 1.0
        assert row[f"{name}_joint_codeword_exact_rate"] == 1.0
        assert row[f"{name}_joint_ber_conditional"] == 0.0
        assert row[f"{name}_joint_packet_error_rate"] == 0.0


def test_mmse_regularization_uses_fft_noise_variance():
    rows, _, _ = run_experiment(
        trials=2,
        noise_variances=[0.0005, 0.001],
    )

    assert len(rows) == 2

    expected = {
        0.0005: 0.032,
        0.001: 0.064,
    }

    for row in rows:
        variance = row["noise_variance"]
        assert np.isclose(
            row["frequency_domain_noise_variance"],
            expected[variance],
        )
        assert np.isclose(
            row["mmse_regularization_lambda"],
            expected[variance],
        )


def test_mmse_zf_comparison_writes_isolated_outputs(tmp_path):
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

    csv_path = tmp_path / "mmse_zf_comparison.csv"
    profile_path = tmp_path / "mmse_zf_comparison_profile.json"
    report_path = tmp_path / "mmse_zf_comparison_report.md"

    assert csv_path.is_file()
    assert profile_path.is_file()
    assert report_path.is_file()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        saved_rows = list(csv.DictReader(handle))

    assert len(saved_rows) == 1
    assert float(saved_rows[0]["noise_variance"]) == 0.0

    with profile_path.open(encoding="utf-8") as handle:
        saved_profile = json.load(handle)

    assert saved_profile["experiment"] == "mmse_zf_comparison"
    assert saved_profile["methods"] == list(METHODS)
    assert saved_profile["channel_knowledge"] == "oracle"
    assert saved_profile["noise_variances"] == [0.0]

    saved_taps = np.asarray(saved_profile["channel_taps_real_imag"])
    assert saved_taps.shape == channel_taps.shape + (2,)

    report = report_path.read_text(encoding="utf-8")
    assert "zf" in report
    assert "mmse" in report
    assert "oracle" in report.lower()
    assert "same received grid" in report
    assert "does not remove AWGN" in report
    assert "all transmitted trials" in report

    for name in METHODS:
        assert int(saved_rows[0][f"{name}_rate_denominator"]) == 2
        assert f"{name}_joint_ber_conditional" in saved_rows[0]
        assert f"{name}_joint_packet_error_rate" in saved_rows[0]
