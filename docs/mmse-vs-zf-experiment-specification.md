# MMSE vs ZF Receiver Experiment Specification

## 1. Objective

Investigate whether linear MMSE detection improves end-to-end receiver performance compared with Zero-Forcing (ZF) detection under noisy 2x2 MIMO multipath conditions.

The experiment isolates detector performance by supplying both detectors with the exact channel frequency response generated from the simulated channel taps (oracle channel knowledge).

This is an experimental investigation. It must not modify or replace the production ZF receiver.

## 2. Experimental Scope

Compare two detectors:

1. Existing ZF detector.
2. Experimental linear MMSE detector.

Both detectors must process exactly the same received frequency-domain resource grid and use the same oracle channel matrices.

The following receiver stages remain unchanged:

- QPSK hard-decision demapping.
- Descrambling.
- CRC24A checking.
- Payload recovery and comparison.

The experiment must not modify production Kernel 6, the production MIMO detector, or the existing oracle-channel comparison experiment.

## 3. Simulation Configuration

Use the same configuration as the existing oracle-channel comparison experiment:

| Parameter | Value |
|---|---:|
| MIMO configuration | 2x2 |
| FFT size | 64 |
| Cyclic prefix length | 16 |
| OFDM symbols | 3 |
| Modulation | QPSK |
| Payload bits per stream | 38 |
| CRC length | 24 bits |
| Channel delays | 0, 3, 8 samples |
| Relative tap powers | 0, -3, -8 dB |
| Trials per noise variance | 100 |
| Number of noise conditions | 6 |
| Total simulations | 600 |

Noise variances:

- 0.0
- 0.0005
- 0.001
- 0.002
- 0.005
- 0.01

Reuse the existing deterministic channel, payload, and noise seed conventions from the oracle-channel comparison experiment.

## 4. Noise and Symbol-Energy Derivation

The multipath channel adds complex AWGN:

\[
w[n]=\sqrt{\frac{\sigma^2}{2}}
\left(n_I[n]+j n_Q[n]\right)
\]

where the independent real Gaussian components have unit variance.

Therefore:

\[
E[|w[n]|^2]=\sigma^2
\]

Kernel 4 uses the unnormalized forward FFT:

\[
Y[k]=\sum_{n=0}^{N-1}y[n]e^{-j2\pi kn/N}
\]

For independent white complex noise samples, the frequency-domain noise variance is:

\[
\sigma_f^2=N_{\mathrm{FFT}}\sigma^2
\]

With FFT size 64:

\[
\boxed{\sigma_f^2=64\sigma^2}
\]

The QPSK mapper uses the constellation:

\[
x=\frac{\pm1\pm j}{\sqrt{2}}
\]

Thus:

\[
E_s=|x|^2=1
\]

The MMSE regularization parameter is consequently:

\[
\lambda=\frac{\sigma_f^2}{E_s}
\]

and for this experiment:

\[
\boxed{\lambda=64\sigma^2}
\]

The regularization parameter must be calculated from the configured time-domain complex noise variance for each trial condition.

## 5. Detector Algorithms

### 5.1 Zero-Forcing

For each data subcarrier:

\[
y=Hx+n
\]

The existing ZF detector estimates:

\[
\hat{x}_{ZF}=H^{-1}y
\]

Use the existing production ZF implementation without changing its behavior.

### 5.2 Linear MMSE

The experimental MMSE detector estimates:

\[
\boxed{
\hat{x}_{MMSE}
=
(H^H H+\lambda I)^{-1}H^H y
}
\]

where:

- \(H\) is the 2x2 oracle channel matrix for the data subcarrier.
- \(y\) is the received two-antenna frequency-domain observation.
- \(H^H\) is the conjugate transpose of \(H\).
- \(I\) is the 2x2 identity matrix.
- \(\lambda=64\sigma^2\).

Implementation requirements:

- Use `numpy.linalg.solve()`.
- Do not explicitly calculate a matrix inverse.
- Validate input shapes and finite values.
- Handle numerical failures explicitly.
- Do not silently substitute ZF when MMSE fails.
- At zero noise variance, MMSE must reduce to ZF within numerical tolerance for nonsingular channel matrices.

## 6. Fair Comparison Procedure

For every trial:

1. Generate the channel profile using the existing deterministic seed convention.
2. Generate the same payloads and CRC-protected codewords for both detectors.
3. Generate the transmitted waveforms.
4. Apply the multipath channel and configured AWGN once.
5. Demodulate the received waveforms into the frequency-domain grid once.
6. Calculate the oracle channel frequency response for the data subcarriers.
7. Pass the same received grid and oracle channel matrices to ZF and MMSE.
8. Pass each detector's output through the same existing receive-bit processing stages.
9. Score both outcomes against the same transmitted payloads and codewords.

Only the detector algorithm and its required regularization differ.

## 7. Metrics

Report the following metrics separately for ZF and MMSE:

- BER for stream 0.
- BER for stream 1.
- Joint BER.
- CRC success rate for each stream.
- Joint CRC success rate.
- Exact payload recovery rate for each stream and jointly.
- Exact codeword recovery rate for each stream and jointly.
- Packet error rate.
- Joint CRC packet error rate.
- Receiver execution failures.

Packet, CRC, and exact-recovery rates use all trials as their denominator. Failed receiver trials count as errors.

BER is calculated conditionally on trials that return payload bits. Failed trials must not contribute fabricated bits.

Clearly distinguish payload exact recovery from codeword exact recovery. Payload exact recovery excludes CRC bits; codeword exact recovery includes them.

## 8. Outputs

Write experiment outputs to a new directory:

`results/integration_multipath/mmse_zf_comparison/`

Expected artifacts:

- `mmse_zf_comparison.csv`
- `mmse_zf_comparison_report.md`
- `mmse_zf_comparison_profile.json`

The report must include:

- Configuration and seed information.
- Noise variance and corresponding MMSE regularization parameter.
- Per-detector metrics.
- Direct MMSE-versus-ZF comparisons.
- Receiver failure counts.
- Interpretation and limitations.

Do not overwrite existing experiment outputs.

## 9. Testing and Validation

Add focused tests for the experimental MMSE implementation and comparison workflow.

At minimum, validate:

1. Identity-channel behavior.
2. Nonsingular complex channel behavior.
3. Zero-noise MMSE equivalence to ZF within numerical tolerance.
4. Correct regularization scaling for each noise variance.
5. Finite output for valid finite inputs.
6. Invalid shapes and nonfinite input handling.
7. Numerical failure handling.
8. Reproducible experiment results.
9. Both detectors receive identical observations and channel matrices.
10. Output metrics and report generation.

Run a small smoke experiment before the full 600-trial experiment.

Run the complete regression suite after implementation.

## 10. Interpretation and Limitations

Oracle channel knowledge is not available in a practical receiver. It is used here only to isolate detector behavior from channel-estimation error.

The experiment uses a custom simulated 2x2 multipath profile and QPSK. Results must not be presented as universal 5G NR receiver performance.

MMSE performance must be evaluated from measured results. Do not assume it will outperform ZF at every noise level or for every metric.

Even with oracle channel knowledge, AWGN and channel-dependent noise enhancement remain present.

This experiment does not establish that MMSE alone explains all observed receiver errors. Any conclusions must be limited to the tested configuration and supported by the measured results.

## 11. Production-Code Protection

This is an isolated experimental comparison.

Do not modify:

- `integration/rx_chain/mimo_detector.py`
- `kernels/kernel6_mimo/mimo_zf_reference.py`
- Existing production transmitter or receiver stages.
- Existing oracle-channel comparison implementation.

The experimental MMSE detector and its evaluation path must remain separate from the production receiver.
