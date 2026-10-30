# Delay-Domain Channel Estimation: Experimental Results

## 1. Objective

This document records the comparison between the existing Kernel 5 channel estimator and an experimental delay-domain least-squares (LS) channel estimator.

The comparison has two parts:

1. **Channel-estimation comparison:** Evaluate channel-estimation accuracy using normalized mean squared error (NMSE).
2. **End-to-end receiver comparison:** Evaluate the effect of each estimator on the existing 2×2 MIMO ZF receiver, including CRC success, payload recovery, codeword recovery, BER and PER.

The purpose is to investigate whether exploiting known finite delay support improves channel estimation and receiver performance under the selected multipath channel.

The delay-domain estimator remains experimental. The production Kernel 5 implementation and production receiver have not been replaced.

## 2. Compared Estimators

### 2.1 Existing Kernel 5 estimator

The baseline uses existing LS pilot channel estimates followed by linear interpolation across frequency-domain subcarriers.

### 2.2 Experimental delay-domain LS estimator

The experimental estimator models the channel frequency response as:

\[
H[k] = \sum_{\ell=0}^{L} h[\ell]
e^{-j2\pi k\ell/N}
\]

where:

- \(H[k]\) is the channel frequency response at subcarrier \(k\).
- \(h[\ell]\) is the channel tap at delay \(\ell\).
- \(N\) is the FFT size.
- \(L\) is the maximum modeled delay.

At pilot subcarriers, the LS observations are:

\[
z[k_p] = \frac{Y[k_p]}{X[k_p]}
\]

The estimator constructs a Fourier-domain design matrix:

\[
A_{p,\ell} = e^{-j2\pi k_p\ell/N}
\]

and solves:

\[
\hat{h} = \operatorname{argmin}_{h}\|Ah-z\|_2^2
\]

The implementation uses `numpy.linalg.lstsq` and reconstructs the channel frequency response from the estimated taps.

The modeled delay support is contiguous from sample 0 through sample 8. Intermediate delay positions are included even though the configured channel has active taps only at delays 0, 3 and 8.

This is a known-support experimental estimator. It does not automatically discover the channel delay support.

## 3. Experiment Configuration

### 3.1 Channel profile

Both experiments use the same fixed 2×2 MIMO multipath channel profile.

| Parameter | Value |
|---|---:|
| Transmit antennas | 2 |
| Receive antennas | 2 |
| FFT size | 64 |
| Active channel delays | 0, 3, 8 samples |
| Configured relative tap powers | 0, −3, −8 dB |
| Maximum modeled delay | 8 samples |
| Cyclic prefix length (receiver experiment) | 16 |
| Channel profile seed | 20261029 |

The channel profile uses integer-sample delays and a static channel.

The configured tap powers are normalized to sum to 1.0. The realized random channel tap matrices do not necessarily have exactly the configured energies.

For this profile:

- Total configured tap power: 1.0
- Total realized tap-matrix energy: approximately 1.37832

Configured tap powers and realized tap-matrix energies are different quantities and should not be interpreted interchangeably.

This is a custom educational multipath profile, not a standardized 3GPP TDL or CDL channel model.

### 3.2 Channel-estimation experiment

| Parameter | Value |
|---|---:|
| Trials per noise variance | 100 |
| Number of noise conditions | 6 |
| Total trials | 600 |
| Pilot subcarriers | 31 |
| Data subcarriers | 31 |
| FFT size | 64 |
| Maximum modeled delay | 8 samples |

Both estimators process identical received pilot observations for each trial.

### 3.3 End-to-end receiver experiment

| Parameter | Value |
|---|---|
| Modulation | QPSK |
| FFT size | 64 |
| Cyclic prefix length | 16 |
| OFDM symbols | 3 |
| Payload bits per stream | 38 |
| Streams | 2 |
| CRC | CRC24A |
| Channel estimation | Kernel 5 or delay-domain LS |
| MIMO detector | Existing 2×2 ZF |
| Trials per noise variance | 100 |

The receiver comparison uses the same received grid for both estimators in each trial. The existing receiver processing and MIMO ZF detector are retained.

### 3.4 Noise conditions and reproducibility

The evaluated noise variances are:

`0.0, 0.0005, 0.001, 0.002, 0.005, 0.01`

The receiver experiment uses these seed values:

| Random source | Seed |
|---|---:|
| Channel profile | 20261029 |
| Payload | 20261041 |
| Noise seed base | 20361033 |

Each noise condition uses 100 trials.

## 4. Channel-Estimation Results

### 4.1 Mean NMSE

The normalized mean squared error (NMSE) is used to compare estimated and true channel frequency responses.

The measured mean NMSE values are:

| Noise variance | Kernel 5 mean NMSE | Delay-domain mean NMSE |
|---:|---:|---:|
| 0.0000 | 0.00832245 | 3.24739 × 10⁻³¹ |
| 0.0005 | 0.05444479 | 0.02601095 |
| 0.0010 | 0.09971279 | 0.05181603 |
| 0.0020 | 0.19485628 | 0.10345158 |
| 0.0050 | 0.47358606 | 0.26206367 |
| 0.0100 | 0.92647117 | 0.51630887 |

The delay-domain estimator produced lower mean NMSE at all six evaluated noise variances.

For the five nonzero-noise conditions, the measured NMSE reduction relative to Kernel 5 was approximately:

| Noise variance | NMSE reduction |
|---:|---:|
| 0.0005 | 52.2% |
| 0.0010 | 48.0% |
| 0.0020 | 46.9% |
| 0.0050 | 44.6% |
| 0.0100 | 44.3% |

At zero noise, the delay-domain estimate is close to numerical floating-point precision for this channel model and known delay support. Its extremely small NMSE makes a percentage-reduction comparison misleading. The very large improvement ratio should not be interpreted as a practical percentage gain.

### 4.2 Per-link NMSE

The channel-estimation CSV contains separate NMSE values for all four MIMO links:

- RX0–TX0
- RX0–TX1
- RX1–TX0
- RX1–TX1

The delay-domain estimator produced lower NMSE for every link at every evaluated noise condition.

The individual link measurements are preserved in:

`results/integration_multipath/delay_domain_comparison_full_20261030/delay_domain_comparison.csv`

### 4.3 Least-squares diagnostics

The delay-domain estimator also records its LS residual norm and design-matrix condition number.

The mean residual norms across the six noise conditions were approximately:

| Noise variance | Mean LS residual norm |
|---:|---:|
| 0.0000 | 2.24481 × 10⁻¹⁵ |
| 0.0005 | 0.85917 |
| 0.0010 | 1.19541 |
| 0.0020 | 1.70825 |
| 0.0050 | 2.70008 |
| 0.0100 | 3.80653 |

The design-matrix condition number was approximately 1.0 across the evaluated conditions.

The increasing residual with noise is consistent with fitting noisy pilot observations. A low condition number indicates that the selected design matrix is well-conditioned for this configuration; it does not establish that every possible delay-support configuration will be well-conditioned.

## 5. End-to-End Receiver Results

### 5.1 Joint CRC success rate

Joint CRC success requires both streams to pass CRC.

| Noise variance | Kernel 5 | Delay-domain |
|---:|---:|---:|
| 0.0000 | 0.60 | 1.00 |
| 0.0005 | 0.00 | 0.03 |
| 0.0010 | 0.00 | 0.00 |
| 0.0020 | 0.00 | 0.00 |
| 0.0050 | 0.00 | 0.00 |
| 0.0100 | 0.00 | 0.00 |

At zero noise, the delay-domain receiver achieved 100% joint CRC success in the 100 trials, compared with 60% for Kernel 5.

At noise variance 0.0005, the delay-domain receiver achieved a 3% joint CRC success rate, while Kernel 5 had no successful joint CRC trials.

At higher evaluated noise variances, neither receiver achieved joint CRC success in these trials.

### 5.2 Full-link payload exact recovery

This metric checks whether both streams' original payload bits were recovered exactly.

| Noise variance | Kernel 5 | Delay-domain |
|---:|---:|---:|
| 0.0000 | 1.00 | 1.00 |
| 0.0005 | 0.04 | 0.21 |
| 0.0010 | 0.00 | 0.02 |
| 0.0020 | 0.00 | 0.00 |
| 0.0050 | 0.00 | 0.00 |
| 0.0100 | 0.00 | 0.00 |

At noise variance 0.0005, full-link payload exact recovery was 21% for the delay-domain receiver and 4% for Kernel 5.

At noise variance 0.001, the delay-domain receiver achieved 2% full-link payload exact recovery, while Kernel 5 achieved 0% in the 100 trials.

### 5.3 Joint BER

The reported BER is calculated from the compared payload bits for trials in which the receiver returned payload bits. It is therefore a conditional BER, not a packet-level failure rate.

| Noise variance | Kernel 5 joint BER | Delay-domain joint BER |
|---:|---:|---:|
| 0.0000 | 0.000000 | 0.000000 |
| 0.0005 | 0.043158 | 0.024737 |
| 0.0010 | 0.091053 | 0.066053 |
| 0.0020 | 0.161316 | 0.128158 |
| 0.0050 | 0.264737 | 0.225132 |
| 0.0100 | 0.349079 | 0.306711 |

The delay-domain receiver produced a lower measured joint BER at every nonzero-noise condition.

### 5.4 Joint packet error rate

The joint PER measures the fraction of transmitted trials in which the full-link payload was not recovered exactly. It uses all 100 transmitted trials at each noise condition.

| Noise variance | Kernel 5 joint PER | Delay-domain joint PER |
|---:|---:|---:|
| 0.0000 | 0.00 | 0.00 |
| 0.0005 | 0.96 | 0.79 |
| 0.0010 | 1.00 | 0.98 |
| 0.0020 | 1.00 | 1.00 |
| 0.0050 | 1.00 | 1.00 |
| 0.0100 | 1.00 | 1.00 |

The delay-domain receiver had a lower measured joint PER at noise variances 0.0005 and 0.001. At noise variances 0.002 and above, both receivers had a joint PER of 100% in this experiment.

### 5.5 Joint CRC packet error rate

CRC packet error rate is the fraction of transmitted trials in which the joint CRC check failed.

| Noise variance | Kernel 5 joint CRC packet error | Delay-domain joint CRC packet error |
|---:|---:|---:|
| 0.0000 | 0.40 | 0.00 |
| 0.0005 | 1.00 | 0.97 |
| 0.0010 | 1.00 | 1.00 |
| 0.0020 | 1.00 | 1.00 |
| 0.0050 | 1.00 | 1.00 |
| 0.0100 | 1.00 | 1.00 |

CRC packet error rate and payload PER are different measurements.

At zero noise, Kernel 5 had 100% full-link payload exact recovery but a 40% joint CRC packet error rate. This means payload bits could be correct while one or more CRC bits were incorrect.

CRC success also does not, by itself, prove that every payload bit or the complete codeword is correct.

### 5.6 Receiver failures and denominators

No receiver failures were recorded for either estimator at any of the six noise conditions.

Each receiver's packet, CRC and exact-recovery rates use a denominator of 100 transmitted trials per noise condition.

BER uses only payload bits returned by the receiver and reports the compared-bit denominator. No payload bits are fabricated for failed receiver trials.

The complete per-stream and joint measurements are preserved in the receiver comparison CSV.

## 6. Interpretation of Results

### 6.1 Channel-estimation accuracy

The delay-domain estimator achieved lower mean channel-estimation NMSE than the existing Kernel 5 LS plus linear-interpolation estimator at all six evaluated noise variances.

At zero noise, the delay-domain estimator recovered the channel response to near floating-point precision under the assumed delay-support model.

At nonzero noise, its mean NMSE was approximately 44% to 52% lower than Kernel 5 across the evaluated conditions.

The result is consistent with exploiting the known finite delay support rather than estimating each pilot subcarrier independently and interpolating between pilot estimates.

### 6.2 End-to-end receiver performance

The channel-estimation improvement also produced measurable receiver improvements in some evaluated conditions.

The delay-domain receiver achieved:
- Higher joint CRC success at noise variances 0 and 0.0005.
- Higher full-link payload exact-recovery rates at noise variances 0.0005 and 0.001.
- Lower conditional joint BER at every nonzero-noise condition.
- Lower joint payload PER at noise variances 0.0005 and 0.001.

However, the receiver results show that lower channel-estimation NMSE does not guarantee successful packet recovery.

At noise variance 0.002 and above, both receivers had 100% joint payload PER in the 100 trials per condition. The channel-estimation advantage alone was not sufficient to overcome the combined effects of noise, MIMO detection and hard-decision errors in these tested conditions.

### 6.3 Engineering conclusion

The experiment supports the delay-domain estimator as a useful isolated alternative when the channel's maximum delay support is known and the assumed channel model is appropriate.

It does not justify replacing the existing Kernel 5 implementation in the production receiver.

The delay-domain implementation remains experimental. A production decision would require broader channel-model coverage, robustness tests, complexity measurements and additional receiver-level validation.

## 7. Limitations and Scope

The results must be interpreted within the following experimental boundaries.

1. **Known delay support:** The estimator was configured with maximum delay 8. It was not required to discover the channel delay support automatically.

2. **Contiguous support assumption:** The estimator solves for delay taps from 0 through the configured maximum delay, inclusive. It does not independently identify a sparse set of active delays.

3. **Custom channel profile:** The experiment uses a custom static integer-delay multipath profile with active delays 0, 3 and 8 and relative tap powers of 0, -3 and -8 dB. It is not a standardized 3GPP TDL or CDL channel model.

4. **Finite configuration:** The comparison uses a 64-point FFT, 31 pilot subcarriers, 31 data subcarriers and a 2×2 MIMO receiver. Results should not be generalized automatically to other numerologies, FFT sizes, pilot patterns or antenna configurations.

5. **Finite Monte Carlo sample:** Each noise condition contains 100 trials. The reported rates are measurements from these trials, not analytical performance guarantees.

6. **Receiver scope:** The end-to-end comparison uses the existing 2×2 MIMO Zero-Forcing detector and the current hard-decision QPSK receiver chain. Other detectors, modulation orders and receiver algorithms were not evaluated here.

7. **No channel coding extension:** This experiment evaluates the existing uncoded payload and CRC-based chain. It does not establish performance with a complete 5G NR channel-coding chain.

8. **No complexity comparison:** This report compares estimation accuracy and receiver outcomes. It does not establish execution-time, memory, computational-complexity or hardware-performance advantages.

9. **No production replacement:** The delay-domain estimator is isolated experimental code. The existing Kernel 5 estimator remains unchanged.

10. **Realized channel energy:** The configured normalized tap powers sum to 1.0. The realized tap-matrix energies in the recorded channel profile do not sum to exactly 1.0 because the individual random tap matrices have finite-sample energy variation. Configured powers and realized energies are distinct quantities.

These limitations define the scope of the conclusions and identify the areas that require further investigation.

## 8. Reproducibility and Artifact Inventory

### 8.1 Experimental configuration

| Parameter | Value |
|---|---|
| FFT size | 64 |
| Cyclic prefix length | 16 |
| MIMO configuration | 2×2 |
| Modulation | QPSK |
| OFDM symbols | 3 |
| Payload bits per stream | 38 |
| Pilot value | 1 + 0j |
| Pilot subcarriers | 31 |
| Data subcarriers | 31 |
| Maximum delay | 8 |
| Active channel delays | 0, 3, 8 |
| Relative tap powers | 0, -3, -8 dB |
| Trials per noise variance | 100 |
| Noise variances | 0, 0.0005, 0.001, 0.002, 0.005, 0.01 |

The random seeds are channel 20261029, payload 20261041 and noise seed base 20361033.

### 8.2 Generated artifacts

The consolidated experiment outputs are stored separately from the earlier multipath baseline results.

| Artifact | Purpose |
|---|---|
| `delay_domain_comparison.csv` | Channel-estimation comparison measurements |
| `delay_domain_comparison_report.md` | Channel-estimation experiment report |
| `delay_domain_profile.json` | Channel-estimation configuration and metadata |
| `receiver_comparison.csv` | End-to-end receiver measurements |
| `receiver_comparison_profile.json` | Receiver configuration, seeds and metadata |
| `receiver_comparison_report.md` | Receiver comparison report |

All six files are stored under:

`results/integration_multipath/delay_domain_comparison_full_20261030/`

The receiver comparison files are stored in its `receiver_comparison/` subdirectory.

Implementation, scripts, specifications and tests:

- `integration/experimental/delay_domain_channel_estimator.py`
- `scripts/compare_delay_domain_estimator.py`
- `scripts/compare_delay_domain_receiver.py`
- `tests/integration/test_delay_domain_channel_estimator.py`
- `tests/integration/test_delay_domain_receiver_comparison.py`
- `docs/delay-domain-channel-estimation-specification.md`
- `docs/delay-domain-receiver-comparison-specification.md`

### 8.3 Reproduction and validation

Inspect the available command-line options:

- `python scripts/compare_delay_domain_estimator.py --help`
- `python scripts/compare_delay_domain_receiver.py --help`

Use the options documented by each script to reproduce the recorded configuration and select an output directory. Keep new outputs separate from the archived experiment results.

Run the focused tests:

- `pytest -q tests/integration/test_delay_domain_channel_estimator.py`
- `pytest -q tests/integration/test_delay_domain_receiver_comparison.py`

Run the full regression suite using `pytest -q`.

The recorded full regression result for this stage was 358 passed tests.

## 9. Final Conclusion

The delay-domain channel-estimation experiment demonstrates that, for the evaluated custom multipath channel and known delay support, estimating the channel in the delay domain produced lower mean NMSE than the existing Kernel 5 LS plus linear-interpolation approach.

The end-to-end receiver comparison also showed improvements in conditional BER and selected low-noise packet-recovery conditions. However, both receivers reached 100% joint payload PER at noise variance 0.002 and above in the evaluated 100-trial samples.

These findings support further investigation of delay-domain estimation, but they do not establish universal superiority or justify replacing the production Kernel 5 estimator.

The implementation remains isolated as an experimental extension. The existing production receiver and Kernel 5 implementation are preserved.
