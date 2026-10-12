# Kernel 5 — 5G NR Channel Estimation Specification

## 1. Purpose

Kernel 5 implements a simplified pilot-based channel estimator for the
5G NR PHY performance-engineering project.

The kernel estimates the complex channel frequency response from known
reference symbols and received pilot observations. It will provide a
Python reference implementation followed by a scalar C implementation.

The objectives are:

* Define a mathematically testable channel-estimation operation.
* Validate the Python implementation using known synthetic channels.
* Implement an equivalent scalar C version.
* Cross-validate C results against the Python reference.
* Benchmark representative workloads.
* Profile execution using Linux perf.
* Investigate optimization opportunities without sacrificing correctness.
* Prepare the estimator for future OFDM receiver and MIMO integration.

## 2. Reference Specifications

The principal reference is:

**3GPP TS 38.211 — NR; Physical channels and modulation**

Relevant subject: PDSCH demodulation reference signals (DM-RS), including
their sequence generation and mapping to physical resources.

The applicable specification version and exact clause numbers must be
verified when the standards references are finalized.

**3GPP TS 38.214 — NR; Physical layer procedures for data**

This specification provides relevant PDSCH physical-layer procedure context.

The project will distinguish standardized DM-RS behavior from the estimator
and test-model choices defined in this document.

## 3. Kernel Scope

The initial estimator models one transmission layer and one receive antenna.

It accepts known pilot symbols, received pilot observations, their subcarrier
positions, and the subcarrier positions at which channel estimates are
requested.

The initial implementation includes:

* Least-squares (LS) estimation at pilot positions.
* Linear interpolation of complex channel estimates across frequency.
* Deterministic input validation.
* A NumPy reference implementation.
* A scalar C implementation.
* Correctness and cross-language tests.
* Benchmarking, profiling, and optimization.

The initial implementation does not generate standardized PDSCH DM-RS
sequences, perform complete NR resource mapping, estimate a full MIMO
channel matrix, or implement an entire receiver.

## 4. Mathematical Model

At pilot subcarrier k_p, the received observation is:

    Y[k_p] = H[k_p] * X_DMRS[k_p] + N[k_p]

where:

* Y[k_p] is the received complex pilot observation.
* H[k_p] is the channel frequency response.
* X_DMRS[k_p] is the known transmitted pilot symbol.
* N[k_p] is additive complex noise.

The least-squares estimate at a pilot position is:

    H_hat[k_p] = Y[k_p] / X_DMRS[k_p]

The pilot symbol must be non-zero.

This estimator does not remove the effect of noise. Noise in the received
pilot observations therefore affects the estimated channel response.

## 5. Frequency Interpolation

For requested subcarrier k between two pilot positions k_a and k_b, where
k_a < k < k_b, define:

    alpha = (k - k_a) / (k_b - k_a)

The interpolated estimate is:

    H_hat[k] = (1 - alpha) * H_hat[k_a] + alpha * H_hat[k_b]

Interpolation is performed on the complex estimates, equivalently applying
linear interpolation to their real and imaginary components.

Requested positions must lie within the range covered by the pilot positions.
Extrapolation beyond the first or last pilot is not supported initially.

At a pilot position, the returned estimate is the LS estimate for that pilot.

## 6. Input and Output Contract

### 6.1 Inputs

The estimator accepts:

* Known complex pilot symbols.
* Received complex pilot observations.
* Integer subcarrier indices corresponding to the pilots.
* Integer subcarrier indices where estimates are requested.

The pilot arrays must have equal, non-zero lengths. Pilot subcarrier
indices must be unique and supplied in strictly increasing order.
All pilot symbols and received observations must contain finite real and
imaginary components. Pilot symbols must be non-zero.

Requested subcarrier indices must lie between the first and last pilot
positions, inclusive.

### 6.2 Output

The estimator returns one complex channel estimate for each requested
subcarrier position, preserving the order of the requested positions.

The output length equals the number of requested positions. An empty list
of requested positions produces an empty output after the pilot inputs
have been validated.

The Python and C interfaces must implement equivalent validation rules.

## 7. DM-RS and Modeling Boundaries

PDSCH DM-RS is the intended reference-signal context for later integration.

The standardized DM-RS sequence, configuration, and resource mapping are
defined by the applicable 3GPP specifications. The initial estimator does
not implement all of those procedures.

For standalone tests, the caller supplies the known transmitted pilot
symbols and their subcarrier positions. Synthetic pilot values are test
inputs, not a claim of complete standards-compliant DM-RS generation.

The single-layer, single-receive-antenna model and the linear interpolation
method are project-level simplifications.

The initial estimator does not implement MMSE estimation, time-domain
interpolation, Doppler tracking, channel prediction, or MIMO channel-matrix
estimation.

## 8. Python Reference Implementation

The Python implementation will use NumPy complex-valued arrays and explicit
input validation.

It will be the behavioral reference for the scalar C implementation.

The reference must remain readable and prioritize mathematical clarity
over low-level optimization.

## 9. C Implementation

The C implementation will use a documented complex-number representation
and scalar operations initially.

The implementation must follow the same input validation, pilot ordering,
interpolation, output ordering, and numerical behavior as the Python
reference.

The C interface and memory layout will be documented before implementation.

## 10. Correctness and Validation

The test plan includes:

* Exact recovery of a constant, noise-free channel.
* Exact estimates at pilot positions within floating-point tolerance.
* Correct interpolation for a known linear complex channel response.
* Correct handling of requested positions supplied in a non-sorted order.
* A single pilot case, with estimates requested only at that pilot position.
* Multiple pilots and multiple requested positions.
* Empty requested-position input.
* Rejection of empty pilot input.
* Rejection of mismatched array lengths.
* Rejection of duplicate or unsorted pilot positions.
* Rejection of zero-valued pilot symbols.
* Rejection of non-finite input values.
* Rejection of requested positions outside the pilot range.
* Noisy-channel tests with appropriate statistical expectations.
* Python/C cross-validation using numerical tolerances.
* Regression tests after every optimization.

Floating-point results will be compared with documented absolute and
relative tolerances rather than requiring bit-for-bit equality.

## 11. Benchmarking and Profiling

Benchmarks will use reproducible pilot and requested-subcarrier workloads.

Measurements will include execution time and throughput where appropriate.
Linux perf will be used to investigate CPU utilization, instructions,
cycles, and cache behavior when supported by the environment.

Benchmark workloads will be large enough to measure reliably and will
include multiple input sizes. Correctness will be checked independently
of timing measurements.

## 12. Optimization Plan

The initial baseline is a clear scalar implementation.

Potential investigations include:

* Reducing repeated indexing and validation overhead.
* Improving memory layout and data access.
* Processing larger arrays efficiently.
* Compiler optimization levels.
* SIMD feasibility where the computation and data representation justify it.

Every optimization must be revalidated against the Python reference and
compared with the scalar baseline.

## 13. Future Integration

The planned receiver path is:

    OFDM FFT
        |
        v
    PDSCH DM-RS observations
        |
        v
    Kernel 5: Channel estimation
        |
        v
    Channel estimates
        |
        v
    Receiver equalization / Kernel 6 MIMO detection
        |
        v
    QAM demapping
        |
        v
    Descrambling and CRC verification

The integrated receiver will require consistent resource indexing, pilot
generation, channel dimensions, and signal conventions across kernels.
Those integration interfaces will be specified separately.

## 14. Completion Criteria

Kernel 5 will be considered complete only after:

* The specification and interfaces are documented.
* The Python reference passes its correctness tests.
* The scalar C implementation passes its tests.
* C/Python cross-validation succeeds.
* Benchmarks and profiling results are recorded.
* Optimization experiments are revalidated and documented.
* The final documentation is reviewed.
* Changes are committed and pushed to GitHub.
