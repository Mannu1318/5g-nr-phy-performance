# Integration Multipath Channel Specification

## 1. Purpose

Extend the simplified 2x2 MIMO PHY integration with a static, discrete-time,
frequency-selective multipath channel.

The existing flat-fading channel remains supported without behavioral changes.
The multipath implementation will be developed and validated separately before
being integrated into the end-to-end simulation.

This is an educational channel model, not a complete 3GPP 5G NR channel model.

## 2. Scope

The initial implementation includes:

- Two transmit antennas and two receive antennas.
- A configurable, finite set of discrete-time channel taps.
- A time-invariant channel during one simulated waveform.
- Independent complex additive white Gaussian noise (AWGN) at each receive
  antenna and sample.
- Reproducible noise when a NumPy random generator is supplied.
- Integration with the existing OFDM transmitter, receiver, channel estimator,
  and MIMO zero-forcing detector.

The initial implementation excludes:

- Time-varying fading and Doppler.
- Standardized 3GPP TDL/CDL channel profiles.
- Fractional-sample delays.
- Explicit synchronization error, carrier-frequency offset, and phase noise.
- Interference from other users or cells.
- Automatic channel-tap normalization.

## 3. Mathematical Model

Let `x_t[n]` denote the transmitted sample from transmit antenna `t`, and let
`h[r, t, l]` denote the channel coefficient from transmit antenna `t` to receive
antenna `r` at integer delay `l`.

For receive antenna `r`:

    y_r[n] = sum_t sum_l h[r, t, l] * x_t[n-l] + w_r[n]

where:

- `r` and `t` range from 0 to 1.
- `l` ranges from 0 to `num_taps - 1`.
- Samples before the beginning of the transmitted waveform are zero.
- `w_r[n]` is independent complex AWGN when noise is enabled.

Equivalently, with one 2x2 matrix per tap:

    y[:, n] = sum_l H_l @ x[:, n-l] + w[:, n]

The channel is causal and time-invariant for the duration of the waveform.

## 4. Input and Output Shapes

### Transmitted waveforms

`tx_waveforms` must be a finite complex-compatible array of shape:

    (2, num_samples)

Both `num_samples` and the number of transmit antennas must be nonzero and
exactly as specified.

### Channel taps

`channel_taps` must be a finite complex-compatible array of shape:

    (num_taps, 2, 2)

Requirements:

- `num_taps >= 1`.
- Axis 0 indexes integer sample delay.
- Axis 1 indexes receive antenna.
- Axis 2 indexes transmit antenna.
- Tap zero is the zero-delay channel matrix.
- At least one coefficient across all taps must be nonzero.

An all-zero channel is rejected because it cannot convey a signal and would
make end-to-end channel estimation and detection uninformative.

### Received waveforms

The output shape must equal the input waveform shape:

    (2, num_samples)

For each output sample, only input samples within the transmitted waveform
are used. Samples before time zero are treated as zero. The implementation
does not append the trailing convolution tail after the last transmitted
sample, so the existing OFDM receiver can retain its current framing.

## 5. API and Backward Compatibility

Add a separate function in `integration/channel.py`:

    apply_mimo_multipath_channel(
        tx_waveforms,
        channel_taps,
        noise_variance=0.0,
        rng=None,
    )

The function must not change the signature or behavior of the existing
`apply_mimo_channel()` function.

The flat-fading function remains the reference for compatibility. A single-tap
multipath channel whose only tap is `H` must produce the same noiseless output
as `apply_mimo_channel(tx_waveforms, H)`.

For end-to-end integration, extend `simulate_mimo_link()` with an optional
`channel_taps` argument while preserving the existing positional argument
order and behavior of existing calls. The intended selection rules are:

- Existing calls supplying `channel_matrix` continue to use flat fading.
- Calls supplying `channel_taps` use the multipath function.
- Supplying both a channel matrix and channel taps is invalid.
- Supplying neither is invalid.
- The default flat-fading path remains unchanged for existing callers.

If needed, the implementation may make `channel_matrix` optional to support
multipath-only calls, provided existing positional calls remain compatible.

## 6. AWGN Definition

`noise_variance` is the expected complex noise power per receive sample:

    E[|w|^2] = noise_variance

For positive variance, generate independent noise for both receive antennas
and all output samples:

    w = sqrt(noise_variance / 2) * (N_real + j * N_imag)

where `N_real` and `N_imag` are independent standard normal random variables.

Requirements:

- Accept finite, non-negative real scalar values.
- Reject booleans, negative values, non-finite values, and non-real values.
- When variance is zero, do not add noise.
- When an RNG is supplied, repeated calls with equivalent fresh generator
  states must produce identical results.
- Add noise after summing the contributions from all channel taps.

The noise variance is not itself an SNR value. The resulting SNR also depends
on transmitted signal power and channel gain.

## 7. Convolution and OFDM Behavior

Convolution must run continuously across the entire concatenated waveform.
The channel must not reset its delay line at OFDM symbol boundaries.

For an OFDM symbol with a cyclic prefix, a static channel with maximum tap
delay `D = num_taps - 1` can be handled without inter-symbol interference
under the ideal discrete-time model when:

    cp_length >= D

This condition assumes correct symbol timing and a time-invariant channel.
When the cyclic prefix is shorter than the maximum delay, inter-symbol
interference and loss of subcarrier orthogonality may occur. The tests must
characterize this behavior rather than assume every short-CP case fails
identically.

The channel does not itself add or remove cyclic prefixes.

## 8. Frequency-Domain Channel Response

For an FFT size `N`, the channel response at FFT bin `k` is:

    H[k] = sum_l H_l * exp(-j * 2*pi*k*l/N)

This uses the same forward-FFT sign convention as NumPy's FFT.

With a sufficiently long cyclic prefix and ideal timing, each subcarrier can
be modeled by its corresponding 2x2 frequency-domain channel matrix.

Tests must compare this response against the FFT of each individual impulse
response. This provides an independent check of tap indexing, delay direction,
and FFT convention.

## 9. Channel Estimation and Detection

The existing receiver estimates each TX-to-RX channel using pilots in the
first two OFDM symbols and linear interpolation across frequency.

Multipath makes the channel frequency-selective. Therefore:

- The true channel matrix differs by subcarrier.
- Pilot interpolation accuracy depends on the frequency variation and pilot
  spacing.
- The existing pilot layout is a simplified educational arrangement, not a
  complete standardized NR DM-RS pattern.
- ZF detection can amplify noise when a channel matrix is ill-conditioned.

End-to-end exact payload recovery must only be required for test channels where
the channel response is sufficiently sampled by the existing pilots and the
effective per-subcarrier matrices are well-conditioned. Not every multipath
profile is expected to produce exact recovery with the current receiver.

## 10. Validation Requirements

The channel function must validate:

- Transmitted waveform dimensionality and shape.
- Non-empty waveform samples.
- Finite transmitted samples.
- Channel tap dimensionality and exact antenna dimensions.
- At least one channel tap.
- Finite channel coefficients.
- A nonzero overall channel.
- Valid noise variance.

Invalid inputs must raise clear `ValueError` exceptions consistent with the
existing integration channel functions.

## 11. Test Plan

### Channel-level tests

1. A single tap matches the existing flat-fading channel in a noiseless test.
2. A two-tap channel matches a manually calculated causal convolution.
3. The first output sample includes only zero-delay tap contributions.
4. Earlier samples contribute to later outputs, including across OFDM symbol
   boundaries; channel memory must not reset at symbol boundaries.
5. Output shape equals input shape and the trailing convolution tail is not
   appended.
6. Zero noise produces deterministic noiseless output.
7. A supplied RNG produces reproducible noisy output.
8. Empirical complex noise power approaches the configured variance over a
   sufficiently large sample set, using a statistically appropriate tolerance.
9. Invalid shapes, empty taps, non-finite values, all-zero taps, and invalid
   noise variances are rejected.
10. The per-bin frequency response agrees with the FFT of each channel tap
    sequence.

### Integration tests

1. Existing flat-fading integration tests continue to pass unchanged.
2. A single-tap multipath simulation agrees with the flat-fading path in the
   noiseless case.
3. A carefully selected, well-conditioned multipath channel with adequate
   cyclic prefix can recover both payloads and validate both CRCs.
4. A channel with a cyclic prefix shorter than its maximum tap delay is
   characterized through waveform or received-grid comparisons; exact bit
   failure is not assumed for every channel.
5. Noisy integration tests use fixed seeds and report recovery outcomes without
   claiming that arbitrary noise levels guarantee error-free reception.
6. Existing public function calls and return fields remain compatible.

## 12. Non-Goals

This milestone does not implement standardized NR channel profiles, realistic
large-scale path loss, Doppler, MIMO correlation models, or a complete
standards-compliant physical layer.

It does not change the individual kernel specifications or their reference
implementations.

## 13. Acceptance Criteria

The milestone is complete when:

- The specification is committed before implementation.
- The new multipath channel function passes its channel-level tests.
- The existing flat-fading API and regression tests remain intact.
- Frequency-response calculations agree with the reference FFT.
- End-to-end behavior is demonstrated for at least one suitable multipath
  channel and documented with its assumptions.
- The full regression suite passes.
- Documentation clearly states the model's educational scope and limitations.
