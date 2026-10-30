"""Compare estimated and oracle channels in the 2x2 MIMO receiver."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from integration.channel import apply_mimo_multipath_channel
from integration.channel_profiles import build_multipath_profile
from integration.multipath_metrics import summarize_outcomes
from integration.rx_chain.ofdm_receiver import demodulate_waveforms
from scripts import compare_delay_domain_receiver as base



METHODS = ("kernel5", "delay_domain", "oracle")

DEFAULT_OUTPUT_DIR = (
    PROJECT_ROOT
    / "results"
    / "integration_multipath"
    / "oracle_channel_comparison"
)


def run_experiment(trials, noise_variances):
    """Run paired Kernel 5, delay-domain, and oracle receiver comparisons."""
    channel_taps, profile_metadata = build_multipath_profile(
        base.DELAYS_SAMPLES,
        base.TAP_POWERS_DB,
        seed=base.PROFILE_SEED,
        normalize_power=True,
    )

    payload_rng = np.random.default_rng(base.PAYLOAD_SEED)
    payloads_by_trial = [
        base.make_payloads(payload_rng) for _ in range(trials)
    ]

    rows = []

    for variance_index, variance in enumerate(noise_variances):
        outcomes = {name: [] for name in METHODS}
        nmse = {name: [] for name in METHODS}
        residuals = []
        conditions = []

        for trial_index, payloads in enumerate(payloads_by_trial):
            codewords, tx_waveforms, pilot_bins, data_bins = (
                base.build_tx(payloads)
            )

            noise_seed = (
                base.NOISE_SEED_BASE
                + variance_index * 1_000_003
                + trial_index
            )

            received_waveforms = apply_mimo_multipath_channel(
                tx_waveforms,
                channel_taps,
                noise_variance=variance,
                rng=np.random.default_rng(noise_seed),
            )

            received_grid = demodulate_waveforms(
                received_waveforms,
                fft_size=base.FFT_SIZE,
                cp_length=base.CP_LENGTH,
            )

            # Exact channel response calculated from the generated taps.
            truth = base.true_frequency_response(channel_taps, data_bins)

            kernel5, delay_domain, trial_residuals, trial_conditions = (
                base.estimate_both(
                    received_grid,
                    pilot_bins,
                    data_bins,
                )
            )

            estimates = {
                "kernel5": kernel5,
                "delay_domain": delay_domain,
                "oracle": truth,
            }

            residuals.extend(trial_residuals)
            conditions.extend(trial_conditions)

            for name in METHODS:
                nmse[name].append(
                    base.calculate_nmse(estimates[name], truth)
                )

                try:
                    outcome = base.evaluate_estimator(
                        received_grid,
                        estimates[name],
                        data_bins,
                        payloads,
                        codewords,
                    )
                except (
                    ValueError,
                    np.linalg.LinAlgError,
                    FloatingPointError,
                ):
                    outcome = None

                outcomes[name].append(outcome)

        summaries = {
            name: summarize_outcomes(
                payloads_by_trial,
                outcomes[name],
            )
            for name in METHODS
        }

        row = {
            "noise_variance": float(variance),
            "trials": trials,
            "mean_delay_domain_residual_norm": float(
                np.mean(residuals)
            ),
            "mean_design_matrix_condition_number": float(
                np.mean(conditions)
            ),
        }

        for name in METHODS:
            summary = summaries[name]

            row[f"{name}_receiver_failures"] = summary[
                "failed_trials"
            ]
            row[f"{name}_mean_nmse"] = float(np.mean(nmse[name]))
            row[f"{name}_rate_denominator"] = trials

            rate_suffixes = {
                "crc": "crc_success_rate",
                "payload_exact": "payload_exact_rate",
                "codeword_exact": "codeword_exact_rate",
            }

            for metric, suffix in rate_suffixes.items():
                row[f"{name}_stream0_{metric}_rate"] = summary[
                    f"stream0_{suffix}"
                ]
                row[f"{name}_stream1_{metric}_rate"] = summary[
                    f"stream1_{suffix}"
                ]
                row[f"{name}_joint_{metric}_rate"] = summary[
                    f"joint_{suffix}"
                ]

            for metric in (
                "stream0_bit_errors",
                "stream1_bit_errors",
                "stream0_compared_bits",
                "stream1_compared_bits",
                "stream0_ber_conditional",
                "stream1_ber_conditional",
                "joint_bit_errors",
                "joint_compared_bits",
                "joint_ber_conditional",
                "stream0_packet_error_rate",
                "stream1_packet_error_rate",
                "joint_packet_error_rate",
                "stream0_crc_packet_error_rate",
                "stream1_crc_packet_error_rate",
                "joint_crc_packet_error_rate",
            ):
                row[f"{name}_{metric}"] = summary[metric]

        rows.append(row)

    return rows, profile_metadata, channel_taps


def write_outputs(rows, profile_metadata, channel_taps, output_dir):
    """Write isolated CSV, JSON profile, and Markdown report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "oracle_comparison.csv"
    profile_path = output_dir / "oracle_comparison_profile.json"
    report_path = output_dir / "oracle_comparison_report.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    profile_document = {
        "experiment": "oracle_channel_comparison",
        "profile_metadata": profile_metadata,
        "profile_seed": base.PROFILE_SEED,
        "payload_seed": base.PAYLOAD_SEED,
        "noise_seed_base": base.NOISE_SEED_BASE,
        "fft_size": base.FFT_SIZE,
        "cp_length": base.CP_LENGTH,
        "num_ofdm_symbols": base.NUM_OFDM_SYMBOLS,
        "modulation": base.MODULATION,
        "payload_bits_per_stream": base.PAYLOAD_BITS,
        "max_delay_samples": base.MAX_DELAY_SAMPLES,
        "noise_variances": [
            row["noise_variance"] for row in rows
        ],
        "channel_taps_real_imag": [
            [
                [
                    [float(value.real), float(value.imag)]
                    for value in link
                ]
                for link in tap
            ]
            for tap in channel_taps
        ],
    }

    profile_path.write_text(
        json.dumps(profile_document, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# End-to-End Oracle Channel Comparison",
        "",
        f"- Trials per noise variance: `{rows[0]['trials']}`",
        f"- Noise variances: `{[r['noise_variance'] for r in rows]}`",
        f"- Profile delays: `{profile_metadata['delays_samples']}`",
        f"- Profile powers (dB): `{profile_metadata['tap_powers_db']}`",
        f"- Profile seed: `{base.PROFILE_SEED}`",
        f"- Payload seed: `{base.PAYLOAD_SEED}`",
        f"- Noise seed base: `{base.NOISE_SEED_BASE}`",
        "- All three methods process the same received grid in every trial.",
        "- All methods use the existing ZF detector and bit-processing chain.",
        "- Oracle uses the exact generated channel response only for equalization.",
        "- Oracle does not remove AWGN from the received waveform.",
        "",
        "## Channel-estimation and recovery results",
        "",
        "| Noise variance | Method | Mean NMSE | CRC stream 0 | CRC stream 1 | Joint CRC | Joint payload exact | Joint codeword exact | Receiver failures |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        for name in METHODS:
            lines.append(
                f"| {row['noise_variance']:g} | {name} "
                f"| {row[f'{name}_mean_nmse']:.8g} "
                f"| {row[f'{name}_stream0_crc_rate']:.3f} "
                f"| {row[f'{name}_stream1_crc_rate']:.3f} "
                f"| {row[f'{name}_joint_crc_rate']:.3f} "
                f"| {row[f'{name}_joint_payload_exact_rate']:.3f} "
                f"| {row[f'{name}_joint_codeword_exact_rate']:.3f} "
                f"| {row[f'{name}_receiver_failures']} |"
            )

    lines.extend([
        "",
        "## BER and Packet Error Rates",
        "",
        "| Noise variance | Method | BER stream 0 | BER stream 1 | Joint BER | Joint PER | Joint CRC packet error rate |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ])

    for row in rows:
        for name in METHODS:
            def format_rate(value):
                return "N/A" if value is None else f"{value:.6f}"

            lines.append(
                f"| {row['noise_variance']:g} | {name} "
                f"| {format_rate(row[f'{name}_stream0_ber_conditional'])} "
                f"| {format_rate(row[f'{name}_stream1_ber_conditional'])} "
                f"| {format_rate(row[f'{name}_joint_ber_conditional'])} "
                f"| {row[f'{name}_joint_packet_error_rate']:.3f} "
                f"| {row[f'{name}_joint_crc_packet_error_rate']:.3f} |"
            )

    lines.extend([
        "",
        "## Interpretation and limitations",
        "",
        "- Packet, CRC, and exact-recovery rates use all transmitted trials as the denominator; receiver failures count as errors.",
        "- BER is conditional on receiver trials that returned payload bits; failed trials contribute no fabricated bits.",
        "- Payload exact recovery compares the original payload bits.",
        "- Codeword exact recovery includes payload and CRC bits.",
        "- CRC success is not proof of exact payload or codeword recovery.",
        "- Oracle NMSE should be zero up to floating-point precision.",
        "- Oracle channel knowledge is diagnostic and is not available to a practical receiver.",
        "- The delay-domain estimator assumes integer delays 0 through 8 samples.",
        "- This is a custom educational multipath profile, not a standardized 3GPP TDL/CDL model.",
        "- Results apply only to the specified profile and configuration.",
        "",
    ])

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Wrote {csv_path}")
    print(f"Wrote {profile_path}")
    print(f"Wrote {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trials",
        type=int,
        default=base.DEFAULT_TRIALS,
    )
    parser.add_argument(
        "--noise-variances",
        type=float,
        nargs="+",
        default=list(base.DEFAULT_NOISE_VARIANCES),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be positive")

    if not args.noise_variances or any(
        not np.isfinite(value) or value < 0
        for value in args.noise_variances
    ):
        parser.error("noise variances must be finite and nonnegative")

    rows, profile_metadata, channel_taps = run_experiment(
        args.trials,
        args.noise_variances,
    )

    write_outputs(
        rows,
        profile_metadata,
        channel_taps,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
