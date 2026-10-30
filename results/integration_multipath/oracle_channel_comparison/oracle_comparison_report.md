# End-to-End Oracle Channel Comparison

- Trials per noise variance: `100`
- Noise variances: `[0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]`
- Profile delays: `[0, 3, 8]`
- Profile powers (dB): `[0.0, -3.0, -8.0]`
- Profile seed: `20261029`
- Payload seed: `20261041`
- Noise seed base: `20361033`
- All three methods process the same received grid in every trial.
- All methods use the existing ZF detector and bit-processing chain.
- Oracle uses the exact generated channel response only for equalization.
- Oracle does not remove AWGN from the received waveform.

## Channel-estimation and recovery results

| Noise variance | Method | Mean NMSE | CRC stream 0 | CRC stream 1 | Joint CRC | Joint payload exact | Joint codeword exact | Receiver failures |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | kernel5 | 0.0083224494 | 0.600 | 1.000 | 0.600 | 1.000 | 0.600 | 0 |
| 0 | delay_domain | 3.2473944e-31 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| 0 | oracle | 0 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| 0.0005 | kernel5 | 0.05444479 | 0.020 | 0.140 | 0.000 | 0.040 | 0.000 | 0 |
| 0.0005 | delay_domain | 0.026010948 | 0.110 | 0.240 | 0.030 | 0.210 | 0.030 | 0 |
| 0.0005 | oracle | 0 | 0.220 | 0.470 | 0.150 | 0.390 | 0.150 | 0 |
| 0.001 | kernel5 | 0.099712794 | 0.000 | 0.020 | 0.000 | 0.000 | 0.000 | 0 |
| 0.001 | delay_domain | 0.051816029 | 0.000 | 0.020 | 0.000 | 0.020 | 0.000 | 0 |
| 0.001 | oracle | 0 | 0.010 | 0.120 | 0.010 | 0.090 | 0.010 | 0 |
| 0.002 | kernel5 | 0.19485628 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.002 | delay_domain | 0.10345158 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.002 | oracle | 0 | 0.000 | 0.000 | 0.000 | 0.010 | 0.000 | 0 |
| 0.005 | kernel5 | 0.47358606 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.005 | delay_domain | 0.26206367 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.005 | oracle | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | kernel5 | 0.92647117 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | delay_domain | 0.51630887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |
| 0.01 | oracle | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 |

## BER and Packet Error Rates

| Noise variance | Method | BER stream 0 | BER stream 1 | Joint BER | Joint PER | Joint CRC packet error rate |
|---:|---|---:|---:|---:|---:|---:|
| 0 | kernel5 | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.400 |
| 0 | delay_domain | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.000 |
| 0 | oracle | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.000 |
| 0.0005 | kernel5 | 0.047105 | 0.039211 | 0.043158 | 0.960 | 1.000 |
| 0.0005 | delay_domain | 0.032368 | 0.017105 | 0.024737 | 0.790 | 0.970 |
| 0.0005 | oracle | 0.018421 | 0.008947 | 0.013684 | 0.610 | 0.850 |
| 0.001 | kernel5 | 0.111316 | 0.070789 | 0.091053 | 1.000 | 1.000 |
| 0.001 | delay_domain | 0.081316 | 0.050789 | 0.066053 | 0.980 | 1.000 |
| 0.001 | oracle | 0.047368 | 0.026842 | 0.037105 | 0.910 | 0.990 |
| 0.002 | kernel5 | 0.181579 | 0.141053 | 0.161316 | 1.000 | 1.000 |
| 0.002 | delay_domain | 0.146053 | 0.110263 | 0.128158 | 1.000 | 1.000 |
| 0.002 | oracle | 0.105000 | 0.065526 | 0.085263 | 0.990 | 1.000 |
| 0.005 | kernel5 | 0.287105 | 0.242368 | 0.264737 | 1.000 | 1.000 |
| 0.005 | delay_domain | 0.247368 | 0.202895 | 0.225132 | 1.000 | 1.000 |
| 0.005 | oracle | 0.182105 | 0.155263 | 0.168684 | 1.000 | 1.000 |
| 0.01 | kernel5 | 0.364211 | 0.333947 | 0.349079 | 1.000 | 1.000 |
| 0.01 | delay_domain | 0.331842 | 0.281579 | 0.306711 | 1.000 | 1.000 |
| 0.01 | oracle | 0.258947 | 0.221053 | 0.240000 | 1.000 | 1.000 |

## Interpretation and limitations

- Packet, CRC, and exact-recovery rates use all transmitted trials as the denominator; receiver failures count as errors.
- BER is conditional on receiver trials that returned payload bits; failed trials contribute no fabricated bits.
- Payload exact recovery compares the original payload bits.
- Codeword exact recovery includes payload and CRC bits.
- CRC success is not proof of exact payload or codeword recovery.
- Oracle NMSE should be zero up to floating-point precision.
- Oracle channel knowledge is diagnostic and is not available to a practical receiver.
- The delay-domain estimator assumes integer delays 0 through 8 samples.
- This is a custom educational multipath profile, not a standardized 3GPP TDL/CDL model.
- Results apply only to the specified profile and configuration.
- Each noise condition contains 100 trials. Reported rates are empirical results for this deterministic experiment configuration and should not be interpreted as formal statistical-significance claims.
