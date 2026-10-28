# End-to-End 2x2 MIMO AWGN Sweep

- Master seed: `20261028`
- Trials per noise variance: `100`
- Modulation: QPSK
- FFT size / cyclic prefix: 64 / 16
- OFDM symbols: 3
- Payload length: 38 bits per stream
- Channel matrix: `[[1, 0.2+0.1j], [0.1-0.1j, 1.2]]`

Noise variance is expected complex noise power per receive sample. Nominal SNR is calculated from average noiseless received signal power divided by the configured noise variance.

## Results

| Noise variance | Nominal SNR (dB) | CRC stream 0 | CRC stream 1 | Joint CRC | Full-link exact recovery | Measured noise power |
|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | ∞ | 1.000 | 1.000 | 1.000 | 1.000 | 0.000000 |
| 0.0005 | 10.64 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000503 |
| 0.001 | 7.63 | 0.790 | 0.980 | 0.770 | 0.820 | 0.000996 |
| 0.002 | 4.62 | 0.220 | 0.500 | 0.070 | 0.190 | 0.001998 |
| 0.003 | 2.85 | 0.020 | 0.190 | 0.000 | 0.030 | 0.003005 |
| 0.005 | 0.64 | 0.000 | 0.020 | 0.000 | 0.000 | 0.005046 |
| 0.0075 | -1.12 | 0.000 | 0.000 | 0.000 | 0.000 | 0.007512 |
| 0.01 | -2.37 | 0.000 | 0.000 | 0.000 | 0.000 | 0.009989 |
| 0.02 | -5.38 | 0.000 | 0.000 | 0.000 | 0.000 | 0.020052 |

## Interpretation notes

- Rates are empirical results from the specified number of trials.
- CRC success is not assumed to guarantee exact payload recovery.
- At zero noise, measured noise power is reported as zero and SNR as infinite.
- For nonzero variance, finite-sample measured noise power may differ from the configured variance.
