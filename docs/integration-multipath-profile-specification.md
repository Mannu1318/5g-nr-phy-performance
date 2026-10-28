# Integration Multipath Channel-Profile Specification

## 1. Purpose

Define reproducible, configurable discrete-time multipath channel profiles for
the simplified end-to-end 2x2 MIMO PHY simulation.

The profile layer will make it possible to compare channel delay spreads,
relative tap powers, cyclic-prefix lengths, and receiver performance without
changing the standalone PHY kernels.

This is an educational engineering model, not a complete 5G NR channel model.

## 2. Scope

### Included

- Integer-sample channel delays, including gaps between nonzero taps.
- Relative tap powers specified in decibels.
- Reproducible generation of complex 2x2 tap matrices from an explicit seed.
- Explicit total-power normalization behavior.
- Conversion from a sparse delay/power description to the dense tap-array
  format accepted by `apply_mimo_multipath_channel`.
- Multipath experiments across noise levels and cyclic-prefix lengths.
- BER, PER, CRC success, exact payload recovery, channel-estimation NMSE,
  and MIMO channel-conditioning measurements.
- CSV and Markdown experiment reports with recorded configuration and seeds.

### Excluded

- Standardized 3GPP TDL/CDL profile implementations.
- Fractional-sample delays or pulse shaping.
- Time-varying fading, Doppler, carrier-frequency offset, phase noise, or
  synchronization recovery.
- Inter-cell interference or multi-user scheduling.
- Coding beyond the existing CRC-protected payload path.
- Automatic selection of a cyclic-prefix length or receiver algorithm.
- Claims of standards-compliant NR conformance.

A custom profile must not be described as a standardized 3GPP channel model.

## 3. Existing integration interfaces

The current channel API is:

`apply_mimo_multipath_channel(tx_waveforms, channel_taps, noise_variance=0.0, rng=None)`

The dense `channel_taps` array has shape `(num_taps, 2, 2)`:
- Axis 0: integer sample delay.
- Axis 1: receive antenna.
- Axis 2: transmit antenna.

The current end-to-end API accepts either `channel_matrix` or `channel_taps`,
but not both. Existing flat-channel calls must remain compatible.

The multipath channel returns the same waveform length as its input. Samples
before the beginning of the transmitted waveform are zero, and the channel
does not append the convolution tail. Convolution continues across the
concatenated OFDM waveform; it is not reset at OFDM-symbol boundaries.

The profile feature must not silently alter these channel semantics.

## 4. Profile description and validation

The profile description will contain:

- `delays_samples`: one-dimensional sequence of nonnegative integer delays.
- `tap_powers_db`: one finite real value per delay, expressed in dB relative
  to the largest specified tap power.
- `seed`: an explicit nonnegative integer used for reproducible tap generation.
- `normalize_power`: an explicit Boolean controlling total-power normalization.

The initial profile API should be a Python reference helper in a dedicated
integration module. Its proposed interface is:

`build_multipath_profile(delays_samples, tap_powers_db, seed, normalize_power=True)`

The helper will return the dense complex tap array and validated metadata
describing the supplied profile, the normalization choice, and the seed.
The exact return structure must be fixed before implementation and tested.

Validation requirements:

- Delays and powers must be one-dimensional, nonempty, and equal in length.
- Delays must be unique, nonnegative integers and strictly increasing.
- Boolean values are not valid delays or seeds.
- Powers must be finite real numbers; NaN, infinity, complex values, and
  booleans are rejected.
- At least one finite path must be specified.
- The seed must be a valid nonnegative integer.
- `normalize_power` must be Boolean.
- Unsupported input shapes and types must raise clear `ValueError` or
  `TypeError` exceptions consistently with the eventual API contract.
- Dense tap-array dimensions must be `(max(delays_samples) + 1, 2, 2)`.
- Unspecified delays must be represented by zero-valued tap matrices.
- The dense tap array must contain finite values and at least one nonzero
  coefficient.

The profile helper must not modify its input arrays.

## 5. Tap-power and random-matrix conventions

Convert each relative tap power from dB to linear power:

`p_l = 10 ** (tap_powers_db[l] / 10)`

The dB values are relative powers, not amplitude magnitudes. An amplitude
scaling factor is proportional to the square root of linear power.

If `normalize_power=True`, normalize the linear tap powers so that their sum
is one. If it is false, preserve the linear powers obtained directly from the
relative dB values. Because the strongest specified tap has relative power
1 before normalization, the unnormalized total expected tap energy is the
sum of these linear powers and is not necessarily one. This flag does not
preserve an independently specified absolute channel gain; the input powers
describe relative tap strengths. Record the normalization choice and the
resulting configured linear tap powers in metadata and reports.

For the initial random model, generate independent, zero-mean circular complex
Gaussian coefficients for each receive/transmit antenna pair and each
nonzero-delay tap. Scale each tap matrix so that its expected squared
Frobenius norm equals its configured linear tap power. Thus, for a normalized
profile, the sum over taps of the expected squared Frobenius norms is one.

Use an independent, local NumPy random generator initialized from the supplied
seed. Do not depend on or mutate NumPy's global random state.

The same inputs and seed must produce exactly repeatable tap arrays in the
same supported software environment. Different seeds should normally produce
different realizations. Tests should avoid asserting that two random
realizations can never coincide as a mathematical guarantee.

A profile's configured powers describe expected tap-matrix energy, not the
exact realized energy of every random draw. Reports must distinguish configured
power from realized tap energy.

## 6. Channel and OFDM model

For receive antenna `r` and sample `n`:

`y_r[n] = sum_t sum_d H_d[r,t] * x_t[n-d] + w_r[n]`

Equivalently:

`y[:, n] = sum_d H_d @ x[:, n-d] + w[:, n]`

Here `H_d` is the 2x2 complex channel matrix at integer sample delay `d`.
The complex AWGN has expected power `E[|w|^2] = noise_variance` per receive
sample, with independent real and imaginary Gaussian components of variance
`noise_variance / 2`.

For FFT size `N`, the true frequency-domain channel matrix at FFT bin `k` is:

`H[k] = sum_d H_d * exp(-j * 2*pi*k*d/N)`

Use the same FFT-bin indices as the receiver when comparing true and estimated
channels. Validate this expression against an FFT of each dense tap sequence
and a direct frequency-response calculation.

The current transmitter uses an IFFT and prepends a cyclic prefix to each
OFDM symbol. The receiver removes the configured prefix from each concatenated
symbol and applies an FFT.

## 7. Cyclic-prefix adequacy

For a static channel with integer-sample delays and ideal receiver timing,
define the maximum channel delay as:

`D = max(delays_samples)`

A cyclic prefix of length `cp_length >= D` is sufficient to contain the
modeled channel memory under these assumptions. The number of dense tap slots
is `D + 1`, which is not the same quantity as the maximum delay.

Experiments must include:
- A suitable profile with `cp_length >= D`.
- A profile with a shorter prefix, where `cp_length < D`.
- A flat or zero-delay-only channel as a baseline.

The tests must verify the expected cyclic-prefix condition and document
observed receiver behavior. They must not assert that every insufficient-CP
case necessarily fails CRC or loses every payload bit. The amount of
interference depends on the waveform, channel realization, and receiver.

Do not change the receiver's configured prefix automatically to match the
channel profile.

## 8. End-to-end experiment design

Use the existing `simulate_mimo_link` interface and its established transmitter
and receiver processing. Add profile support through the new profile helper
and experiment tooling without breaking flat-channel use.

Experiments must record at least:

- Profile identifier or name.
- Delays in samples and configured relative powers in dB.
- Seed and normalization choice.
- Realized tap matrices or an unambiguous saved representation of them.
- FFT size, cyclic-prefix length, modulation, OFDM-symbol count, and payload
  length.
- Noise variance, trial count, and master seed.
- Mean noiseless received signal power, measured noise power, and nominal SNR.
- BER, PER, CRC success, and exact payload-recovery metrics.
- Channel-estimation NMSE and MIMO conditioning metrics when valid.
- Errors, excluded trials, or failed detections, with reasons.

Keep the payload set fixed across profile or noise-level comparisons wherever
practical. Use deterministic, documented seeds for payloads, tap generation,
and per-trial noise. Avoid accidental reuse of one random stream for unrelated
purposes.

For multipath signal-power measurements, compute the noiseless receive waveform
using the same transmitted waveform and tap array as the corresponding noisy
trial. Do not reuse the flat-channel matrix formula for a multipath result.

At zero noise, report measured noise power as zero and nominal SNR as infinity
when the noiseless signal power is positive. Handle zero received signal power
explicitly rather than producing an unexplained numeric result.

## 9. Metric definitions

### Bit error rate (BER)

For each stream and jointly, count mismatched recovered payload bits against
the original transmitted payload bits:

`BER = total payload-bit mismatches / total transmitted payload bits`

For joint BER, sum mismatches from both streams and divide by the total number
of payload bits across both streams. Do not include CRC bits in payload BER.
Report the number of compared bits so the denominator is auditable.

### Packet error rate (PER)

Treat each stream's payload in one trial as one packet. A stream packet is in
error if one or more recovered payload bits differ from its transmitted
payload. Joint packet error is recorded if either stream's payload is wrong.

`PER = erroneous packets / transmitted packets`

Report per-stream PER and joint PER separately. With this definition, PER is
the complement of exact payload-recovery rate for the same stream or joint
trial set.

### CRC success

Preserve the existing per-stream and joint CRC success rates. CRC success is
not equivalent to exact payload recovery: a CRC can pass even if payload bits
are incorrect.

### Exact recovery

Preserve the existing per-stream and full-link exact payload-recovery rates.
Preserve codeword exact-recovery rates as separate measurements.

### Received signal power and nominal SNR

Calculate received signal power from the mean squared magnitude of the
noiseless receive waveform across receive antennas and time samples.

For positive noise variance and positive signal power:

`nominal_snr_db = 10 * log10(mean_received_signal_power / noise_variance)`

Also report empirical noise power from the difference between noisy and
noiseless receive waveforms. Empirical noise power can differ from configured
variance in a finite experiment.

This SNR is an explicitly defined average receive-sample metric; it is not a
per-subcarrier post-equalization SINR or a universal NR link-quality metric.

### Channel-estimation normalized mean-square error (NMSE)

At the receiver's data-bin indices, compare `channel_estimates` with the true
frequency response derived from the exact tap array:

`NMSE = sum(|H_est - H_true|^2) / sum(|H_true|^2)`

The sums cover receive antenna, transmit antenna, and data-bin dimensions.
Report NMSE as a linear ratio; optionally report `10*log10(NMSE)` in dB.
If the denominator is zero or estimates are unavailable due to a receiver
failure, report the metric as undefined with an explicit reason.

### MIMO channel conditioning

For each data-bin channel matrix `H[k]`, compute the 2-norm condition number:

`kappa_2(H[k]) = sigma_max(H[k]) / sigma_min(H[k])`

Report summary statistics over data bins, including at least the maximum and
mean finite condition number, and count bins that are singular or numerically
ill-conditioned under a documented threshold.

A singular channel has an undefined or infinite condition number. Do not hide
singular bins by silently dropping them. Document the threshold used for
near-singular classification and keep it distinct from the ZF kernel's own
status threshold.

## 10. Receiver failures and metric accounting

The existing ZF receiver raises `ValueError` if any batch detection fails.
Experiment tooling must not mislabel such a trial as a successful decode.

A failed receiver trial must be counted and reported explicitly. Payload BER,
PER, and exact recovery metrics for a trial with no recovered payload must
follow a documented accounting policy. The implementation must not silently
discard failed trials from denominators, because doing so biases the results.

Use the following accounting policy consistently:

- A trial in which receiver detection fails and no payloads are recovered
  counts as a packet error for both streams and as a joint packet error.
- Such a trial counts as unsuccessful for CRC success and exact payload
  recovery; it must never be counted as a successful decode.
- Do not fabricate recovered bits for a failed trial. BER is calculated
  over bits from trials that produced valid recovered payloads, and must be
  labeled as conditional on successful receiver output. Report the number
  of compared bits, the number of receiver-failed trials, and the receiver
  failure rate alongside BER so the conditional denominator is transparent.
- PER and exact-recovery rates use all transmitted packets or trials in
  their denominators, including receiver failures. CRC success also uses
  all transmitted packets or trials, with receiver failures counted as
  unsuccessful.
- If a later implementation can recover one stream but not the other, its
  per-stream accounting must identify the affected streams explicitly;
  do not classify an unavailable payload as successfully recovered.

## 11. Validation plan

### Profile-helper tests

- A one-tap profile at delay zero produces a dense array with one tap slot.
- A one-tap profile at delay `d` produces `d + 1` slots, with leading
  zero-valued slots when `d > 0`.
- A profile with delays `[0, 2, 5]` produces six tap slots, with zero matrices
  at delays 1, 3, and 4.
- Repeated inputs and the same seed produce identical taps and metadata.
- Different seeds normally produce different tap realizations.
- Relative-power scaling and optional normalization follow the definitions.
- Tap matrices are finite, have the required shape, and have zero energy at
  unspecified delays.
- Invalid delays, powers, seeds, normalization flags, shapes, and empty inputs
  are rejected.
- Inputs and NumPy's global random state are not mutated.

### Channel and frequency-response tests

- A one-tap profile agrees with the existing flat-channel behavior when the
  tap matrices are equal.
- Existing causal-convolution, AWGN, and output-shape tests continue to pass.
- Direct frequency response agrees with FFT-derived tap responses.
- A complex sinusoid/tone test agrees with the expected channel response after
  excluding initial transient samples where appropriate.

### End-to-end tests

- Existing flat-channel tests and API calls remain unchanged.
- A suitable multipath profile with adequate cyclic prefix is exercised
  end to end.
- Adequate- and inadequate-prefix configurations are compared without
  requiring every inadequate-prefix case to fail.
- Zero-noise behavior is checked on a well-conditioned profile.
- Repeated experiments are deterministic.
- BER, PER, CRC, exact-recovery, NMSE, and conditioning calculations are
  checked against small hand-computable examples.
- Receiver failures are included in explicit experiment accounting.
- The complete existing test suite passes.

## 12. Experiment outputs and interpretation

Write generated CSV files and Markdown reports beneath a dedicated
multipath-results directory, separate from the existing AWGN outputs.
Do not commit generated results until they have been reviewed.

Reports must include:
- Model assumptions and excluded effects.
- Profile definition, delays, powers, seed, and normalization.
- Simulation configuration and trial count.
- Metric definitions and denominators.
- Receiver failures and undefined measurements.
- Limitations of pilot interpolation and Zero-Forcing detection.
- A clear distinction between configured tap powers and realized tap energy.

Small trial counts are useful for smoke tests but not strong statistical
evidence. Performance comparisons should use enough trials to make observed
rates meaningful, and reports should state the actual trial count.

## 13. Implementation order and acceptance criteria

Follow the repository workflow:

1. Understand and specify the profile model.
2. Review and commit this specification.
3. Implement the Python profile reference helper.
4. Add unit tests for profile validation, reproducibility, and tap construction.
5. Validate the helper against hand-computable profiles.
6. Integrate the profile into end-to-end experiments.
7. Add BER/PER, NMSE, conditioning, and cyclic-prefix experiments.
8. Run the complete regression suite.
9. Benchmark or profile only where measurements justify it.
10. Document results and limitations.

Acceptance requires a reviewed and committed specification, deterministic
profile generation, passing profile and integration tests, preserved flat
channel compatibility, verified frequency response, explicit failure
accounting, and documented experimental results.

No C implementation is required for profile generation in this milestone.
The existing C kernels remain independently validated; this work is focused
on the Python end-to-end simulation and experiment harness.
