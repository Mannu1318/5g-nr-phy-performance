#!/usr/bin/env python3
"""Reproducible flat-versus-multipath experiment for the integrated 2x2 PHY."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from integration.channel import apply_mimo_channel, apply_mimo_multipath_channel
from integration.channel_profiles import build_multipath_profile
from integration.multipath_metrics import summarize_outcomes
from integration.simulation import simulate_mimo_link
from integration.tx_chain.bit_processing import transmit_bits
from integration.tx_chain.ofdm_transmitter import modulate_resource_grid
from integration.tx_chain.resource_grid import build_mimo_resource_grid


FLAT_CHANNEL = np.array(
    [[1.0 + 0j, 0.2 + 0.1j], [0.1 - 0.1j, 1.2 + 0j]],
    dtype=np.complex128,
)

DELAYS_SAMPLES = (0, 3, 8)
TAP_POWERS_DB = (0.0, -3.0, -8.0)
PROFILE_SEED = 20261029
MASTER_SEED = 20261030
PAYLOAD_SEED = MASTER_SEED + 11
NOISE_SEED_BASE = MASTER_SEED + 1_000_003

DEFAULT_NOISE_VARIANCES = (0.0, 0.001, 0.005, 0.01)
PAYLOAD_BITS = 38
FFT_SIZE = 64
CP_LENGTH = 16
NUM_OFDM_SYMBOLS = 3
MODULATION = "QPSK"
ILL_CONDITIONED_THRESHOLD = 1e8


def make_payloads(rng):
    """Generate two fixed-length payloads from the supplied RNG."""
    return [
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
        rng.integers(0, 2, size=PAYLOAD_BITS).tolist(),
    ]


def build_tx_waveforms(payloads):
    """Rebuild the same transmitted OFDM waveforms as the link simulation."""
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

    grid, _, data_bins = build_mimo_resource_grid(
        data_symbols=symbol_streams,
        fft_size=FFT_SIZE,
        num_ofdm_symbols=NUM_OFDM_SYMBOLS,
    )
    return modulate_resource_grid(grid, cp_length=CP_LENGTH), data_bins


def channel_output(tx_waveforms, channel, noise_variance=0.0, rng=None):
    """Apply the supplied flat channel or multipath impulse response."""
    if channel.ndim == 2:
        return apply_mimo_channel(
            tx_waveforms,
            channel,
            noise_variance=noise_variance,
            rng=rng,
        )

    return apply_mimo_multipath_channel(
        tx_waveforms,
        channel,
        noise_variance=noise_variance,
        rng=rng,
    )


def true_frequency_response(channel, data_bins):
    """Calculate H[k], with axes (receive antenna, transmit antenna, bin)."""
    if channel.ndim == 2:
        return np.repeat(channel[:, :, None], len(data_bins), axis=2)

    response = np.zeros((2, 2, len(data_bins)), dtype=np.complex128)
    for delay, tap in enumerate(channel):
        phase = np.exp(-2j * np.pi * delay * data_bins / FFT_SIZE)
        response += tap[:, :, None] * phase[None, None, :]

    return response


def calculate_nmse(estimates, true_response):
    """Return normalized channel-estimation error, or None if undefined."""
    denominator = float(np.sum(np.abs(true_response) ** 2))
    if denominator == 0.0:
        return None

    numerator = float(np.sum(np.abs(estimates - true_response) ** 2))
    return numerator / denominator


def channel_condition_metrics(response):
    """Summarize true-channel 2-norm conditioning over data subcarriers."""
    conditions = np.asarray(
        [
            np.linalg.cond(response[:, :, index], p=2)
            for index in range(response.shape[2])
        ],
        dtype=np.float64,
    )
    finite = conditions[np.isfinite(conditions)]

    return {
        "condition_number_mean_finite": (
            float(np.mean(finite)) if finite.size else None
        ),
        "condition_number_max_finite": (
            float(np.max(finite)) if finite.size else None
        ),
        "singular_or_nonfinite_bins": int(
            np.count_nonzero(~np.isfinite(conditions))
        ),
        "ill_conditioned_bins_threshold_1e8": int(
            np.count_nonzero(
                (~np.isfinite(conditions))
                | (conditions >= ILL_CONDITIONED_THRESHOLD)
            )
        ),
        "data_subcarrier_count": int(response.shape[2]),
    }


def run_one_trial(payloads, channel, noise_variance, noise_seed):
    """Run a trial and independently measure its received signal and noise."""
    tx_waveforms, data_bins = build_tx_waveforms(payloads)
    noiseless_rx = channel_output(tx_waveforms, channel)

    signal_power = float(np.mean(np.abs(noiseless_rx) ** 2))

    if noise_variance > 0.0:
        measured_rx = channel_output(
            tx_waveforms,
            channel,
            noise_variance=noise_variance,
            rng=np.random.default_rng(noise_seed),
        )
        noise = measured_rx - noiseless_rx
        measured_noise_power = float(np.mean(np.abs(noise) ** 2))
    else:
        measured_noise_power = 0.0

    try:
        result = simulate_mimo_link(
            payloads=payloads,
            channel_matrix=channel if channel.ndim == 2 else None,
            channel_taps=channel if channel.ndim == 3 else None,
            modulation=MODULATION,
            fft_size=FFT_SIZE,
            cp_length=CP_LENGTH,
            num_ofdm_symbols=NUM_OFDM_SYMBOLS,
            noise_variance=noise_variance,
            rng=np.random.default_rng(noise_seed),
        )
        failure_reason = None
    except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
        # Treat numerical/receiver failures as failed trials. Keep the reason
        # for the report instead of inventing recovered bits.
        result = None
        failure_reason = f"{type(exc).__name__}: {exc}"

    response = true_frequency_response(channel, data_bins)
    nmse = (
        calculate_nmse(result["channel_estimates"], response)
        if result is not None
        else None
    )

    return {
        "result": result,
        "failure_reason": failure_reason,
        "signal_power": signal_power,
        "measured_noise_power": measured_noise_power,
        "nmse": nmse,
        "condition_metrics": channel_condition_metrics(response),
        "max_channel_delay_samples": (
            0 if channel.ndim == 2 else int(channel.shape[0] - 1)
        ),
        "cp_covers_max_delay": (
            CP_LENGTH >= (0 if channel.ndim == 2 else channel.shape[0] - 1)
        ),
    }


def safe_mean(values):
    """Mean of available finite values, or None if none are available."""
    usable = [float(value) for value in values if value is not None]
    return float(np.mean(usable)) if usable else None


def run_experiment(trials, noise_variances):
    """Run reproducible flat and multipath sweeps using common payloads."""
    profile_taps, profile_metadata = build_multipath_profile(
        DELAYS_SAMPLES,
        TAP_POWERS_DB,
        seed=PROFILE_SEED,
        normalize_power=True,
    )

    scenarios = (
        ("flat", FLAT_CHANNEL),
        ("multipath", profile_taps),
    )

    payload_rng = np.random.default_rng(PAYLOAD_SEED)
    trial_payloads = [make_payloads(payload_rng) for _ in range(trials)]
    rows = []
    failure_summary = {}

    for scenario_index, (scenario_name, channel) in enumerate(scenarios):
        for noise_index, variance in enumerate(noise_variances):
            outcomes = []
            signal_powers = []
            noise_powers = []
            nmse_values = []
            failures = Counter()
            condition_metrics = None
            cp_covers = None
            max_delay = None

            for trial_index, payloads in enumerate(trial_payloads):
                # Common noise seeds across channel scenarios make the
                # comparisons reproducible and use matching noise samples.
                noise_seed = (
                    NOISE_SEED_BASE
                    + noise_index * 1_000_003
                    + trial_index
                )

                trial = run_one_trial(
                    payloads, channel, variance, noise_seed
                )
                outcomes.append(trial["result"])
                signal_powers.append(trial["signal_power"])
                noise_powers.append(trial["measured_noise_power"])
                condition_metrics = trial["condition_metrics"]
                cp_covers = trial["cp_covers_max_delay"]
                max_delay = trial["max_channel_delay_samples"]

                if trial["nmse"] is not None:
                    nmse_values.append(trial["nmse"])

                if trial["failure_reason"] is not None:
                    failures[trial["failure_reason"]] += 1

            metrics = summarize_outcomes(trial_payloads, outcomes)
            mean_signal_power = float(np.mean(signal_powers))
            measured_noise_power = float(np.mean(noise_powers))

            if variance == 0.0:
                nominal_snr_db = (
                    float("inf") if mean_signal_power > 0.0 else None
                )
            elif mean_signal_power > 0.0:
                nominal_snr_db = float(
                    10.0 * np.log10(mean_signal_power / variance)
                )
            else:
                nominal_snr_db = None

            row = {
                "scenario": scenario_name,
                "noise_variance": float(variance),
                "nominal_snr_db": nominal_snr_db,
                "trials": trials,
                "mean_received_signal_power": mean_signal_power,
                "measured_noise_power": measured_noise_power,
                "mean_channel_estimation_nmse": safe_mean(nmse_values),
                "nmse_trials_included": len(nmse_values),
                "max_channel_delay_samples": max_delay,
                "cp_length_samples": CP_LENGTH,
                "cp_covers_max_delay": cp_covers,
                **condition_metrics,
                **metrics,
                "failure_reasons_json": json.dumps(dict(failures), sort_keys=True),
            }
            rows.append(row)
            failure_summary[f"{scenario_name}_noise_{variance:g}"] = dict(failures)

    return rows, profile_metadata, profile_taps, failure_summary


def write_outputs(rows, profile_metadata, profile_taps, failure_summary, output_dir):
    """Write measurements, profile metadata, and a reproducible Markdown report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "multipath_sweep.csv"
    report_path = output_dir / "multipath_report.md"
    profile_path = output_dir / "multipath_profile.json"

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
            for tap in profile_taps
        ],
    }
    profile_path.write_text(
        json.dumps(profile_document, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    def fmt(value, digits=4):
        if value is None:
            return "undefined"
        if isinstance(value, (float, np.floating)) and np.isinf(value):
            return "∞" if value > 0 else "−∞"
        return f"{value:.{digits}f}" if isinstance(
            value, (float, np.floating)
        ) else str(value)

    lines = [
        "# End-to-End 2×2 MIMO Flat-versus-Multipath Experiment",
        "",
        "## Configuration",
        "",
        f"- Master seed: `{MASTER_SEED}`",
        f"- Payload seed: `{PAYLOAD_SEED}`",
        f"- Trials per scenario/noise variance: `{rows[0]['trials']}`",
        f"- Modulation: `{MODULATION}`",
        f"- FFT / cyclic prefix: `{FFT_SIZE}` / `{CP_LENGTH}` samples",
        f"- OFDM symbols: `{NUM_OFDM_SYMBOLS}`",
        f"- Payload length: `{PAYLOAD_BITS}` bits per stream",
        f"- Noise variances: `{sorted(set(row['noise_variance'] for row in rows))}`",
        f"- Ill-conditioning threshold: `{ILL_CONDITIONED_THRESHOLD:g}`",
        "",
        "## Multipath profile",
        "",
        f"- Delays: `{profile_metadata['delays_samples']}` samples",
        f"- Relative tap powers: `{profile_metadata['tap_powers_db']}` dB",
        f"- Profile seed: `{profile_metadata['seed']}`",
        f"- Power normalization: `{profile_metadata['normalize_power']}`",
        f"- Configured tap powers: `{profile_metadata['configured_tap_powers']}`",
        f"- Total configured power: `{profile_metadata['total_configured_power']:.6f}`",
        f"- Total realized tap energy: `{profile_metadata['total_realized_energy']:.6f}`",
        f"- CP covers maximum delay: `{CP_LENGTH >= max(profile_metadata['delays_samples'])}`",
        f"- Full tap matrices (real/imaginary pairs): `{profile_path.name}`",
        "",
        "Configured tap powers are expected matrix energies; realized random tap "
        "energies vary from realization to realization.",
        "",
        "## Results",
        "",
        "| Scenario | Noise variance | SNR (dB) | BER stream 0 | BER stream 1 | Joint BER | "
        "Payload PER stream 0 | Payload PER stream 1 | Joint payload PER | "
        "Joint CRC PER | Joint CRC success | Joint payload exact | "
        "Joint codeword exact | Failures | NMSE | Mean cond. | Max cond. | Ill-conditioned bins |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| {scenario} | {noise_variance:g} | {snr} | {ber0} | {ber1} | {berj} "
            "| {per0} | {per1} | {perj} | {crcper} | {crc} | {payload} | {codeword} "
            "| {fail}/{trials} | {nmse} | {condmean} | {condmax} | {ill} |".format(
                scenario=row["scenario"],
                noise_variance=row["noise_variance"],
                snr=fmt(row["nominal_snr_db"], 2),
                ber0=fmt(row["stream0_ber_conditional"]),
                ber1=fmt(row["stream1_ber_conditional"]),
                berj=fmt(row["joint_ber_conditional"]),
                per0=fmt(row["stream0_packet_error_rate"]),
                per1=fmt(row["stream1_packet_error_rate"]),
                perj=fmt(row["joint_packet_error_rate"]),
                crcper=fmt(row["joint_crc_packet_error_rate"]),
                crc=fmt(row["joint_crc_success_rate"]),
                payload=fmt(row["joint_payload_exact_rate"]),
                codeword=fmt(row["joint_codeword_exact_rate"]),
                fail=row["failed_trials"],
                trials=row["trials"],
                nmse=fmt(row["mean_channel_estimation_nmse"]),
                condmean=fmt(row["condition_number_mean_finite"], 2),
                condmax=fmt(row["condition_number_max_finite"], 2),
                ill=row["ill_conditioned_bins_threshold_1e8"],
            )
        )

    lines.extend(
        [
            "",
            "## Metric definitions and interpretation",
            "",
            "- BER counts payload-bit errors only; the 24 CRC bits are excluded. "
            "BER is conditional on successful receiver output. `None`/undefined "
            "means no bits were available for comparison.",
            "- Joint BER pools the compared payload bits from both streams and all "
            "successful trials; compared-bit counts are recorded in the CSV.",
            "- Payload PER measures trials with at least one recovered payload-bit "
            "error; failed receiver trials count as errors. Its denominator is all "
            "transmitted trials.",
            "- CRC PER measures trials where CRC validation fails on a stream; "
            "joint CRC PER counts a trial as an error if either stream fails CRC. "
            "Failed receiver trials count as CRC failures for both streams.",
            "- CRC success and exact payload/codeword recovery rates use all trials; "
            "failed receiver trials count as unsuccessful.",
            "- NMSE is the squared channel-estimation error divided by true "
            "frequency-response energy, summed over RX, TX, and data subcarriers. "
            "Failed receiver trials are excluded and counted in `nmse_trials_included`.",
            "- Condition numbers are calculated from the true channel response at "
            "each data subcarrier. The ill-conditioned threshold is 1e8 and is a "
            "diagnostic threshold, not the ZF detector's singularity threshold.",
            "- Nominal SNR is mean noiseless received waveform power divided by "
            "configured complex noise variance. Measured noise power is estimated "
            "from the generated noise samples.",
            "- The same payload set and matching noise seeds are used for both "
            "channel scenarios at each noise variance.",
            "- CP adequacy is assessed using `CP length >= maximum tap delay`. "
            "A short CP would permit inter-symbol/inter-carrier interference.",
            "- This is an educational static 2×2 MIMO channel model, not a "
            "standardized 3GPP TDL/CDL profile. Pilot interpolation and ZF have "
            "known limitations; results depend on the chosen profile and seeds.",
            "",
            "## Receiver failures",
            "",
        ]
    )

    if any(failure_summary.values()):
        for key, reasons in failure_summary.items():
            if reasons:
                lines.append(f"- `{key}`: `{json.dumps(reasons, sort_keys=True)}`")
    else:
        lines.append("No receiver failures occurred in this run.")

    lines.extend(
        [
            "",
            "## Output files",
            "",
            f"- Measurements: `{csv_path.name}`",
            f"- Profile and tap matrices: `{profile_path.name}`",
            f"- Report: `{report_path.name}`",
            "",
            "These results are generated experiment artifacts. Review them before "
            "deciding whether they belong in version control.",
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {csv_path}")
    print(f"Wrote {profile_path}")
    print(f"Wrote {report_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument(
        "--noise-variances",
        type=float,
        nargs="+",
        default=list(DEFAULT_NOISE_VARIANCES),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results" / "integration_multipath",
    )
    args = parser.parse_args()

    if args.trials < 1:
        parser.error("--trials must be positive")
    if not args.noise_variances or any(
        not np.isfinite(value) or value < 0
        for value in args.noise_variances
    ):
        parser.error("noise variances must be finite and nonnegative")

    rows, profile_metadata, profile_taps, failures = run_experiment(
        args.trials, args.noise_variances
    )
    write_outputs(
        rows,
        profile_metadata,
        profile_taps,
        failures,
        args.output_dir,
    )


if __name__ == "__main__":
    main()
