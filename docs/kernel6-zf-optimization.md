# Kernel 6 — 2×2 MIMO Zero-Forcing Optimization and Performance Analysis

## 1. Objective

This document records the correctness validation, performance benchmarking,
profiling, and optimization of Kernel 6 in the 5G NR PHY Performance
Engineering project.

Kernel 6 estimates two transmitted complex symbols from two received complex
samples using a 2×2 channel matrix:

\[
y = Hx + n
\]

The Zero-Forcing (ZF) detector solves the linear system

\[
H\hat{x} = y
\]

rather than explicitly computing the inverse of the channel matrix.

The implementation uses C99 complex arithmetic and provides both single-pair
and batch detection interfaces.

## 2. Optimization

### Original implementation

The normalized channel matrix is used to assess whether the channel is
singular or near-singular. The Frobenius norm squared is calculated as

\[
\|G\|_F^2 = \sum_{i,j}|G_{ij}|^2
\]

The original calculation used four expressions of the form
`pow(cabs(gij), 2.0)`. This performed magnitude calculations followed by
general-purpose power-function calls.

### Optimized implementation

The squared magnitude of each complex element is calculated directly from
its real and imaginary components:

\[
|a+jb|^2 = a^2+b^2
\]

This removes the four `pow()` calls and avoids the associated repeated
function-call overhead. The normalized channel elements have magnitudes no
greater than one, so their component squares do not overflow.

The determinant calculation, singularity checks, detection algorithm, and
status-handling behavior remain unchanged.

This is a local arithmetic optimization; it does not change the mathematical
ZF algorithm or its computational complexity.

## 3. Correctness validation

The updated implementation passed the following checks:

* Kernel 6 C unit tests: 13 passed, 0 failed.
* Complete project Python test suite: 124 passed.
* C–Python cross-validation: all eight Kernel 6 cases passed.
* Tested cases include identity, diagonal and complex non-diagonal channels,
  small and large channel scaling, zero and near-singular channels, and
  non-finite inputs.
* Batch processing, invalid pointers, empty batches, and numerical failure
  handling were also tested.

These tests provide evidence that the optimization preserves the tested
behavior. They do not prove correctness for every possible floating-point
input.

## 4. Benchmark methodology

The benchmark uses:

* GCC with `-O2`
* `clock_gettime(CLOCK_MONOTONIC)`
* A fixed, well-conditioned complex 2×2 channel
* Batch sizes of 1, 16, 256, 4096, and 65536
* Approximately one million detected pairs per batch-size measurement
* Nanoseconds per pair and pairs per second as reported metrics

The baseline executable was built before the arithmetic optimization. The
optimized executable was rebuilt from the updated C source before the
post-optimization measurements.

Measurements depend on CPU frequency, system load, scheduling, and other
environmental factors. The results below are individual runs, not medians
from a statistically controlled repeated-sample experiment.

## 5. Initial performance comparison

The following table compares the saved baseline with the first
post-optimization run.

| Batch size | Baseline (ns/pair) | Optimized (ns/pair) | Measured reduction |
|-----------:|-------------------:|--------------------:|-------------------:|
| 1          | 78.98              | 68.02               | 13.9% |
| 16         | 61.47              | 54.25               | 11.8% |
| 256        | 61.48              | 54.15               | 11.9% |
| 4096       | 62.23              | 54.21               | 12.9% |
| 65536      | 61.81              | 54.20               | 12.3% |

The measured reduction is calculated as

\[
\text{Reduction} =
\frac{\text{Baseline}-\text{Optimized}}{\text{Baseline}}\times100\%
\]

A second optimized run measured 54.58 ns/pair at batch size 4096 and
54.46 ns/pair at batch size 65536. These repeat measurements are consistent
with the first optimized run for the larger batches.

The single-pair result varied more between runs. Therefore, the larger-batch
measurements provide the clearest preliminary evidence of an improvement.
More repeated samples and medians are needed before treating the measured
percentages as definitive.

## 6. Profiling observations

The baseline sampling profile showed `zf_detect_single` and the library
function `hypot` as prominent sampled locations. The profile motivated
investigating repeated magnitude and power calculations, but sampled
percentages alone do not establish the precise cost of an individual
expression.

The optimized `perf stat` run reported approximately:

* Task clock: 299.72 ms
* Elapsed time: 301.76 ms
* Performance-core PMU cycles: 1.412 billion
* Performance-core PMU instructions: 4.769 billion
* Performance-core PMU branches: 736.98 million
* Performance-core PMU branch misses: 71,793

The system has hybrid performance and efficiency cores. `perf` reports
separate `cpu_core` and `cpu_atom` counters, with multiplexing percentages.
These PMU values must not be casually combined or treated as a single
unified counter set. Profiling overhead and system scheduling also affect
timing, so the profiled run is not directly comparable to an unprofiled
benchmark run.

The benchmark timings are the primary evidence for the preliminary
performance comparison. The profiling results are retained as diagnostic
observations rather than proof of a specific counter-level speedup.

## 7. Artifacts

* Specification: `docs/kernel6-zf-specification.md`
* C implementation: `kernels/kernel6_mimo/mimo_zf_scalar.c`
* C interface: `kernels/kernel6_mimo/mimo_zf_scalar.h`
* Python reference: `kernels/kernel6_mimo/mimo_zf_reference.py`
* C tests: `tests/kernel6_mimo/test_mimo_zf.c`
* C–Python cross-validation harness: `tests/kernel6_mimo/zf_cross_validation.c`
* Python cross-validation tests: `tests/kernel6_mimo/test_mimo_zf_cross_validation.py`
* Benchmark source: `profiling/kernel6_mimo/benchmark_mimo_zf.c`
* Baseline benchmark: `results/kernel6_mimo/baseline_benchmark.txt`
* First optimized benchmark: `results/kernel6_mimo/post_optimization_benchmark.txt`
* Repeat optimized benchmark: `results/kernel6_mimo/post_optimization_benchmark_run2.txt`
* Baseline hardware counters: `results/kernel6_mimo/perf_stat_baseline.txt`
* Optimized hardware counters: `results/kernel6_mimo/perf_stat_optimized.txt`

## 8. Conclusion

The direct squared-magnitude calculation removes unnecessary power-function
calls from the normalized Frobenius norm calculation. The C tests and the
complete 124-test project suite passed after the source change.

Initial measurements indicate an approximately 12% reduction in execution
time per pair for larger batches on the current development system. The
result is promising but remains preliminary because the benchmark has not
yet used a statistically controlled repeated-sample methodology.

Kernel 6 has passed its current standalone correctness and performance
checks. Integration into a complete transmit/channel/receive chain remains
a separate project milestone.
