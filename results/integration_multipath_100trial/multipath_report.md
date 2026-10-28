# End-to-End 2×2 MIMO Flat-versus-Multipath Experiment

## Configuration

- Master seed: `20261030`
- Payload seed: `20261041`
- Trials per scenario/noise variance: `100`
- Modulation: `QPSK`
- FFT / cyclic prefix: `64` / `16` samples
- OFDM symbols: `3`
- Payload length: `38` bits per stream
- Noise variances: `[0.0, 0.001, 0.005, 0.01]`
- Ill-conditioning threshold: `1e+08`

## Multipath profile

- Delays: `[0, 3, 8]` samples
- Relative tap powers: `[0.0, -3.0, -8.0]` dB
- Profile seed: `20261029`
- Power normalization: `True`
- Configured tap powers: `[0.602527039541957, 0.3019788601336635, 0.09549410032437956]`
- Total configured power: `1.000000`
- Total realized tap energy: `1.378322`
- CP covers maximum delay: `True`
- Full tap matrices (real/imaginary pairs): `multipath_profile.json`

Configured tap powers are expected matrix energies; realized random tap energies vary from realization to realization.

## Results

| Scenario | Noise variance | SNR (dB) | BER stream 0 | BER stream 1 | Joint BER | Payload PER stream 0 | Payload PER stream 1 | Joint payload PER | Joint CRC PER | Joint CRC success | Joint payload exact | Joint codeword exact | Failures | NMSE | Mean cond. | Max cond. | Ill-conditioned bins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flat | 0 | ∞ | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0/100 | 0.0000 | 1.46 | 1.46 | 0 |
| flat | 0.001 | 7.61 | 0.0034 | 0.0008 | 0.0021 | 0.1200 | 0.0300 | 0.1500 | 0.2000 | 0.8000 | 0.8500 | 0.8000 | 0/100 | 0.0495 | 1.46 | 1.46 | 0 |
| flat | 0.005 | 0.63 | 0.1250 | 0.0816 | 0.1033 | 1.0000 | 0.9800 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0/100 | 0.2525 | 1.46 | 1.46 | 0 |
| flat | 0.01 | -2.39 | 0.2271 | 0.1787 | 0.2029 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0/100 | 0.5025 | 1.46 | 1.46 | 0 |
| multipath | 0 | ∞ | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.4000 | 0.6000 | 1.0000 | 0.6000 | 0/100 | 0.0083 | 3.09 | 7.98 | 0 |
| multipath | 0.001 | 4.98 | 0.1084 | 0.0763 | 0.0924 | 1.0000 | 0.9600 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0/100 | 0.0976 | 3.09 | 7.98 | 0 |
| multipath | 0.005 | -2.01 | 0.2942 | 0.2421 | 0.2682 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0/100 | 0.4676 | 3.09 | 7.98 | 0 |
| multipath | 0.01 | -5.02 | 0.3579 | 0.3363 | 0.3471 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0/100 | 0.9207 | 3.09 | 7.98 | 0 |

## Metric definitions and interpretation

- BER counts payload-bit errors only; the 24 CRC bits are excluded. BER is conditional on successful receiver output. `None`/undefined means no bits were available for comparison.
- Joint BER pools the compared payload bits from both streams and all successful trials; compared-bit counts are recorded in the CSV.
- Payload PER measures trials with at least one recovered payload-bit error; failed receiver trials count as errors. Its denominator is all transmitted trials.
- CRC PER measures trials where CRC validation fails on a stream; joint CRC PER counts a trial as an error if either stream fails CRC. Failed receiver trials count as CRC failures for both streams.
- CRC success and exact payload/codeword recovery rates use all trials; failed receiver trials count as unsuccessful.
- NMSE is the squared channel-estimation error divided by true frequency-response energy, summed over RX, TX, and data subcarriers. Failed receiver trials are excluded and counted in `nmse_trials_included`.
- Condition numbers are calculated from the true channel response at each data subcarrier. The ill-conditioned threshold is 1e8 and is a diagnostic threshold, not the ZF detector's singularity threshold.
- Nominal SNR is mean noiseless received waveform power divided by configured complex noise variance. Measured noise power is estimated from the generated noise samples.
- The same payload set and matching noise seeds are used for both channel scenarios at each noise variance.
- CP adequacy is assessed using `CP length >= maximum tap delay`. A short CP would permit inter-symbol/inter-carrier interference.
- This is an educational static 2×2 MIMO channel model, not a standardized 3GPP TDL/CDL profile. Pilot interpolation and ZF have known limitations; results depend on the chosen profile and seeds.

## Receiver failures

No receiver failures occurred in this run.

## Output files

- Measurements: `multipath_sweep.csv`
- Profile and tap matrices: `multipath_profile.json`
- Report: `multipath_report.md`

These results are generated experiment artifacts. Review them before deciding whether they belong in version control.
