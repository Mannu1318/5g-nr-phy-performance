import csv

import numpy as np

from scripts.run_integration_awgn import (
    NOISE_VARIANCES,
    run_experiment,
    write_outputs,
)


def test_awgn_sweep_covers_all_configured_noise_variances():
    rows = run_experiment(trials=2)

    assert [row["noise_variance"] for row in rows] == list(NOISE_VARIANCES)
    assert all(row["trials"] == 2 for row in rows)


def test_awgn_sweep_is_reproducible():
    first = run_experiment(trials=2)
    second = run_experiment(trials=2)

    assert first == second


def test_awgn_recovery_rates_are_valid_and_zero_noise_is_exact():
    rows = run_experiment(trials=2)

    rate_keys = (
        "stream0_crc_rate",
        "stream1_crc_rate",
        "joint_crc_rate",
        "stream0_exact_rate",
        "stream1_exact_rate",
        "full_link_exact_rate",
    )

    for row in rows:
        for key in rate_keys:
            assert 0.0 <= row[key] <= 1.0

    zero_noise = rows[0]
    assert zero_noise["noise_variance"] == 0.0
    assert zero_noise["joint_crc_rate"] == 1.0
    assert zero_noise["full_link_exact_rate"] == 1.0
    assert zero_noise["measured_noise_power"] == 0.0
    assert np.isinf(zero_noise["nominal_snr_db"])


def test_awgn_outputs_write_csv_and_markdown_report(tmp_path):
    rows = run_experiment(trials=2)
    write_outputs(rows, tmp_path)

    csv_path = tmp_path / "awgn_sweep.csv"
    report_path = tmp_path / "awgn_report.md"

    assert csv_path.is_file()
    assert report_path.is_file()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))

    assert len(csv_rows) == len(NOISE_VARIANCES)
    assert float(csv_rows[0]["noise_variance"]) == 0.0
    assert float(csv_rows[0]["full_link_exact_rate"]) == 1.0

    report = report_path.read_text(encoding="utf-8")
    assert "# End-to-End 2x2 MIMO AWGN Sweep" in report
    assert "## Results" in report
    assert "## Interpretation notes" in report
    assert "Trials per noise variance: `2`" in report
