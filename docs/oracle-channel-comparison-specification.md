# Oracle Channel Comparison Experiment Specification

## 1. Objective

Investigate the contribution of channel-estimation error to end-to-end 2×2 MIMO receiver performance under a custom multipath channel and additive white Gaussian noise (AWGN).

The experiment introduces an oracle channel-estimation reference that uses the exact frequency-domain channel response calculated from the known channel taps.

The oracle receiver will be compared against:

1. Kernel 5 LS channel estimation with linear interpolation.
2. Experimental delay-domain LS channel estimation.
3. Oracle channel estimation using the true channel response.

The purpose is to distinguish errors caused by channel estimation from errors that remain when the receiver has perfect channel knowledge.

## 2. Experimental Configuration

| Parameter | Value |
|---|---|
| MIMO configuration | 2×2 |
| FFT size | 64 |
| Cyclic prefix length | 16 |
| OFDM symbols | 3 |
| Modulation | QPSK |
| Payload bits per stream | 38 |
| CRC | CRC24A |
| Channel tap delays | 0, 3, 8 samples |
| Channel tap powers | 0, -3, -8 dB |
| Maximum channel delay | 8 samples |
| Trials per noise variance | 100 |
| Noise variances | 0, 0.0005, 0.001, 0.002, 0.005, 0.01 |

The experiment will reuse the channel profile, payload, and noise seed configuration from the existing delay-domain receiver comparison.

## 3. Channel and Signal Processing

Each trial will generate two payloads and process them through the existing transmitter chain.

The transmitted OFDM waveforms will pass through the same multipath channel and AWGN model used in the existing receiver comparison experiment.

The received waveform will be demodulated into a resource grid.

All three receiver methods will process the exact same received grid for each trial.

### 3.1 Kernel 5 estimation

Use the existing MIMO channel-estimation wrapper, which applies Kernel 5 LS estimation and linear interpolation.

### 3.2 Delay-domain estimation

Reuse the existing experimental delay-domain channel estimator and its configured integer-delay support.

### 3.3 Oracle channel estimation

Calculate the exact frequency-domain channel response:

H[k] = sum_l h[l] exp(-j 2 pi k l / N)

where:

- h[l] is the channel matrix at delay l.
- k is the data-subcarrier index.
- N is the FFT size.

The resulting channel response will be supplied directly to the existing ZF detector.

The oracle will use the true channel only for data-subcarrier equalization. It will not modify the received waveform or remove AWGN.

## 4. Receiver Processing

All three methods will use the existing:

- 2×2 MIMO ZF detector.
- QPSK demapper.
- Descrambling operation.
- CRC24A verification.
- Payload recovery logic.

No production receiver implementation will be modified.

## 5. Evaluation Metrics

The experiment will record:

- Channel-estimation NMSE.
- Stream 0 and Stream 1 BER.
- Joint BER.
- Stream 0 and Stream 1 CRC success rates.
- Joint CRC success rate.
- Payload exact-recovery rates.
- Codeword exact-recovery rates.
- Packet error rates.
- Receiver execution failures.

Packet, CRC, and exact-recovery rates will use all transmitted trials as the denominator. Receiver failures will count as errors.

BER will be conditional on trials that successfully return payload bits. Failed trials will not contribute fabricated bits.

The oracle channel-estimation NMSE is expected to be zero, subject to numerical precision.

## 6. Reproducibility

The experiment will reuse the existing:

- Channel profile seed: 20261029.
- Payload seed: 20261041.
- Noise seed base: 20361033.

The default experiment will run 100 trials for each of the six configured noise variances.

The experiment will save the configuration and generated channel taps alongside its results.

## 7. Output Artifacts

Results will be stored separately from the existing estimator comparison:

results/integration_multipath/oracle_channel_comparison/

Expected files:

- oracle_comparison.csv
- oracle_comparison_profile.json
- oracle_comparison_report.md

## 8. Validation Requirements

Before accepting the experiment:

1. Confirm that all three methods process identical received grids.
2. Confirm that the oracle uses the true channel response at the data-subcarrier indices.
3. Confirm that all methods use the existing ZF detector and bit-processing implementation.
4. Verify that the oracle has negligible channel-estimation NMSE.
5. Verify exact payload and codeword recovery in the zero-noise oracle case.
6. Run the experiment with a small trial count before the full 100-trial experiment.
7. Run the relevant regression tests and the complete test suite.

## 9. Limitations

The oracle method is an ideal diagnostic reference, not a deployable channel estimator.

It assumes exact knowledge of the generated channel taps and their frequency response.

The channel profile is a custom educational multipath model and is not a standardized 3GPP TDL/CDL profile.

Results apply to the specified channel, modulation, MIMO configuration, and noise conditions.
