# End-to-End AWGN Validation Specification

## 1. Objective

Evaluate the simplified end-to-end 2×2 MIMO PHY link under additive white Gaussian noise (AWGN). Measure payload recovery, CRC success, and link degradation as noise variance increases.

## 2. Existing System

The experiment uses the existing transmitter, channel, and receiver implementations without changing their behavior.

- Transmitter: CRC24A, scrambling, QPSK mapping, resource-grid construction, OFDM modulation, and cyclic prefix.
- Channel: fixed complex 2×2 flat-fading channel with optional independent complex AWGN.
- Receiver: cyclic-prefix removal, OFDM demodulation, pilot-based channel estimation, ZF detection, demapping, descrambling, and CRC validation.

## 3. Fixed Configuration

- Modulation: QPSK
- FFT size: 64
- Cyclic prefix length: 16
- OFDM symbols: 3
- Payload length: 38 bits per stream
- CRC: CRC24A
- Transmit and receive antennas: 2 each
- Channel matrix:

  \[
  H=\begin{bmatrix}
  1 & 0.2+0.1j\\
  0.1-0.1j & 1.2
  \end{bmatrix}
  \]

The channel and PHY configuration remain fixed across the initial noise sweep.

## 4. Noise Sweep

Evaluate complex noise variances:

`0`, `0.001`, `0.01`, `0.1`, `0.5`, and `1.0`.

The noise variance is the expected complex noise power per receive sample:

\[
\sigma^2=E[|w|^2]
\]

For each trial, use a reproducible random seed. Generate valid payloads with the required length and use the same trial payloads across noise levels where practical.

## 5. Measurements

For every noise variance, report:

- Number of trials
- CRC success rate for stream 0
- CRC success rate for stream 1
- Joint CRC success rate, requiring both CRCs to pass
- Exact payload recovery rate for each stream
- Full-link exact recovery rate, requiring both payloads to match
- Measured received signal power
- Measured noise power
- Nominal received SNR in dB

For zero noise, report SNR as undefined or infinite rather than attempting to take the logarithm of zero noise power.

## 6. Reproducibility

Use a fixed master seed and deterministic trial-specific seeds. Record the seed, trial count, noise variances, channel matrix, and PHY parameters in the experiment output.

## 7. Interpretation

Noise variance is not SNR. SNR depends on received signal power and noise power. The measured received signal power must be computed from the noiseless channel output for the same transmitted waveforms.

CRC success and exact payload recovery are separate measurements. Report both and investigate any disagreement rather than assuming they are interchangeable.

## 8. Validation

Before accepting the experiment:

1. Run the existing integration tests.
2. Verify that zero-noise trials recover both payloads and pass both CRCs.
3. Verify that fixed seeds reproduce results.
4. Check that measured noise power approaches the configured variance over sufficiently many samples.
5. Run repeated trials at every noise level.
6. Report measured results without assuming that every individual trial must succeed or fail at a particular variance.

## 9. Outputs

Store experiment results under `results/integration_awgn/`, including machine-readable CSV data and a Markdown report. Do not commit generated outputs until their contents have been reviewed.
