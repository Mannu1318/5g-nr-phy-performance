# End-to-End Delay-Domain Receiver Comparison

- Trials per noise variance: `100`
- Noise variances: `[0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]`
- Profile delays: `[0, 3, 8]`
- Profile powers (dB): `[0.0, -3.0, -8.0]`
- Profile seed: `20261029`
- Payload seed: `20261041`
- Noise seed base: `20361033`
- Both estimators process the same received grid in every trial.
- Receiver stages: existing 2x2 MIMO ZF detector and bit processor.

## Results

| Noise variance | Estimator | Mean NMSE | CRC stream 0 | CRC stream 1 | Joint CRC | Payload exact stream 0 | Payload exact stream 1 | Full-link payload exact | Codeword exact stream 0 | Codeword exact stream 1 | Full-link codeword exact | Receiver failures | Rate denominator |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | kernel5 | 0.0083224494 | 0.600 | 1.000 | 0.600 | 1.000 | 1.000 | 1.000 | 0.600 | 1.000 | 0.600 | 0 | 100 |
| 0 | delay_domain | 3.2473944e-31 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 100 |
| 0.0005 | kernel5 | 0.05444479 | 0.020 | 0.140 | 0.000 | 0.090 | 0.260 | 0.040 | 0.020 | 0.140 | 0.000 | 0 | 100 |
| 0.0005 | delay_domain | 0.026010948 | 0.110 | 0.240 | 0.030 | 0.290 | 0.500 | 0.210 | 0.110 | 0.240 | 0.030 | 0 | 100 |
| 0.001 | kernel5 | 0.099712794 | 0.000 | 0.020 | 0.000 | 0.020 | 0.050 | 0.000 | 0.000 | 0.020 | 0.000 | 0 | 100 |
| 0.001 | delay_domain | 0.051816029 | 0.000 | 0.020 | 0.000 | 0.060 | 0.140 | 0.020 | 0.000 | 0.020 | 0.000 | 0 | 100 |
| 0.002 | kernel5 | 0.19485628 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |
| 0.002 | delay_domain | 0.10345158 | 0.000 | 0.000 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |
| 0.005 | kernel5 | 0.47358606 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |
| 0.005 | delay_domain | 0.26206367 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |
| 0.01 | kernel5 | 0.92647117 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |
| 0.01 | delay_domain | 0.51630887 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0 | 100 |

## Interpretation and limitations

- Rates use successful receiver trials as the denominator; receiver failures are reported separately.
- Payload exact recovery compares the original 38 payload bits per stream.
- Codeword exact recovery includes payload and all 24 CRC bits.
- CRC success is not proof of exact payload or codeword recovery.
- Channel NMSE is the normalized squared error over all four channel links and data bins.
- The delay-domain estimator assumes integer delays 0 through 8 samples.
- This is a custom educational multipath profile, not a standardized 3GPP TDL/CDL model.
- Results apply only to the specified profile and configuration.
