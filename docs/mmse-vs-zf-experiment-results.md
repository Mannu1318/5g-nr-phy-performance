# MMSE vs ZF Receiver Experiment Results

## 1. Objective

Evaluate whether experimental linear Minimum Mean Square Error (MMSE)
detection improves receiver performance compared with the existing
Zero-Forcing (ZF) detector under noisy 2x2 MIMO multipath conditions.

Both detectors receive the same observations and exact channel frequency
response. This oracle-channel setup isolates detector behavior from channel
estimation errors.

This experiment is diagnostic. It does not replace or modify the production
ZF detector.

## 2. Experimental Configuration

| Parameter | Value |
|---|---:|
| MIMO configuration | 2x2 |
| FFT size | 64 |
| Cyclic prefix | 16 |
| OFDM symbols | 3 |
| Modulation | QPSK |
| Payload bits per stream | 38 |
| CRC length | 24 bits |
| Channel delays | 0, 3, 8 samples |
| Relative tap powers | 0, -3, -8 dB |
| Trials per noise condition | 100 |
| Noise conditions | 6 |
| Total paired trials | 600 |

Noise variances:

`0, 0.0005, 0.001, 0.002, 0.005, 0.01`

Deterministic seeds:

| Parameter | Seed |
|---|---:|
| Channel profile | 20261029 |
| Payload | 20261041 |
| Noise seed base | 20361033 |

The experiment reuses the deterministic seed conventions from the
oracle-channel receiver comparison.

## 3. Detector Algorithms

### Zero-Forcing

The existing production detector estimates:

\[
\hat{x}_{ZF}=H^{-1}y
\]

The production implementation is used without modification.

### Linear MMSE

The experimental detector estimates:

\[
\hat{x}_{MMSE}
=
(H^H H+\lambda I)^{-1}H^H y
\]

The implementation uses `numpy.linalg.solve()` rather than explicitly
calculating a matrix inverse.

The regularization parameter is:

\[
\lambda=\frac{\sigma_f^2}{E_s}
\]

The channel applies complex AWGN with time-domain variance \(\sigma^2\).
The unnormalized 64-point FFT gives:

\[
\sigma_f^2=64\sigma^2
\]

QPSK has symbol energy \(E_s=1\), so:

\[
\boxed{\lambda=64\sigma^2}
\]

| Time-domain noise variance | Frequency-domain noise variance | MMSE lambda |
|---:|---:|---:|
| 0 | 0 | 0 |
| 0.0005 | 0.032 | 0.032 |
| 0.001 | 0.064 | 0.064 |
| 0.002 | 0.128 | 0.128 |
| 0.005 | 0.32 | 0.32 |
| 0.01 | 0.64 | 0.64 |

At zero noise, the regularization is zero and MMSE reduces to the ZF
solution for nonsingular channel matrices.

## 4. Fair Comparison Methodology

For each trial:

1. Generate the deterministic multipath channel and payloads.
2. Construct the same CRC-protected transmitted codewords.
3. Transmit both streams through the same simulated channel.
4. Add AWGN once and demodulate the received waveforms once.
5. Calculate the exact channel frequency response from the generated taps.
6. Give both detectors the same received grid and oracle channel matrices.
7. Apply the same QPSK demapping, descrambling, and CRC processing.
8. Compare recovered payloads and codewords against the same transmitted
   reference data.

The detector algorithm is the only intended difference.

## 5. Results

### 5.1 BER comparison

| Noise variance | ZF stream 0 | MMSE stream 0 | ZF stream 1 | MMSE stream 1 | ZF joint | MMSE joint |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 0.0005 | 0.018421 | 0.015526 | 0.008947 | 0.002895 | 0.013684 | 0.009211 |
| 0.001 | 0.047368 | 0.036316 | 0.026842 | 0.012368 | 0.037105 | 0.024342 |
| 0.002 | 0.105000 | 0.076579 | 0.065526 | 0.035526 | 0.085263 | 0.056053 |
| 0.005 | 0.182105 | 0.158684 | 0.155263 | 0.100000 | 0.168684 | 0.129342 |
| 0.01 | 0.258947 | 0.222105 | 0.221053 | 0.162895 | 0.240000 | 0.192500 |

MMSE achieved lower measured BER than ZF at every tested non-zero noise
variance.

The relative reduction in joint BER was:

| Noise variance | Joint BER reduction with MMSE |
|---:|---:|
| 0.0005 | 32.7% |
| 0.001 | 34.4% |
| 0.002 | 34.2% |
| 0.005 | 23.3% |
| 0.01 | 19.8% |

These reductions are calculated relative to the corresponding ZF joint BER.

### 5.2 CRC and exact recovery

| Noise variance | Method | Stream 0 CRC | Stream 1 CRC | Joint CRC | Joint payload exact | Joint codeword exact |
|---:|---|---:|---:|---:|---:|---:|
| 0 | ZF | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 0 | MMSE | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 0.0005 | ZF | 0.22 | 0.47 | 0.15 | 0.39 | 0.15 |
| 0.0005 | MMSE | 0.32 | 0.80 | 0.31 | 0.50 | 0.31 |
| 0.001 | ZF | 0.01 | 0.12 | 0.01 | 0.09 | 0.01 |
| 0.001 | MMSE | 0.02 | 0.43 | 0.02 | 0.17 | 0.02 |
| 0.002 | ZF | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 |
| 0.002 | MMSE | 0.00 | 0.08 | 0.00 | 0.00 | 0.00 |
| 0.005 | ZF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 0.005 | MMSE | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 0.01 | ZF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| 0.01 | MMSE | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

At noise variance 0.0005, MMSE increased joint CRC success from 15% to 31%
and joint payload exact recovery from 39% to 50%.

At 0.001, joint payload exact recovery increased from 9% to 17%. Joint CRC
success increased from 1% to 2%.

Neither detector achieved joint CRC success at 0.002 or higher.

### 5.3 Packet error rates

| Noise variance | ZF joint PER | MMSE joint PER | ZF joint CRC PER | MMSE joint CRC PER |
|---:|---:|---:|---:|---:|
| 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| 0.0005 | 0.61 | 0.50 | 0.85 | 0.69 |
| 0.001 | 0.91 | 0.83 | 0.99 | 0.98 |
| 0.002 | 0.99 | 1.00 | 1.00 | 1.00 |
| 0.005 | 1.00 | 1.00 | 1.00 | 1.00 |
| 0.01 | 1.00 | 1.00 | 1.00 | 1.00 |

At noise variance 0.002, MMSE has lower BER but a slightly higher joint
packet error rate. This is possible because packet success requires every
payload bit in both streams to be correct. Reducing the number of bit errors
does not necessarily eliminate all errors in a packet.

### 5.4 Receiver failures

Both detectors had zero receiver execution failures in all 600 paired
trials. Each noise condition used all 100 trials as the denominator for
packet, CRC, and exact-recovery rates.

BER was calculated conditionally on trials that returned payload bits.
Each stream had 3,800 compared payload bits per detector and noise
condition, giving 7,600 joint compared bits.

## 6. Interpretation

The experiment provides evidence that MMSE regularization reduces measured
bit errors relative to ZF for this simulated 2x2 QPSK multipath channel.

The observed BER improvement is consistent with MMSE mitigating the
noise-enhancement behavior associated with ZF inversion. MMSE regularization
balances channel inversion against noise amplification rather than forcing
an exact channel inverse.

The benefit is visible in both streams and at every tested non-zero noise
variance. However, lower BER does not guarantee successful packet recovery.
At moderate and high noise levels, both detectors still have very poor
packet-level performance.

The zero-noise results also confirm that the experimental MMSE detector
reduces to the ZF solution under the tested nonsingular channel conditions.

## 7. Limitations

- The exact channel response is supplied to both detectors. A practical
  receiver would have channel-estimation errors.
- Oracle channel knowledge does not remove AWGN.
- The channel profile is a custom educational multipath model, not a
  standardized 3GPP TDL or CDL channel model.
- The experiment uses 2x2 MIMO and QPSK only.
- Each noise condition has 100 trials. Results are descriptive and do not
  constitute a formal statistical significance analysis.
- The regularization assumes the configured noise variance and known QPSK
  symbol energy.
- Results do not establish universal MMSE superiority or prove that ZF
  noise enhancement is the only cause of receiver errors.

## 8. Conclusion

For the tested oracle-channel 2x2 MIMO configuration, MMSE consistently
reduced BER compared with the existing ZF detector under non-zero noise.

MMSE also improved joint CRC and exact payload recovery at the two lowest
non-zero noise variances. At higher noise levels, packet recovery remained
unreliable for both detectors despite MMSE's lower BER.

The experimental MMSE implementation remains separate from the production
receiver. The production ZF detector and Kernel 6 were not modified.

## 9. Reproducibility and Artifacts

Experiment specification:

`docs/mmse-vs-zf-experiment-specification.md`

Implementation:

- `integration/rx_chain/mmse_detector.py`
- `scripts/compare_mmse_zf_receiver.py`

Tests:

- `tests/integration/test_mmse_detector.py`
- `tests/integration/test_mmse_zf_comparison.py`

Generated results:

- `results/integration_multipath/mmse_zf_comparison/mmse_zf_comparison.csv`
- `results/integration_multipath/mmse_zf_comparison/mmse_zf_comparison_profile.json`
- `results/integration_multipath/mmse_zf_comparison/mmse_zf_comparison_report.md`
