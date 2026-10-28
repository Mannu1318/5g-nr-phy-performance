#!/usr/bin/env python3
"""Reproducible AWGN sweep for the integrated 2x2 MIMO PHY link."""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
# Make the project root importable when this script is run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integration.channel import apply_mimo_channel
from integration.simulation import simulate_mimo_link


CHANNEL = np.array(
    [
        [1.0 + 0.0j, 0.2 + 0.1j],
        [0.1 - 0.1j, 1.2 + 0.0j],
    ],
    dtype=np.complex128,
)

NOISE_VARIANCES = (
    0.0,
    0.0005,
    0.001,
    0.002,
    0.003,
    0.005,
    0.0075,
    0.01,
    0.02,
)
MASTER_SEED = 20261028
PAYLOAD_BITS = 38


def make_payloads(rng: np.random.Generator) -> list[list[int]]:
    """Generate two independent valid-length payloads."""
    return [
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
    ]


def run_experiment(trials: int) -> list[dict[str, object]]:
    """Run the same payload trials at each noise variance."""
    master_rng = np.random.default_rng(MASTER_SEED)
    trial_payloads = [make_payloads(master_rng) for _ in range(trials)]
    rows: list[dict[str, object]] = []

    for variance_index, variance in enumerate(NOISE_VARIANCES):
        stream_crc = np.zeros(2, dtype=np.int64)
        stream_exact = np.zeros(2, dtype=np.int64)
        joint_crc = 0
        joint_exact = 0
        signal_power_sum = 0.0
        measured_noise_power_sum = 0.0
        measured_noise_samples = 0

        for trial_index, payloads in enumerate(trial_payloads):
            # Independent, repeatable noise sequence for each trial and level.
            seed = (
                MASTER_SEED
                + variance_index * 1_000_003
                + trial_index
            )
            noise_rng = np.random.default_rng(seed)

            # Run the normal simulation with the selected noise level.
            result = simulate_mimo_link(
                payloads=payloads,
                channel_matrix=CHANNEL,
                modulation="QPSK",
                fft_size=64,
                cp_length=16,
                num_ofdm_symbols=3,
                noise_variance=variance,
                rng=noise_rng,
            )

            for stream in range(2):
                stream_crc[stream] += bool(result["crc_valid"][stream])
                stream_exact[stream] += (
                    result["recovered_payloads"][stream] == payloads[stream]
                )

            both_crc = all(result["crc_valid"])
            both_exact = result["recovered_payloads"] == payloads
            joint_crc += both_crc
            joint_exact += both_exact

            # Reconstruct transmitted waveforms from the noiseless received
            # waveform relation. The same channel and transmitted waveforms
            # are used for this trial's received signal-power measurement.
            from integration.tx_chain.ofdm_transmitter import (
                modulate_resource_grid,
            )
            from integration.tx_chain.resource_grid import (
                build_mimo_resource_grid,
            )
            from integration.tx_chain.bit_processing import transmit_bits

            symbol_streams = [
                transmit_bits(
                    payload_bits=payload,
                    n_rnti=0x1234,
                    n_id=0x155,
                    modulation="QPSK",
                    q=0,
                )[2]
                for payload in payloads
            ]
            grid, _, _ = build_mimo_resource_grid(
                data_symbols=symbol_streams,
                fft_size=64,
                num_ofdm_symbols=3,
            )
            tx_waveforms = modulate_resource_grid(grid, cp_length=16)
            noiseless_rx = CHANNEL @ tx_waveforms
            signal_power_sum += float(np.mean(np.abs(noiseless_rx) ** 2))

            if variance > 0:
                noisy_rx = apply_mimo_channel(
                    tx_waveforms,
                    CHANNEL,
                    noise_variance=variance,
                    rng=np.random.default_rng(seed),
                )
                noise = noisy_rx - noiseless_rx
                measured_noise_power_sum += float(np.sum(np.abs(noise) ** 2))
                measured_noise_samples += noise.size

        mean_signal_power = signal_power_sum / trials
        measured_noise_power = (
            measured_noise_power_sum / measured_noise_samples
            if measured_noise_samples
            else 0.0
        )

        if variance == 0:
            snr_db = float("inf")
        else:
            # Nominal SNR uses expected noise variance, not the random
            # measured noise power from this finite experiment.
            snr_db = 10.0 * np.log10(mean_signal_power / variance)

        rows.append(
            {
                "noise_variance": variance,
                "trials": trials,
                "stream0_crc_rate": stream_crc[0] / trials,
                "stream1_crc_rate": stream_crc[1] / trials,
                "joint_crc_rate": joint_crc / trials,
                "stream0_exact_rate": stream_exact[0] / trials,
                "stream1_exact_rate": stream_exact[1] / trials,
                "full_link_exact_rate": joint_exact / trials,
                "mean_received_signal_power": mean_signal_power,
                "measured_noise_power": measured_noise_power,
                "nominal_snr_db": snr_db,
            }
        )

    return rows


def write_outputs(rows: list[dict[str, object]], output_dir: Path) -> None:
    """Write CSV measurements and a Markdown summary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "awgn_sweep.csv"
    report_path = output_dir / "awgn_report.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    report_lines = [
        "# End-to-End 2x2 MIMO AWGN Sweep",
        "",
        f"- Master seed: `{MASTER_SEED}`",
        f"- Trials per noise variance: `{rows[0]['trials']}`",
        "- Modulation: QPSK",
        "- FFT size / cyclic prefix: 64 / 16",
        "- OFDM symbols: 3",
        "- Payload length: 38 bits per stream",
        "- Channel matrix: `[[1, 0.2+0.1j], [0.1-0.1j, 1.2]]`",
        "",
        "Noise variance is expected complex noise power per receive sample. "
        "Nominal SNR is calculated from average noiseless received signal "
        "power divided by the configured noise variance.",
        "",
        "## Results",
        "",
        "| Noise variance | Nominal SNR (dB) | CRC stream 0 | CRC stream 1 "
        "| Joint CRC | Full-link exact recovery | Measured noise power |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        snr = (
            "∞"
            if np.isinf(row["nominal_snr_db"])
            else f"{row['nominal_snr_db']:.2f}"
        )
        report_lines.append(
            f"| {row['noise_variance']} | {snr} "
            f"| {row['stream0_crc_rate']:.3f} "
            f"| {row['stream1_crc_rate']:.3f} "
            f"| {row['joint_crc_rate']:.3f} "
            f"| {row['full_link_exact_rate']:.3f} "
            f"| {row['measured_noise_power']:.6f} |"
        )

    report_lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- Rates are empirical results from the specified number of trials.",
            "- CRC success is not assumed to guarantee exact payload recovery.",
            "- At zero noise, measured noise power is reported as zero and SNR "
            "as infinite.",
            "- For nonzero variance, finite-sample measured noise power may "
            "differ from the configured variance.",
            "",
        ]
    )
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trials",
        type=int,
        default=100,
        help="Number of repeated payload trials per noise variance (default: 100)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/integration_awgn"),
        help="Directory for CSV and Markdown outputs",
    )
    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be at least 1")

    rows = run_experiment(args.trials)
    write_outputs(rows, args.output_dir)

    print("\nNoise sweep summary:")
    for row in rows:
        print(
            f"variance={row['noise_variance']:>6}  "
            f"joint_crc={row['joint_crc_rate']:.3f}  "
            f"full_link_exact={row['full_link_exact_rate']:.3f}"
        )


if __name__ == "__main__":
    main()
