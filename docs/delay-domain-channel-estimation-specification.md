# Experimental Delay-Domain Channel Estimation Specification

## 1. Purpose

Investigate delay-domain least-squares (LS) channel estimation as an alternative to the existing Kernel 5 frequency-domain LS estimation followed by linear interpolation.

The experiment targets frequency-selective channels where linear interpolation may not accurately represent the channel response between pilot subcarriers.

This is an experimental estimator for the simplified 2x2 MIMO PHY simulation. It is not a standardized 3GPP NR channel-estimation implementation.

## 2. Scope

### Included

- A single complex channel frequency response.
- Known pilot symbols and received pilot observations.
- A configurable integer delay-domain channel model.
- Least-squares estimation of candidate channel taps.
- Frequency-response reconstruction at requested FFT bins.
- Input validation and deterministic numerical behavior.
- Diagnostics for estimated taps, residual norm, and design-matrix condition number.
- Tests with exact synthetic channels, noisy observations, and incorrect delay assumptions.
- Comparisons with the existing linear-interpolation estimator using identical observations.

### Excluded

- Changes to the production receiver's channel-estimation path.
- Changes to Kernel 5's Python or C implementations.
- Standardized 3GPP TDL/CDL channel models.
- Fractional-sample delays, Doppler tracking, or time-varying channels.
- Automatic selection of the maximum channel delay.
- MMSE estimation or other regularized estimators.
- Claims of full 5G NR conformance.

## 3. Mathematical Model

Let:

- \(N\) be the FFT size.
- \(L\) be the maximum modeled delay in samples.
- \(h[\ell]\) be the complex channel tap at delay \(\ell\).
- \(X[k_p]\) be the known transmitted pilot at FFT bin \(k_p\).
- \(Y[k_p]\) be the corresponding received pilot observation.

The modeled channel response is:

\[
H[k]=\sum_{\ell=0}^{L}h[\ell]e^{-j2\pi k\ell/N}
\]

The pilot observation model is:

\[
Y[k_p]=X[k_p]H[k_p]+n[k_p]
\]

where \(n[k_p]\) represents observation noise or modeling error.

For each pilot, divide the received observation by its known nonzero pilot:

\[
z[k_p]=\frac{Y[k_p]}{X[k_p]}
\]

Construct the design matrix \(A\) as:

\[
A_{p,\ell}=e^{-j2\pi k_p\ell/N}
\]

for pilot row \(p\) and delay column \(\ell\), where \(\ell=0,\ldots,L\).

Estimate the channel taps by solving:

\[
\hat{\mathbf h}=\underset{\mathbf h}{\operatorname{argmin}}
\left\|A\mathbf h-\mathbf z\right\|_2
\]

Use `numpy.linalg.lstsq` rather than explicitly forming and inverting the normal-equation matrix.

Reconstruct the requested frequency response using:

\[
\hat H[k]=\sum_{\ell=0}^{L}\hat h[\ell]e^{-j2\pi k\ell/N}
\]

The negative exponential must match the existing forward-FFT convention in the multipath channel model.

## 4. Python API

The main function is:

`estimate_channel_delay_domain(pilot_symbols, received_pilots, pilot_indices, estimate_indices, fft_size, max_delay_samples)`

It returns a one-dimensional `numpy.complex128` array containing one channel estimate per requested FFT bin, in the order supplied.

A separate diagnostic function will expose:

- The estimated delay taps.
- The residual norm \(\|A\hat{\mathbf h}-\mathbf z\|_2\).
- The condition number of the pilot design matrix.

The diagnostic function must use the same validation and estimation logic as the main function so that the two APIs cannot silently disagree.

When `estimate_indices` is empty, the main function returns an empty
`complex128` array after validating the inputs. No least-squares fit is
performed. The diagnostic function returns empty frequency-response and
channel-tap arrays, with `NaN` residual norm and condition number to indicate
that no fit was performed.

## 5. Input Contract

### 5.1 Pilot symbols and received observations

- Both inputs must be one-dimensional numeric sequences.
- They must have equal, nonzero lengths.
- All real and imaginary components must be finite.
- Every pilot symbol must be nonzero.
- Inputs must not be modified.

### 5.2 FFT indices

- `pilot_indices` must be a one-dimensional integer sequence with one entry per pilot observation.
- `estimate_indices` must be a one-dimensional integer sequence.
- Boolean and non-integer indices are invalid.
- Every index must satisfy \(0 \le k < N\).
- Pilot indices must be unique. They need not be supplied in sorted order.
- Requested estimate indices may be supplied in any order, and output order must be preserved.
- Duplicate requested indices are permitted because the output contract preserves requested positions.
- An empty `estimate_indices` sequence produces an empty complex128 output after the remaining inputs have been validated.

### 5.3 FFT size and delay support

- `fft_size` must be a positive integer and must not be Boolean.
- `max_delay_samples` must be a nonnegative integer and must not be Boolean.
- The maximum modeled delay must be strictly less than the FFT size.
- The number of unknown taps is `max_delay_samples + 1`.

### 5.4 Identifiability

The pilot design matrix must have full column rank. If the model is underdetermined or rank-deficient, estimation must fail with a clear exception rather than return a silently unreliable solution.

A full-rank matrix can still be poorly conditioned. The diagnostic API must report its condition number. Any future condition-number rejection threshold must be justified by numerical experiments and documented separately.

Invalid input types should raise `TypeError` where appropriate; invalid dimensions, values, ranges, or rank conditions should raise `ValueError`.

## 6. Numerical Behavior

- Use complex128 calculations for the reference implementation.
- Use `numpy.linalg.lstsq` for the tap estimate.
- Do not explicitly invert the design matrix or its normal equations.
- Do not silently change the requested delay support.
- Do not clip or otherwise modify the estimated frequency response.
- The main function returns only channel estimates.
- Diagnostic results must identify the residual norm and design-matrix condition number unambiguously.

The estimator assumes that the actual channel is adequately represented by the selected delay support. If the assumed support omits real channel taps, the estimate may be biased. If too many taps are modeled, the matrix may be poorly conditioned or rank-deficient.

## 7. Validation Plan

Tests must cover:

1. Exact reconstruction of a known channel when the delay model matches the true support.
2. Correct use of the negative-exponential FFT convention.
3. Correct estimates for unsorted pilot indices and unsorted requested indices.
4. Empty requested indices.
5. Rejection of empty or mismatched pilot arrays.
6. Rejection of multidimensional, nonnumeric, or non-finite pilot inputs.
7. Rejection of zero-valued pilots.
8. Rejection of invalid index types, duplicate pilot indices, and out-of-range indices.
9. Rejection of invalid FFT sizes and maximum delays.
10. Rejection of underdetermined or rank-deficient design matrices.
11. Diagnostic consistency with the main estimator.
12. Expected estimation error under controlled additive noise.
13. Behavior when the assumed delay support is too short or unnecessarily long.
14. Regression tests confirming the production Kernel 5 estimator and existing receiver integration remain unchanged.

## 8. Comparative Evaluation

The experimental estimator must be compared with the existing Kernel 5 LS plus linear-interpolation estimator using identical pilot observations, channel realizations, noise samples, and requested subcarrier indices wherever applicable.

Record the following for each experiment:

- FFT size and pilot indices.
- Assumed maximum delay.
- Channel profile and random seed.
- Noise variance.
- Channel-estimation normalized mean squared error (NMSE), when a valid reference channel is available.
- Bit error rate (BER).
- CRC success rate.
- Design-matrix condition number and residual norm.
- Exceptions or failed trials.

Evaluation must include:

1. Exact recovery in a noiseless, correctly specified channel.
2. Controlled additive noise.
3. Multiple channel coefficient realizations.
4. Correct and deliberately mismatched delay support.
5. Comparison against linear interpolation.
6. True-channel detection results, when useful, as a diagnostic reference only.

Results must be reproducible. Any claimed improvement must be supported by recorded measurements and must not be inferred from a single trial.

## 9. Integration Boundary and Acceptance Criteria

The initial implementation must remain isolated in:

- `integration/experimental/delay_domain_channel_estimator.py`
- `tests/integration/test_delay_domain_channel_estimator.py`

The estimator must not replace or modify the production receiver's channel-estimation path. The existing Kernel 5 reference, C implementation, tests, and receiver integration must remain unchanged.

The implementation is acceptable for experimental evaluation when:

1. The Python reference follows this specification.
2. All validation and numerical tests pass.
3. Exact reconstruction succeeds for a correctly specified noiseless channel.
4. Invalid and rank-deficient inputs fail clearly.
5. Diagnostics agree with the main estimator.
6. Incorrect delay support is evaluated and documented.
7. Comparative experiments use reproducible configurations and report their metrics.
8. The existing regression suite continues to pass.

This specification does not authorize production integration, C implementation, performance claims, or a commit or push. Those steps require a separate review of the experimental results.
