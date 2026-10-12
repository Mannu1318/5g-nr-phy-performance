# Kernel 4 — OFDM FFT/IFFT

## 1. Objective

The objective of Kernel 4 is to implement and evaluate the Fast Fourier Transform (FFT) and Inverse Fast Fourier Transform (IFFT) operations used in a simplified 5G NR physical-layer signal-processing workflow.

We will develop a Python reference implementation first, followed by a C implementation. We will validate correctness, measure execution time, profile performance, investigate optimizations, and document the results.

This kernel will also cover subcarrier mapping, cyclic prefix insertion, and cyclic prefix removal.

## 2. Scope

This kernel is a standalone numerical signal-processing study. It does not implement the complete 5G NR OFDM transmitter or receiver.

The initial work will cover:

* FFT: convert time-domain samples into frequency-domain values.
* IFFT: convert frequency-domain values into time-domain samples.
* Subcarrier mapping and extraction.
* Cyclic prefix (CP) insertion and removal.
* Python and C correctness validation.
* Benchmarking, profiling, and performance optimization.
## 3. Mathematical Definitions

### 3.1 Forward FFT

For a sequence of N time-domain samples x[n], the forward FFT is defined as:

X[k] = sum from n = 0 to N-1 of x[n] * exp(-j * 2*pi*k*n/N)

where:

* N is the FFT size.
* n is the time-domain sample index.
* k is the frequency-domain bin index.
* j is the imaginary unit.

The forward FFT uses a negative exponential sign and does not apply normalization.

### 3.2 Inverse FFT (IFFT)

The IFFT is defined as:

x[n] = (1/N) * sum from k = 0 to N-1 of X[k] * exp(+j * 2*pi*k*n/N)

The IFFT uses a positive exponential sign and applies normalization by 1/N.

### 3.3 Round-Trip Property

For valid input data, applying the IFFT to the output of the FFT should approximately reproduce the original input:

IFFT(FFT(x)) ≈ x

Small floating-point differences are expected because numerical calculations have finite precision.
## 4. Supported FFT Sizes

The initial implementation will support the following FFT sizes:

* 64
* 128
* 256
* 512
* 1024
* 2048

These sizes provide a range of workloads for correctness testing and performance benchmarking. They are experimental kernel sizes and do not imply that every size is used for every 5G NR configuration.

## 5. Frequency-Bin Ordering

The FFT output will use natural FFT-bin order.

For an FFT of size N:

* Bin 0 represents the DC component.
* Bins 1 through N/2 - 1 represent positive-frequency bins.
* Bin N/2 is the Nyquist bin for even N.
* Bins above N/2 represent negative-frequency bins in wrapped FFT order.

The implementation will not automatically rearrange bins using an FFT shift operation.

## 6. Subcarrier Mapping and Extraction

Subcarrier mapping places input frequency-domain symbols into explicitly specified FFT-bin indices.

The mapping operation will:

* Accept frequency-domain symbols and their target bin indices.
* Initialize unassigned FFT bins to zero.
* Reject invalid bin indices.
* Reject duplicate bin indices.
* Preserve the specified symbol-to-bin correspondence.

Subcarrier extraction will retrieve symbols from explicitly specified FFT-bin indices.

Subcarrier mapping and extraction will remain separate from the FFT and IFFT operations. This separation will make the kernel easier to test and integrate into a future OFDM transmitter and receiver chain.
## 7. Cyclic Prefix (CP) Operations

### 7.1 CP Insertion

Cyclic prefix insertion copies the last L samples of an OFDM time-domain symbol and prepends them to the beginning of the symbol.

For an input symbol containing N samples and a CP length L, the output contains N + L samples.

The output is:

[ x[N-L], ..., x[N-1], x[0], ..., x[N-1] ]

where the first L samples are the cyclic prefix.

### 7.2 CP Removal

CP removal discards the first L samples of the received OFDM symbol and retains the following N samples.

For an input containing N + L samples, the output contains N samples.

### 7.3 Validation Rules

The CP operations will:

* Accept an explicit CP length L.
* Require 0 <= L <= N for CP insertion.
* Reject invalid CP lengths.
* Check that the input length is sufficient for the requested operation.
* Preserve sample order and values.

For CP removal, the input must contain at least L samples plus the requested N useful samples.

### 7.4 Scope Limitation

This kernel implements the CP operations themselves. It will not initially implement the complete numerology-dependent cyclic-prefix scheduling rules specified for every 5G NR OFDM configuration.

## 8. Implementation Strategy

Development will follow this order:

1. Define the Python reference interfaces.
2. Implement and test the Python FFT and IFFT.
3. Implement and test subcarrier mapping and extraction.
4. Implement and test CP insertion and removal.
5. Develop the corresponding C implementation.
6. Cross-validate C results against the Python reference.
7. Benchmark the baseline implementations.
8. Profile performance using Linux perf.
9. Investigate suitable optimizations.
10. Document correctness and performance results.
## 9. Testing and Correctness Validation

The Python reference implementation will be tested before the C implementation is developed.

### 9.1 FFT and IFFT Tests

Tests will include:

* Impulse input.
* Constant input.
* Single-frequency complex input.
* Deterministic random complex input.
* FFT followed by IFFT.
* IFFT followed by FFT.
* All supported FFT sizes.

Floating-point results will be compared using suitable absolute and relative tolerances rather than exact equality.

### 9.2 Subcarrier Mapping Tests

Tests will verify:

* Correct symbol placement.
* Zero values in unassigned bins.
* Correct extraction of mapped symbols.
* Rejection of invalid bin indices.
* Rejection of duplicate bin indices.
* Empty mapping behavior, if supported by the final interface.

### 9.3 Cyclic Prefix Tests

Tests will verify:

* Correct CP sample order.
* Correct output length after insertion.
* Correct output length after removal.
* Recovery of the original useful samples after insertion followed by removal.
* CP length zero.
* CP length equal to the useful-symbol length.
* Rejection of invalid lengths and insufficient input.

### 9.4 Python and C Cross-Validation

The C implementation will be tested against the Python reference using identical inputs and compatible numerical tolerances.

Both implementations must follow the same FFT sign convention, IFFT normalization, bin ordering, and input-validation rules.

## 10. Benchmarking and Profiling

Correctness validation must pass before performance results are collected.

Benchmarking will measure execution time for the supported FFT sizes and relevant operations.

The study will document:

* Input size and data type.
* Compiler and compiler flags for C.
* Python and relevant library versions.
* Number of benchmark repetitions.
* Timing methodology.
* Baseline execution time.
* Optimized execution time and measured speedup, when applicable.

Linux perf will be used where appropriate to investigate CPU utilization, instruction behavior, cache effects, and other available performance counters.

Optimization will be evidence-driven. Any optimized implementation must pass the same correctness tests as the baseline.

## 11. Reproducibility

Benchmark scripts, test cases, profiling instructions, and results will be kept in the repository.

Performance comparisons must use documented conditions. Results from different environments or compiler settings must not be treated as directly comparable without explanation.
## 12. Future PHY-Chain Integration

Kernel 4 is designed to connect with the other kernels in the broader 5G NR PHY Performance Engineering project.

### 12.1 Transmitter-Side Flow

The planned simplified transmitter flow is:

Input bits -> Kernel 3 QAM Mapping -> Kernel 4 Subcarrier Mapping -> Kernel 4 IFFT -> Kernel 4 CP Insertion

The output is a time-domain OFDM symbol with its cyclic prefix.

### 12.2 Receiver-Side Flow

The corresponding simplified receiver flow is:

Received OFDM Symbol -> Kernel 4 CP Removal -> Kernel 4 FFT -> Kernel 4 Subcarrier Extraction -> Kernel 3 QAM Demapping

A channel model and other receiver operations will be added as part of the broader integration work.

### 12.3 Integration Boundaries

Kernel 4 will not implement the complete transmitter chain, channel model, channel estimation, or MIMO detection internally.

The FFT/IFFT, mapping, extraction, and CP operations will have clear interfaces so they can be connected to other kernels later.

## 13. Completion Criteria

Kernel 4 will be considered complete when:

1. The Python reference implementation is documented and tested.
2. The C implementation is documented and tested.
3. Supported FFT sizes pass correctness tests.
4. Mapping, extraction, and CP operations pass their validation tests.
5. C and Python results agree within defined numerical tolerances.
6. Baseline benchmarks are recorded.
7. Profiling and optimization investigations are documented.
8. Final results and integration interfaces are documented.

## 14. Development Workflow

The kernel will follow this workflow:

Understand -> Specify -> Implement Python Reference -> Implement C -> Validate -> Benchmark -> Profile -> Optimize -> Analyze -> Document

The specification defines the intended behavior. Implementation details may be refined when necessary, but changes must be documented and validated.

## 15. References

3GPP TS 38.211 — NR; Physical channels and modulation.

Clause 5.3.1 — OFDM baseband signal generation for physical channels other than PRACH and RIM-RS.

The 3GPP specification is the standards reference. This project implements a standalone numerical kernel and does not claim to reproduce every detail of a complete standards-compliant 5G NR waveform.

## 16. FFT Algorithm Selection

### 16.1 Python Reference

The Python reference will use NumPy FFT functions:

* `numpy.fft.fft()` for the forward FFT.
* `numpy.fft.ifft()` for the inverse FFT.

These functions establish the numerical reference for validating the C implementation.

### 16.2 C Implementation

The initial C implementation will use the iterative radix-2 Cooley-Tukey FFT algorithm.

The algorithm will include bit-reversal permutation and iterative butterfly stages. The supported FFT sizes are powers of two.

The forward transform will use a negative exponential and no normalization. The inverse transform will use a positive exponential and normalization by 1/N.

### 16.3 Performance Comparison

The Python reference and C implementation will be benchmarked separately. NumPy may use optimized native routines, so comparisons will identify the implementation and environment rather than assuming that C must always be faster.

The C implementation will first establish a correct baseline. Any later optimization must preserve numerical correctness and be supported by measurements.
