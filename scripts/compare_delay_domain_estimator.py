
#!/usr/bin/env python3
"""Compare Kernel 5 interpolation with experimental delay-domain LS."""

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
from integration.tx_chain.bit_processing import transmit_bits
from integration.tx_chain.ofdm_transmitter import modulate_resource_grid
from integration.tx_chain.resource_grid import build_mimo_resource_grid
from integration.rx_chain.ofdm_receiver import demodulate_waveforms
from kernels.kernel5_channel_estimation.channel_estimation_reference import (
    estimate_channel,
)
from integration.experimental.delay_domain_channel_estimator import (
    estimate_channel_delay_domain_diagnostics,
)


FFT_SIZE = 64
CP_LENGTH = 16
NUM_OFDM_SYMBOLS = 3
PAYLOAD_BITS = 38
MODULATION = "QPSK"

DELAYS_SAMPLES = (0, 3, 8)
TAP_POWERS_DB = (0.0, -3.0, -8.0)
PROFILE_SEED = 20261029
PAYLOAD_SEED = 20261041
NOISE_SEED_BASE = 20361033

DEFAULT_NOISE_VARIANCES = (0.0,)
DEFAULT_TRIALS = 100
MAX_DELAY_SAMPLES = 8
PILOT_VALUE = 1.0 + 0.0j


def make_payloads(rng):
    """Generate reproducible payloads for the two transmit streams."""
    return [
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
    ]


def build_tx_waveforms(payloads):
    """Build the same OFDM waveform format used by the integrated PHY."""
    symbol_streams = [
        transmit_bits(
            payload_bits=payload,
            n_rnti=0x1234,
            n_id=0x155,
            modulation=MODULATION,
            q=0,
        )[2]
        for payload in payloads
    ]

    grid, pilot_bins, data_bins = build_mimo_resource_grid(
        data_symbols=symbol_streams,
        fft_size=FFT_SIZE,
        num_ofdm_symbols=NUM_OFDM_SYMBOLS,
        pilot_value=PILOT_VALUE,
    )
    waveforms = modulate_resource_grid(grid, cp_length=CP_LENGTH)
    return waveforms, pilot_bins, data_bins


def true_frequency_response(channel_taps, bins):
    """Compute H[k] = sum_l h[l] exp(-j*2*pi*k*l/N)."""
    response = np.zeros((2, 2, len(bins)), dtype=np.complex128)

    for delay, tap in enumerate(channel_taps):
        phase = np.exp(-2j * np.pi * delay * bins / FFT_SIZE)
        response += tap[:, :, None] * phase[None, None, :]

    return response


def calculate_nmse(estimates, truth):
    """Compute aggregate normalized squared channel-estimation error."""
    denominator = float(np.sum(np.abs(truth) ** 2))
    if denominator == 0.0:
        return float("nan")

    numerator = float(np.sum(np.abs(estimates - truth) ** 2))
    return numerator / denominator


def estimate_both(received_grid, pilot_bins, data_bins):
    """Estimate the same four links with both algorithms."""
    baseline = np.empty((2, 2, len(data_bins)), dtype=np.complex128)
    delay_domain = np.empty_like(baseline)
    residual_norms = []
    condition_numbers = []

    for rx in range(2):
        for tx in range(2):
            received_pilots = received_grid[rx, pilot_bins, tx]
            known_pilots = np.full(
                len(pilot_bins), PILOT_VALUE, dtype=np.complex128
            )

            baseline[rx, tx] = estimate_channel(
                pilot_symbols=known_pilots,
                received_pilots=received_pilots,
                pilot_indices=pilot_bins,
                estimate_indices=data_bins,
            )

            diagnostics = estimate_channel_delay_domain_diagnostics(
                pilot_symbols=known_pilots,
                received_pilots=received_pilots,
                pilot_indices=pilot_bins,
                estimate_indices=data_bins,
                fft_size=FFT_SIZE,
                max_delay_samples=MAX_DELAY_SAMPLES,
            )
            delay_domain[rx, tx] = diagnostics.frequency_response
            residual_norms.append(diagnostics.residual_norm)
            condition_numbers.append(diagnostics.condition_number)

    return baseline, delay_domain, residual_norms, condition_numbers


def run_experiment(trials, noise_variances):
    """Compare estimators on shared payload, channel, and noise observations."""
    channel_taps, profile_metadata = build_multipath_profile(
        DELAYS_SAMPLES,
        TAP_POWERS_DB,
        seed=PROFILE_SEED,
        normalize_power=True,
    )

    payload_rng = np.random.default_rng(PAYLOAD_SEED)
    payloads_per_trial = [make_payloads(payload_rng) for _ in range(trials)]
    rows = []

    for variance_index, variance in enumerate(noise_variances):
        baseline_nmse = []
        delay_nmse = []
        per_link_baseline = {(rx, tx): [] for rx in range(2) for tx in range(2)}
        per_link_delay = {(rx, tx): [] for rx in range(2) for tx in range(2)}
        residual_values = []
        condition_values = []

        for trial_index, payloads in enumerate(payloads_per_trial):
            tx_waveforms, pilot_bins, data_bins = build_tx_waveforms(payloads)
            noise_seed = (
                NOISE_SEED_BASE + variance_index * 1_000_003 + trial_index
            )

            received_waveforms = apply_mimo_multipath_channel(
                tx_waveforms,
                channel_taps,
                noise_variance=variance,
                rng=np.random.default_rng(noise_seed),
            )

            received_grid = demodulate_waveforms(
                received_waveforms,
                fft_size=FFT_SIZE,
                cp_length=CP_LENGTH,
            )

            truth = true_frequency_response(channel_taps, data_bins)
            baseline, delay_estimate, residuals, conditions = estimate_both(
                received_grid, pilot_bins, data_bins
            )

            baseline_nmse.append(calculate_nmse(baseline, truth))
            delay_nmse.append(calculate_nmse(delay_estimate, truth))
            residual_values.extend(residuals)
            condition_values.extend(conditions)

            for rx in range(2):
                for tx in range(2):
                    key = (rx, tx)
                    per_link_baseline[key].append(
                        calculate_nmse(baseline[rx, tx], truth[rx, tx])
                    )
                    per_link_delay[key].append(
                        calculate_nmse(delay_estimate[rx, tx], truth[rx, tx])
                    )

        def mean(values):
            return float(np.mean(values)) if values else float("nan")

        row = {
            "noise_variance": float(variance),
            "trials": trials,
            "pilot_count": 31,
            "data_subcarrier_count": 31,
            "fft_size": FFT_SIZE,
            "max_delay_samples": MAX_DELAY_SAMPLES,
            "baseline_mean_nmse": mean(baseline_nmse),
            "delay_domain_mean_nmse": mean(delay_nmse),
            "mean_nmse_improvement_ratio": (
                mean(baseline_nmse) / mean(delay_nmse)
                if mean(delay_nmse) > 0.0
                else float("inf")
            ),
            "mean_delay_domain_residual_norm": mean(residual_values),
            "mean_design_matrix_condition_number": mean(condition_values),
        }

        for rx in range(2):
            for tx in range(2):
                key = (rx, tx)
                row[f"baseline_nmse_rx{rx}_tx{tx}"] = mean(
                    per_link_baseline[key]
                )
                row[f"delay_nmse_rx{rx}_tx{tx}"] = mean(
                    per_link_delay[key]
                )

        rows.append(row)

    return rows, profile_metadata, channel_taps


def write_outputs(rows, profile_metadata, channel_taps, output_dir):
    """Write separate CSV, profile JSON, and a concise Markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "delay_domain_comparison.csv"
    profile_path = output_dir / "delay_domain_profile.json"
    report_path = output_dir / "delay_domain_comparison_report.md"

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    profile_document = {
        "profile_metadata": profile_metadata,
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
        "# Delay-Domain Channel Estimator Comparison",
        "",
        "## Configuration",
        "",
        f"- Trials per noise variance: `{rows[0]['trials']}`",
        f"- Noise variances: `{[row['noise_variance'] for row in rows]}`",
        f"- FFT size: `{FFT_SIZE}`",
        f"- Pilot / data bins: odd / even bins",
        f"- Maximum modeled delay: `{MAX_DELAY_SAMPLES}` samples",
        f"- Profile delays: `{profile_metadata['delays_samples']}`",
        f"- Profile powers: `{profile_metadata['tap_powers_db']}` dB",
        f"- Profile seed: `{profile_metadata['seed']}`",
        "- Both estimators use identical received pilot observations.",
        "",
        "## Results",
        "",
        "| Noise variance | Kernel 5 mean NMSE | Delay-domain mean NMSE | Baseline / delay NMSE | Mean LS residual | Mean design condition |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| {noise:.6g} | {base:.8g} | {delay:.8g} | {ratio:.6g} | "
            "{resid:.6g} | {cond:.6g} |".format(
                noise=row["noise_variance"],
                base=row["baseline_mean_nmse"],
                delay=row["delay_domain_mean_nmse"],
                ratio=row["mean_nmse_improvement_ratio"],
                resid=row["mean_delay_domain_residual_norm"],
                cond=row["mean_design_matrix_condition_number"],
            )
        )

    lines.extend([
        "",
        "## Per-link NMSE",
        "",
        "| Link | Kernel 5 NMSE | Delay-domain NMSE |",
        "|---|---:|---:|",
    ])

    for row in rows:
        for rx in range(2):
            for tx in range(2):
                lines.append(
                    f"| Noise {row['noise_variance']:g}, RX{rx}-TX{tx} | "
                    f"{row[f'baseline_nmse_rx{rx}_tx{tx}']:.8g} | "
                    f"{row[f'delay_nmse_rx{rx}_tx{tx}']:.8g} |"
                )

    lines.extend([
        "",
        "## Interpretation and limitations",
        "",
        "- NMSE is the squared channel-response error divided by the true response energy.",
        "- The delay-domain model assumes integer delays from 0 through the configured maximum.",
        "- The current profile has configured taps at delays 0, 3, and 8; intermediate modeled taps are allowed to be zero.",
        "- A lower NMSE indicates a more accurate channel estimate for this profile and setup, not guaranteed better end-to-end CRC performance.",
        "- This is an educational static multipath profile, not a standardized 3GPP TDL/CDL model.",
        "- Results are experimental artifacts; review before version control.",
        "",
        "## Output files",
        "",
        f"- CSV: `{csv_path.name}`",
        f"- Profile: `{profile_path.name}`",
        f"- Report: `{report_path.name}`",
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
