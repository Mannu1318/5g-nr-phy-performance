# Oracle-Channel MMSE versus ZF Comparison

- Trials per noise variance: `100`
- Noise variances: `[0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]`
- Profile delays: `[0, 3, 8]`
- Profile powers (dB): `[0.0, -3.0, -8.0]`
- Profile seed: `20261029`
- Payload seed: `20261041`
- Noise seed base: `20361033`
- Both detectors process the same received grid in every trial.
- Both detectors use the exact generated channel response.
- Both detectors use the same QPSK demapper, descrambler, and CRC checker.
- ZF uses the existing production detector without modification.
- MMSE uses a noise-dependent regularization term.

## Detection and recovery results

| Noise variance | MMSE lambda | Method | CRC stream 0 | CRC stream 1 | Joint CRC | Joint payload exact | Joint codeword exact | Receiver failures |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | 0 | zf | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| 0 | 0 | mmse | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| 0.0005 | 0.032 | zf | 0.220 | 0.470 | 0.150 | 0.390 | 0.150 | 0 |
| 0.0005 | 0.032 | mmse | 0.320 | 0.800 | 0.310 | 0.500 | 0.310 | 0 |
| 0.001 | 0.064 | zf | 0.010 | 0.120 | 0.010 | 0.090 | 0.010 | 0 |
| 0.001 | 0.064 | mmse | 0.020 | 0.430 | 0.020 | 0.170 | 0.020 | 0 |
| 0.002 | 0.128 | zf | 0.000 | 0.000 | 0.000 | 0.010 | 0.000 | 0 |
| 0.002 | 0.128 | mmse | 0.000 | 0.080 | 0.000 | 0.000 | 0.000 | 0 |
| 0.005 | 0.32 | zf | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.005 | 0.32 | mmse | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | 0.64 | zf | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | 0.64 | mmse | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |

## BER and packet error rates

| Noise variance | Method | BER stream 0 | BER stream 1 | Joint BER | Joint PER | Joint CRC packet error rate |
|---:|---|---:|---:|---:|---:|---:|
| 0 | zf | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.000 |
| 0 | mmse | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.000 |
| 0.0005 | zf | 0.018421 | 0.008947 | 0.013684 | 0.610 | 0.850 |
| 0.0005 | mmse | 0.015526 | 0.002895 | 0.009211 | 0.500 | 0.690 |
| 0.001 | zf | 0.047368 | 0.026842 | 0.037105 | 0.910 | 0.990 |
| 0.001 | mmse | 0.036316 | 0.012368 | 0.024342 | 0.830 | 0.980 |
| 0.002 | zf | 0.105000 | 0.065526 | 0.085263 | 0.990 | 1.000 |
| 0.002 | mmse | 0.076579 | 0.035526 | 0.056053 | 1.000 | 1.000 |
| 0.005 | zf | 0.182105 | 0.155263 | 0.168684 | 1.000 | 1.000 |
| 0.005 | mmse | 0.158684 | 0.100000 | 0.129342 | 1.000 | 1.000 |
| 0.01 | zf | 0.258947 | 0.221053 | 0.240000 | 1.000 | 1.000 |
| 0.01 | mmse | 0.222105 | 0.162895 | 0.192500 | 1.000 | 1.000 |

## Interpretation and limitations

- Packet, CRC, and exact-recovery rates use all transmitted trials as the denominator; receiver failures count as errors.
- BER is conditional on receiver trials that returned payload bits; failed trials contribute no fabricated bits.
- Payload exact recovery compares the original payload bits.
- Codeword exact recovery includes payload and CRC bits.
- CRC success is not proof of exact payload or codeword recovery.
- Oracle channel knowledge is diagnostic and unavailable to a practical receiver.
- Oracle channel knowledge does not remove AWGN from the received signal.
- MMSE regularization uses the assumed time-domain noise variance and QPSK symbol energy.
- This custom educational multipath profile is not a standardized 3GPP TDL/CDL model.
- Results apply only to the specified channel profile and configuration.
