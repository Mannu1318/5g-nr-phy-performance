# Delay-Domain Channel Estimator Comparison

## Configuration

- Trials per noise variance: `100`
- Noise variances: `[0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]`
- FFT size: `64`
- Pilot / data bins: odd / even bins
- Maximum modeled delay: `8` samples
- Profile delays: `[0, 3, 8]`
- Profile powers: `[0.0, -3.0, -8.0]` dB
- Profile seed: `20261029`
- Both estimators use identical received pilot observations.

## Results

| Noise variance | Kernel 5 mean NMSE | Delay-domain mean NMSE | Baseline / delay NMSE | Mean LS residual | Mean design condition |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0083224494 | 3.2473944e-31 | 2.56281e+28 | 2.24481e-15 | 1 |
| 0.0005 | 0.05444479 | 0.026010948 | 2.09315 | 0.859166 | 1 |
| 0.001 | 0.099712794 | 0.051816029 | 1.92436 | 1.19541 | 1 |
| 0.002 | 0.19485628 | 0.10345158 | 1.88355 | 1.70825 | 1 |
| 0.005 | 0.47358606 | 0.26206367 | 1.80714 | 2.70008 | 1 |
| 0.01 | 0.92647117 | 0.51630887 | 1.79441 | 3.80653 | 1 |

## Per-link NMSE

| Link | Kernel 5 NMSE | Delay-domain NMSE |
|---|---:|---:|
| Noise 0, RX0-TX0 | 0.0078122305 | 2.380397e-31 |
| Noise 0, RX0-TX1 | 0.0041907933 | 2.7079149e-31 |
| Noise 0, RX1-TX0 | 0.0075567088 | 3.746295e-31 |
| Noise 0, RX1-TX1 | 0.0267541 | 6.0509507e-31 |
| Noise 0.0005, RX0-TX0 | 0.063897522 | 0.031394545 |
| Noise 0.0005, RX0-TX1 | 0.029080162 | 0.013908031 |
| Noise 0.0005, RX1-TX0 | 0.063868649 | 0.032069235 |
| Noise 0.0005, RX1-TX1 | 0.12218896 | 0.054217298 |
| Noise 0.001, RX0-TX0 | 0.11835358 | 0.062936302 |
| Noise 0.001, RX0-TX1 | 0.052442737 | 0.027326684 |
| Noise 0.001, RX1-TX0 | 0.11717192 | 0.061074472 |
| Noise 0.001, RX1-TX1 | 0.2243508 | 0.11348587 |
| Noise 0.002, RX0-TX0 | 0.23626588 | 0.12407872 |
| Noise 0.002, RX0-TX1 | 0.1023309 | 0.054464646 |
| Noise 0.002, RX1-TX0 | 0.24038304 | 0.1262862 |
| Noise 0.002, RX1-TX1 | 0.41136199 | 0.2224485 |
| Noise 0.005, RX0-TX0 | 0.57484384 | 0.32408155 |
| Noise 0.005, RX0-TX1 | 0.24560677 | 0.13502688 |
| Noise 0.005, RX1-TX0 | 0.59910717 | 0.33058324 |
| Noise 0.005, RX1-TX1 | 0.98619299 | 0.54033512 |
| Noise 0.01, RX0-TX0 | 1.1339363 | 0.64411875 |
| Noise 0.01, RX0-TX1 | 0.47444223 | 0.2663135 |
| Noise 0.01, RX1-TX0 | 1.1672643 | 0.6485722 |
| Noise 0.01, RX1-TX1 | 1.9446471 | 1.0581687 |

## Interpretation and limitations

- NMSE is the squared channel-response error divided by the true response energy.
- The delay-domain model assumes integer delays from 0 through the configured maximum.
- The current profile has configured taps at delays 0, 3, and 8; intermediate modeled taps are allowed to be zero.
- A lower NMSE indicates a more accurate channel estimate for this profile and setup, not guaranteed better end-to-end CRC performance.
- This is an educational static multipath profile, not a standardized 3GPP TDL/CDL model.
- Results are experimental artifacts; review before version control.

## Output files

- CSV: `delay_domain_comparison.csv`
- Profile: `delay_domain_profile.json`
- Report: `delay_domain_comparison_report.md`
