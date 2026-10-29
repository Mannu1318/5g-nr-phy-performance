# Delay-Domain Channel Estimation: End-to-End Receiver Comparison

## 1. Objective

Evaluate whether the experimental delay-domain least-squares channel estimator improves end-to-end 2×2 MIMO PHY receiver performance compared with Kernel 5 linear interpolation.

The experiment extends the existing channel-estimation NMSE comparison by measuring CRC validation and exact payload/codeword recovery.

## 2. Estimators

- **Baseline:** Kernel 5 LS channel estimation followed by linear interpolation.
- **Experimental:** Delay-domain least-squares estimation using the known maximum delay of 8 samples.

Both estimators receive the same received pilot observations from each simulated trial. Neither estimator may modify the received grid or production receiver code.

## 3. Simulation configuration

- MIMO configuration: 2 transmit and 2 receive antennas.
- Channel: existing custom multipath profile with delays 0, 3, and 8 samples and tap powers 0, −3, and −8 dB.
- Modulation: QPSK.
- FFT size: 64.
- Cyclic prefix: 16 samples.
- OFDM symbols: 3, including two pilot symbols.
- Payload: 38 bits per stream, followed by CRC24A.
- Pilot value: 1 + 0j.
- Delay-domain model: integer delays 0 through 8 inclusive.
- Noise variances: 0, 0.0005, 0.001, 0.002, 0.005, and 0.01.

The experiment uses fixed channel taps, reproducible payload generation, and deterministic noise seeds. At each noise level, both estimators must process identical received observations.

## 4. Receiver processing

For each trial:

1. Generate the two payloads and their transmitted codewords.
2. Construct the resource grid and OFDM waveforms.
3. Apply the same multipath channel and one noise realization.
4. Demodulate the received waveforms into the received resource grid.
5. Estimate the channel with both estimators using the same received pilot observations.
6. Feed each channel estimate independently into the existing MIMO ZF detector.
7. Demap, descramble, and validate CRC using the existing receiver bit-processing function.
8. Compare each result against the original payloads and transmitted codewords.

No production receiver changes are permitted.

## 5. Metrics

Record the following separately for each estimator and noise variance:

- Mean channel NMSE across all four transmit-to-receive links.
- Per-stream CRC success rates and joint CRC success rate.
- Per-stream exact payload recovery rates and full-link exact payload recovery rate.
- Per-stream exact codeword recovery rates and full-link exact codeword recovery rate.
- Mean delay-domain least-squares residual and design-matrix condition number.

Payload exactness and codeword exactness are distinct metrics. Codeword exactness includes the 24 CRC bits. CRC validity alone does not guarantee exact recovery.

If a detector or estimator raises an exception, record the failure explicitly rather than silently dropping the trial. Report the failure count and denominator used for each rate.

## 6. Reproducibility and output

Use fixed master, payload, channel-profile, and noise seeds. Document the seed scheme in the report. Re-running with the same settings must produce identical metrics.

Write results to a dedicated subdirectory:

`results/integration_multipath/delay_domain_comparison/`

Expected outputs:

- `results/integration_multipath/delay_domain_comparison/receiver_comparison/receiver_comparison.csv`
- `results/integration_multipath/delay_domain_comparison/receiver_comparison/receiver_comparison_profile.json`
- `results/integration_multipath/delay_domain_comparison/receiver_comparison/receiver_comparison_report.md`

Existing multipath baseline results must not be overwritten.

## 7. Validation

- Run a small smoke test at zero noise.
- Verify both estimators receive the same observations.
- Verify output shapes, finite metrics, rate bounds, and reproducibility.
- Run the full test suite after adding dedicated experiment tests.
- Run the six-level noise sweep only after the smoke test passes.

## 8. Scope and limitations

This experiment evaluates a custom educational multipath profile, not a standardized 3GPP TDL/CDL channel. Any observed advantage applies to the tested model and configuration and must not be generalized without further experiments.
