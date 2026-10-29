
#!/usr/bin/env python3
"""Compare channel estimators using end-to-end 2x2 MIMO receiver metrics."""

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
from integration.experimental.delay_domain_channel_estimator import (
    estimate_channel_delay_domain_diagnostics,
)
from integration.rx_chain.bit_processing import receive_bits
from integration.rx_chain.channel_estimator import estimate_mimo_channel
from integration.rx_chain.mimo_detector import detect_mimo_symbols
from integration.rx_chain.ofdm_receiver import demodulate_waveforms
from integration.tx_chain.bit_processing import transmit_bits
from integration.tx_chain.ofdm_transmitter import modulate_resource_grid
from integration.tx_chain.resource_grid import build_mimo_resource_grid
from kernels.kernel5_channel_estimation.channel_estimation_reference import (
    estimate_channel,
)

FFT_SIZE = 64
CP_LENGTH = 16
NUM_OFDM_SYMBOLS = 3
PAYLOAD_BITS = 38
MODULATION = "QPSK"
N_RNTI = 0x1234
N_ID = 0x155
Q = 0
PILOT_VALUE = 1.0 + 0.0j

DELAYS_SAMPLES = (0, 3, 8)
TAP_POWERS_DB = (0.0, -3.0, -8.0)
PROFILE_SEED = 20261029
PAYLOAD_SEED = 20261041
NOISE_SEED_BASE = 20361033
MAX_DELAY_SAMPLES = 8

DEFAULT_NOISE_VARIANCES = (0.0, 0.0005, 0.001, 0.002, 0.005, 0.01)
DEFAULT_TRIALS = 100


def make_payloads(rng):
    """Generate two reproducible payloads."""
    return [
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
    ]


def build_tx(payloads):
    """Build transmitted codewords, grid, and OFDM waveforms."""
    codewords = []
    streams = []

    for payload in payloads:
        codeword, _, symbols = transmit_bits(
            payload_bits=payload,
            n_rnti=N_RNTI,
            n_id=N_ID,
            modulation=MODULATION,
            q=Q,
        )
        codewords.append(codeword)
        streams.append(symbols)

    grid, pilot_bins, data_bins = build_mimo_resource_grid(
        data_symbols=streams,
        fft_size=FFT_SIZE,
        num_ofdm_symbols=NUM_OFDM_SYMBOLS,
        pilot_value=PILOT_VALUE,
    )
    waveforms = modulate_resource_grid(grid, cp_length=CP_LENGTH)
    return codewords, waveforms, pilot_bins, data_bins


def true_frequency_response(channel_taps, bins):
    """Compute H[k] = sum_l h[l] exp(-j*2*pi*k*l/N)."""
    response = np.zeros((2, 2, len(bins)), dtype=np.complex128)

    for delay, tap in enumerate(channel_taps):
        phase = np.exp(-2j * np.pi * delay * bins / FFT_SIZE)
        response += tap[:, :, None] * phase[None, None, :]

    return response


def calculate_nmse(estimates, truth):
    denominator = float(np.sum(np.abs(truth) ** 2))
    if denominator == 0.0:
        return float("nan")
    return float(np.sum(np.abs(estimates - truth) ** 2) / denominator)


def estimate_both(received_grid, pilot_bins, data_bins):
    """Return both estimates and diagnostics from identical pilot samples."""
    baseline = estimate_mimo_channel(
        received_grid, pilot_bins, data_bins, pilot_value=PILOT_VALUE
    )
    delay_domain = np.empty_like(baseline)
    residuals = []
    conditions = []

    for rx in range(2):
        for tx in range(2):
            observed = received_grid[rx, pilot_bins, tx]
            pilots = np.full(
                pilot_bins.size, PILOT_VALUE, dtype=np.complex128
            )
            diagnostic = estimate_channel_delay_domain_diagnostics(
                pilot_symbols=pilots,
                received_pilots=observed,
                pilot_indices=pilot_bins,
                estimate_indices=data_bins,
                fft_size=FFT_SIZE,
                max_delay_samples=MAX_DELAY_SAMPLES,
            )
            delay_domain[rx, tx] = diagnostic.frequency_response
            residuals.append(diagnostic.residual_norm)
            conditions.append(diagnostic.condition_number)

    return baseline, delay_domain, residuals, conditions


def evaluate_estimator(received_grid, channel_estimates, data_bins, payloads, codewords):
    """Run existing ZF and bit-processing stages and score one estimator."""
    detected = detect_mimo_symbols(
        received_grid=received_grid,
        channel_estimates=channel_estimates,
        data_bins=data_bins,
    )
    receiver_results = receive_bits(
        detected_symbols=detected,
        n_rnti=N_RNTI,
        n_id=N_ID,
        modulation=MODULATION,
        q=Q,
    )

    crc = [
        bool(receiver_results[s]["crc_valid"])
        for s in range(2)
    ]
    payload_exact = [
        receiver_results[s]["payload_bits"] == payloads[s]
        for s in range(2)
    ]
    codeword_exact = [
        receiver_results[s]["codeword_bits"] == codewords[s]
        for s in range(2)
    ]

    return {
        "crc": crc,
        "payload_exact": payload_exact,
        "codeword_exact": codeword_exact,
    }


def run_experiment(trials, noise_variances):
    """Run paired estimator comparisons over deterministic trials."""
    channel_taps, profile_metadata = build_multipath_profile(
        DELAYS_SAMPLES,
        TAP_POWERS_DB,
        seed=PROFILE_SEED,
        normalize_power=True,
    )
    payload_rng = np.random.default_rng(PAYLOAD_SEED)
    payloads_by_trial = [
        make_payloads(payload_rng) for _ in range(trials)
    ]
    rows = []

    for variance_index, variance in enumerate(noise_variances):
        stats = {
            estimator: {
                metric: np.zeros(2, dtype=np.int64)
                for metric in ("crc", "payload_exact", "codeword_exact")
            }
            for estimator in ("kernel5", "delay_domain")
        }
        joint = {
            estimator: {
                metric: 0
                for metric in ("crc", "payload_exact", "codeword_exact")
            }
            for estimator in ("kernel5", "delay_domain")
        }
        failures = {"kernel5": 0, "delay_domain": 0}
        nmse = {"kernel5": [], "delay_domain": []}
        residuals = []
        conditions = []

        for trial_index, payloads in enumerate(payloads_by_trial):
            codewords, tx_waveforms, pilot_bins, data_bins = build_tx(payloads)
            seed = (
                NOISE_SEED_BASE
                + variance_index * 1_000_003
                + trial_index
            )
            received_waveforms = apply_mimo_multipath_channel(
                tx_waveforms,
                channel_taps,
                noise_variance=variance,
                rng=np.random.default_rng(seed),
            )
            received_grid = demodulate_waveforms(
                received_waveforms,
                fft_size=FFT_SIZE,
                cp_length=CP_LENGTH,
            )

            truth = true_frequency_response(channel_taps, data_bins)
            baseline, delay_estimate, trial_residuals, trial_conditions = (
                estimate_both(received_grid, pilot_bins, data_bins)
            )
            nmse["kernel5"].append(calculate_nmse(baseline, truth))
            nmse["delay_domain"].append(
                calculate_nmse(delay_estimate, truth)
            )
            residuals.extend(trial_residuals)
            conditions.extend(trial_conditions)

            for name, estimates in (
                ("kernel5", baseline),
                ("delay_domain", delay_estimate),
            ):
                try:
                    outcome = evaluate_estimator(
                        received_grid, estimates, data_bins, payloads, codewords
                    )
                except (ValueError, np.linalg.LinAlgError, FloatingPointError):
                    failures[name] += 1
                    continue

                for metric in ("crc", "payload_exact", "codeword_exact"):
                    stats[name][metric] += np.asarray(
                        outcome[metric], dtype=np.int64
                    )
                    joint[name][metric] += int(all(outcome[metric]))

        row = {
            "noise_variance": float(variance),
            "trials": trials,
            "kernel5_receiver_failures": failures["kernel5"],
            "delay_domain_receiver_failures": failures["delay_domain"],
            "kernel5_mean_nmse": float(np.mean(nmse["kernel5"])),
            "delay_domain_mean_nmse": float(np.mean(nmse["delay_domain"])),
            "mean_delay_domain_residual_norm": float(np.mean(residuals)),
            "mean_design_matrix_condition_number": float(np.mean(conditions)),
        }

        for name in ("kernel5", "delay_domain"):
            successful_trials = trials - failures[name]
            row[f"{name}_rate_denominator"] = successful_trials
            for metric in ("crc", "payload_exact", "codeword_exact"):
                denominator = max(successful_trials, 1)
                row[f"{name}_stream0_{metric}_rate"] = (
                    float(stats[name][metric][0] / denominator)
                    if successful_trials else float("nan")
                )
                row[f"{name}_stream1_{metric}_rate"] = (
                    float(stats[name][metric][1] / denominator)
                    if successful_trials else float("nan")
                )
                row[f"{name}_joint_{metric}_rate"] = (
                    float(joint[name][metric] / denominator)
                    if successful_trials else float("nan")
                )

        rows.append(row)

    return rows, profile_metadata, channel_taps


def write_outputs(rows, profile_metadata, channel_taps, output_dir):
    """Write CSV, JSON profile, and Markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "receiver_comparison.csv"
    profile_path = output_dir / "receiver_comparison_profile.json"
    report_path = output_dir / "receiver_comparison_report.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    profile_document = {
        "profile_metadata": profile_metadata,
        "profile_seed": PROFILE_SEED,
        "payload_seed": PAYLOAD_SEED,
        "noise_seed_base": NOISE_SEED_BASE,
        "fft_size": FFT_SIZE,
        "cp_length": CP_LENGTH,
        "num_ofdm_symbols": NUM_OFDM_SYMBOLS,
        "modulation": MODULATION,
        "payload_bits_per_stream": PAYLOAD_BITS,
        "max_delay_samples": MAX_DELAY_SAMPLES,
        "noise_variances": [row["noise_variance"] for row in rows],
        "channel_taps_real_imag": [
            [
                [
                    [float(value.real), float(value.imag)]
                    for value in row
                ]
                for row in tap
            ]
            for tap in channel_taps
        ],
    }
    profile_path.write_text(
        json.dumps(profile_document, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# End-to-End Delay-Domain Receiver Comparison",
        "",
        f"- Trials per noise variance: `{rows[0]['trials']}`",
        f"- Noise variances: `{[r['noise_variance'] for r in rows]}`",
        f"- Profile delays: `{profile_metadata['delays_samples']}`",
        f"- Profile powers (dB): `{profile_metadata['tap_powers_db']}`",
        f"- Profile seed: `{PROFILE_SEED}`",
        f"- Payload seed: `{PAYLOAD_SEED}`",
        f"- Noise seed base: `{NOISE_SEED_BASE}`",
        "- Both estimators process the same received grid in every trial.",
        "- Receiver stages: existing 2x2 MIMO ZF detector and bit processor.",
        "",
        "## Results",
        "",
        "| Noise variance | Estimator | Mean NMSE | CRC stream 0 | CRC stream 1 | Joint CRC | Payload exact stream 0 | Payload exact stream 1 | Full-link payload exact | Codeword exact stream 0 | Codeword exact stream 1 | Full-link codeword exact | Receiver failures | Rate denominator |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        for name in ("kernel5", "delay_domain"):
            lines.append(
                f"| {row['noise_variance']:g} | {name} "
                f"| {row[f'{name}_mean_nmse']:.8g} "
                f"| {row[f'{name}_stream0_crc_rate']:.3f} "
                f"| {row[f'{name}_stream1_crc_rate']:.3f} "
                f"| {row[f'{name}_joint_crc_rate']:.3f} "
                f"| {row[f'{name}_stream0_payload_exact_rate']:.3f} "
                f"| {row[f'{name}_stream1_payload_exact_rate']:.3f} "
                f"| {row[f'{name}_joint_payload_exact_rate']:.3f} "
                f"| {row[f'{name}_stream0_codeword_exact_rate']:.3f} "
                f"| {row[f'{name}_stream1_codeword_exact_rate']:.3f} "
                f"| {row[f'{name}_joint_codeword_exact_rate']:.3f} "
                f"| {row[f'{name}_receiver_failures']} "
                f"| {row[f'{name}_rate_denominator']} |"
            )

    lines.extend([
        "",
        "## Interpretation and limitations",
        "",
        "- Rates use successful receiver trials as the denominator; receiver failures are reported separately.",
        "- Payload exact recovery compares the original 38 payload bits per stream.",
        "- Codeword exact recovery includes payload and all 24 CRC bits.",
        "- CRC success is not proof of exact payload or codeword recovery.",
        "- Channel NMSE is the normalized squared error over all four channel links and data bins.",
        "- The delay-domain estimator assumes integer delays 0 through 8 samples.",
        "- This is a custom educational multipath profile, not a standardized 3GPP TDL/CDL model.",
        "- Results apply only to the specified profile and configuration.",
        "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {csv_path}")
    print(f"Wrote {profile_path}")
    print(f"Wrote {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    parser.add_argument(
        "--noise-variances",
        type=float,
        nargs="+",
        default=list(DEFAULT_NOISE_VARIANCES),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            PROJECT_ROOT
            / "results"
            / "integration_multipath"
            / "delay_domain_comparison"
            / "receiver_comparison"
        ),
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
        args.trials, args.noise_variances
    )
    write_outputs(rows, profile_metadata, channel_taps, args.output_dir)


if __name__ == "__main__":
    main()
