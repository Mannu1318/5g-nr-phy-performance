# Kernel 6 — 2x2 MIMO Zero-Forcing Detection Specification

## 1. Purpose

This kernel implements and evaluates Zero-Forcing (ZF) detection for a
2-transmit-stream, 2-receive-antenna complex baseband MIMO system.

The objective is to establish a correct mathematical reference, implement
a scalar C baseline, validate both implementations, measure performance,
and investigate optimizations using reproducible experiments.

This is a standalone computational study in the context of a 5G NR PHY
receiver. It is not a complete NR receiver implementation.

The engineering workflow is:

Understand -> Specify -> Implement -> Validate -> Benchmark ->
Profile -> Optimize -> Analyze -> Document.

## 2. Reference Specifications and Standards Context

The kernel is developed in the context of 5G NR physical-layer processing.

Relevant standards context includes:

* 3GPP TS 38.211: NR physical channels and modulation, including the
  complex-valued signal representation used in the PHY.
* 3GPP TS 38.214: NR physical-layer procedures for data.

Zero-Forcing is a receiver detection algorithm selected for this
computational study. The standards context does not imply that 3GPP
mandates this particular detection algorithm.

The kernel assumes that the receiver has already obtained the channel
matrix and received samples. Channel estimation and wireless-channel
simulation are outside the kernel's implementation scope.

## 3. Kernel Scope

### 3.1 Included

* A 2x2 complex-valued MIMO system.
* Two simultaneously transmitted complex symbols.
* Two complex received observations.
* A separate 2x2 channel matrix for each symbol pair.
* A Python reference implementation using NumPy.
* A scalar C implementation using double-precision arithmetic.
* Correctness tests, edge-case tests, and Python/C cross-validation.
* Single-pair validation followed by batch processing.
* Reproducible benchmarking and Linux perf profiling.
* Measurement-driven optimization experiments.
* Documentation and future PHY-chain integration planning.

### 3.2 Excluded

* Channel estimation and pilot processing.
* QAM mapping and demapping.
* OFDM FFT/IFFT.
* Bit scrambling and descrambling.
* CRC calculation and checking.
* Channel coding and decoding.
* A complete 5G NR transmitter, channel, or receiver.
* Mandatory SIMD or multithreaded implementation.

These components may be integrated with the kernel later through
separately defined interfaces.

## 4. Mathematical Model

The complex baseband MIMO model is:

    y = H x + n

where:

    H = [ h11  h12 ]
        [ h21  h22 ]

    x = [ x1 ]
        [ x2 ]

    y = [ y1 ]
        [ y2 ]

    n = [ n1 ]
        [ n2 ]

Here:

* H is the 2x2 complex channel matrix.
* x contains the two transmitted complex symbols.
* y contains the two received complex observations.
* n contains additive complex noise.

The scalar equations are:

    y1 = h11*x1 + h12*x2 + n1
    y2 = h21*x1 + h22*x2 + n2

The receiver is assumed to have an estimate of H. For this kernel,
the supplied H is treated as the channel matrix used by the detector.

### 4.1 Zero-Forcing Definition

For a nonsingular H, the ZF estimate is the solution of:

    H*x_hat = y

Equivalently:

    x_hat = inverse(H)*y

The implementation does not have to construct the inverse explicitly.
It may solve the linear system directly.

For the 2x2 matrix, define:

    det(H) = h11*h22 - h12*h21

When det(H) is nonzero, the algebraic solution is:

    x_hat1 = (h22*y1 - h12*y2) / det(H)

    x_hat2 = (h11*y2 - h21*y1) / det(H)

All operations use complex arithmetic.

Substituting the received-signal model gives:

    x_hat = x + inverse(H)*n

Thus, ZF removes channel mixing under the model but may amplify noise,
particularly when H is poorly conditioned. Noisy input does not guarantee
exact recovery of the transmitted symbols.

### 4.2 Numerical Policy

The initial implementations use complex double-precision values.

All input real and imaginary components must be finite.

A singular or numerically near-singular channel must not silently produce
an arbitrary estimate. The implementation must report a defined failure.

The initial numerical policy uses a scale-aware normalized determinant
metric, applied consistently in Python and C.

Let m be the largest magnitude among the four entries of H.

* If m == 0, H is the zero matrix and detection fails as singular.
* Otherwise, define G = H / m.
* Compute rho = abs(det(G)) / ||G||_F^2, where ||G||_F^2 is the sum
  of the squared magnitudes of all four entries of G.
* If rho <= 1e-12, report a numerically near-singular-channel failure.
* If rho > 1e-12, proceed with detection, subject to valid inputs and
  finite numerical results.

Scaling before evaluating the metric helps avoid unnecessary overflow
or underflow when channel coefficients have very different magnitudes.
The implementation must still check intermediate and final results for
non-finite values.

The threshold 1e-12 is an initial project policy, not a threshold
prescribed by 3GPP. It must be documented and tested. The metric is a
conditioning indicator, not an exact condition-number calculation.

Ill-conditioned channels and noise amplification will be investigated
separately from ordinary correctness tests. A valid but poorly
conditioned channel must not be described as mathematically singular
without evidence.

## 5. Processing Model

### 5.1 Single-Pair Operation

The fundamental operation accepts:

* One 2x2 complex channel matrix H.
* One length-2 complex received vector y.

It returns:

* One length-2 complex estimated-symbol vector x_hat.
* An explicit status indicating success or failure.

The single-pair operation is the starting point for mathematical
validation and edge-case testing.

### 5.2 Batch Operation

For N symbol pairs, the conceptual shapes are:

    H:     (N, 2, 2)
    y:     (N, 2)
    x_hat: (N, 2)

Each symbol pair has its own channel matrix. This permits channel
coefficients to vary across OFDM resource elements.

A batch call must define how failures are reported. The initial contract
will use an overall status and a per-pair status so that one invalid
channel does not silently corrupt other results.

Successful pairs must have valid estimates. Failed pairs must not be
presented as successful estimates.

For N = 0, the batch operation returns an empty output and success,
provided that the supplied array shapes and metadata are valid.

## 6. Input and Output Contract

### 6.1 Inputs

Single-pair inputs:

* H: finite complex 2x2 channel matrix.
* y: finite complex length-2 received vector.

Batch inputs:

* H: finite complex array of shape (N, 2, 2).
* y: finite complex array of shape (N, 2).

The Python interface validates array shapes and finite values before
processing.

The C interface uses explicitly documented array layouts and lengths.
The C API must not assume that arbitrary pointers are valid or that
the caller supplied the required number of elements.

### 6.2 Output

The estimated vector is:

    x_hat = [ x_hat1, x_hat2 ]

Python returns complex NumPy values. C stores complex values in a
documented representation and reports operation status explicitly.

The initial C representation will use pairs of double values
(real followed by imaginary) or an equivalently documented C complex
representation. The final choice must be consistent across the API,
tests, and benchmark harness.

For a batch, the output contains two estimates for each input pair,
with per-pair status reporting.

### 6.3 Error Handling

The implementation must define behavior for:

* Invalid dimensions or lengths.
* Non-finite channel coefficients.
* Non-finite received samples.
* Singular channels.
* Numerically near-singular channels.
* Empty batches.

The Python and C interfaces must follow equivalent mathematical and
validation rules, allowing for documented differences in how their
languages represent errors.

No failed operation may be reported as a successful detection.

## 7. Python Reference Implementation

The Python reference is the first implementation and the trusted
mathematical baseline.

It will:

* Use NumPy complex double-precision values.
* Validate shapes and finite input components.
* Solve the 2x2 system for each symbol pair.
* Apply the documented singularity and numerical-failure policy.
* Support single-pair and batch processing.
* Return estimates and explicit status information.

The reference implementation must prioritize clarity and correctness
over optimization.

## 8. C Scalar Implementation

The initial C implementation is a scalar baseline.

It will:

* Use GCC-compatible C and double-precision arithmetic.
* Implement the same ZF mathematical operation as the Python reference.
* Document the complex-number representation and memory layout.
* Validate pointers, dimensions, and lengths that can be checked by the API.
* Report singular and numerically near-singular inputs explicitly.
* Support single-pair operation and batch processing.
* Avoid dynamic allocation inside the per-pair numerical kernel unless
  a documented design decision requires it.

Compilation must enable warnings. Correctness testing will be performed
before benchmarking or optimization.

## 9. Correctness and Validation

The test plan includes:

* Recovery through an identity channel.
* Recovery through a well-conditioned, non-diagonal real channel.
* Recovery through a well-conditioned complex channel.
* Multiple transmitted symbol values.
* Batch processing with different channel matrices.
* Empty-batch behavior.
* Invalid input shapes and lengths.
* Rejection of non-finite channel coefficients.
* Rejection of non-finite received samples.
* Singular-channel detection.
* Numerically near-singular-channel handling.
* Noiseless recovery within floating-point tolerance.
* Noisy-input tests with appropriate expectations.
* Python/C cross-validation.
* Regression tests after every optimization.

Noisy tests must not require exact symbol recovery. They must instead
verify valid outputs and, where appropriate, compare error behavior
against an independently computed reference.

Floating-point comparisons use documented absolute and relative
tolerances rather than requiring bit-for-bit equality.

Tests must distinguish input validation, numerical failure, and ordinary
detection error.

## 10. Benchmarking and Profiling

The benchmark suite will measure the C implementation separately from
correctness tests.

Workloads will include:

* A single symbol pair to characterize fixed overhead.
* Small, medium, and large batches.
* Well-conditioned channel matrices.
* Representative complex-valued inputs.

Measurements will include elapsed time, time per symbol pair, and
throughput in symbol pairs per second.

Linux perf will be used where available to investigate cycles,
instructions, branches, and other relevant CPU behavior.

Benchmark inputs, compiler flags, iteration counts, and measurement
conditions must be documented. Correctness must be checked independently
of timing measurements.

Instrumented profiling results must be distinguished from official
benchmark measurements.

## 11. Optimization Plan

The scalar implementation is the baseline.

Potential investigations include:

* Compiler optimization levels such as -O0, -O2, and -O3.
* Alternative scalar formulations of the 2x2 solve.
* Avoiding unnecessary temporary values and repeated work.
* Batch memory layout and data access.
* SIMD feasibility using available CPU instruction sets.
* Processing multiple independent symbol pairs efficiently.

Every proposed optimization must be validated against the reference
and compared with the scalar baseline using reproducible measurements.

No optimization will be accepted solely because it appears faster
in theory. Measurements and correctness results determine the outcome.

## 12. Future PHY-Chain Integration

The intended conceptual receiver path is:

    OFDM FFT
        |
        v
    Received resource-element observations
        |
        v
    Kernel 5: Channel estimation
        |
        v
    Per-resource-element channel matrices
        |
        v
    Kernel 6: 2x2 MIMO ZF detection
        |
        v
    Estimated complex QAM symbols
        |
        v
    Kernel 3: QAM demapping
        |
        v
    Kernel 2: Descrambling
        |
        v
    Kernel 1: CRC validation

The transmitter path uses the corresponding CRC, scrambling, QAM
mapping, and OFDM processing stages.

The integrated system will require consistent definitions of resource
indices, stream ordering, complex-value representation, channel
dimensions, and error propagation.

A future integration harness will provide the channel model and
coordinate the transmitter and receiver kernels. Those system-level
functions are not part of the standalone ZF implementation.

## 13. Reproducibility and Documentation

The project will preserve:

* The Python reference.
* The scalar C implementation.
* Correctness and cross-validation tests.
* Benchmark source and documented commands.
* Profiling commands and relevant output summaries.
* Optimization experiments, including rejected candidates.
* Final performance comparisons and conclusions.

Measured results must not be fabricated or inferred from expected
performance. All reported speedups must be calculated from actual,
documented measurements.

## 14. Completion Criteria

Kernel 6 is complete when:

* The mathematical model and input/output contract are documented.
* The Python reference is implemented and tested.
* The scalar C implementation is implemented and tested.
* Python/C cross-validation passes for supported inputs.
* Invalid, singular, and numerically near-singular cases are handled
  according to the documented policy.
* Batch processing is validated.
* Reproducible benchmarks have been run.
* Linux perf profiling has been performed where supported.
* Optimization candidates have been evaluated using measurements.
* Final results and limitations are documented.
* Changes are committed and pushed to the project repository.
