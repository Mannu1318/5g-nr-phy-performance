# Kernel 4 — OFDM FFT/IFFT Optimization and Performance Analysis

## 1. Objective

This document records the implementation, correctness validation, performance benchmarking, and profiling of Kernel 4 in the 5G NR PHY Performance Engineering project.

Kernel 4 covers:

* Forward FFT and inverse FFT (IFFT)
* Subcarrier mapping and extraction
* Cyclic prefix insertion and removal

The C FFT implementation uses an iterative radix-2 Cooley–Tukey algorithm with bit-reversal reordering and butterfly operations.

## 2. Optimization

### Original implementation

The original FFT calculated the twiddle factor inside the butterfly-group loop:

* Calculate the angle for each butterfly position.
* Evaluate `cos()` and `sin()` for each group.
* Perform the complex multiplication and butterfly operations.

The twiddle factor depends on the FFT stage and butterfly position, not on the group index. Consequently, the same trigonometric calculations were repeated across multiple groups.

### Optimized implementation

The loop order was changed so that the butterfly-position loop surrounds the group loop.

For each FFT stage:

1. Calculate the twiddle factor once for a butterfly position.
2. Reuse that factor across all groups in the stage.
3. Perform the complex multiplication and butterfly operations.

This reduces redundant trigonometric evaluations while preserving the radix-2 FFT algorithm and its \(O(N\log_2 N)\) computational complexity.

## 3. Correctness validation

The optimized implementation passed the following checks:

* C unit tests: 16 passed, 0 failed.
* Python reference tests: 38 passed.
* C-versus-NumPy cross-validation: all six FFT sizes passed.
* Supported transform sizes: 64, 128, 256, 512, 1024, and 2048.
* Cross-validation tolerance: \(10^{-9}\).
* Maximum observed FFT error: approximately \(1.421\times10^{-13}\).
* Maximum observed IFFT error: approximately \(2.220\times10^{-16}\).

These results confirm numerical agreement with the reference implementation within the selected tolerance.

## 4. Benchmark methodology

The C benchmark uses:

* GCC with `-O2`
* 100 warm-up iterations per transform
* 2,000 iterations per sample
* Seven independent samples per transform
* Median and minimum execution-time reporting
* `clock_gettime(CLOCK_MONOTONIC)` for timing

Measurements are machine- and system-load-dependent. The baseline and optimized versions were measured on the same development system, but repeated runs showed variability, particularly for the 64-point FFT.

## 5. Initial performance comparison

The following table compares the original repeated-sample baseline with the first optimized benchmark run.

| FFT size | Transform | Baseline median (ns) | Optimized median (ns) | Median reduction |
| -------: | --------- | -------------------: | --------------------: | ---------------: |
|       64 | FFT       |              1326.12 |                723.98 |            45.4% |
|       64 | IFFT      |              1372.43 |                788.08 |            42.6% |
|      128 | FFT       |              3055.28 |               1560.75 |            48.9% |
|      128 | IFFT      |              3124.68 |               1649.00 |            47.2% |
|      256 | FFT       |              6984.31 |               3279.19 |            53.1% |
|      256 | IFFT      |              7600.44 |               3580.64 |            52.9% |
|      512 | FFT       |             16506.36 |               6781.06 |            58.9% |
|      512 | IFFT      |             17028.93 |               7398.30 |            56.6% |
|     1024 | FFT       |             36878.24 |              14368.81 |            61.0% |
|     1024 | IFFT      |             37002.92 |              15505.48 |            58.1% |
|     2048 | FFT       |             78899.67 |              30230.85 |            61.7% |
|     2048 | IFFT      |             81575.39 |              33329.58 |            59.1% |

The median reduction is calculated as:

$$
\text{Reduction} =
\frac{\text{Baseline median}-\text{Optimized median}}
{\text{Baseline median}}\times100\%
$$

These percentages describe the first optimized run, not a guarantee of identical performance on every run. Later runs showed additional timing variation, especially for the 64-point FFT. Repeated measurements should be considered when reporting final performance claims.

## 6. Profiling observations

The original profiling report identified `ofdm_fft` as the dominant hotspot. Trigonometric functions, including `__sincos_fma`, were visible in the call tree.

An optimized profile was also recorded. However, the default report selected a sparse `cpu_atom/cycles/Pu` event subset, and attempts to select the performance-core event with `perf report` were unsupported by the installed version's command-line interface.

Therefore, the available reports do not establish a reliable quantitative reduction in trigonometric-function sample percentages. The benchmark measurements are the primary evidence of improved execution time.

Raw profiling captures are retained locally but excluded from Git.

## 7. Artifacts

* Specification: `docs/kernel4-ofdm-specification.md`
* C implementation: `kernels/kernel4_ofdm/src/ofdm.c`
* C interface: `kernels/kernel4_ofdm/include/ofdm.h`
* Python reference: `kernels/kernel4_ofdm/ofdm_reference.py`
* C tests: `tests/kernel4_ofdm/test_ofdm.c`
* Python tests: `tests/kernel4_ofdm/test_ofdm_reference.py`
* Cross-validation: `tests/kernel4_ofdm/validate_c_against_python.py`
* Benchmark source: `profiling/kernel4_ofdm/benchmark_ofdm.c`
* Baseline measurements: `results/kernel4_ofdm/repeated_samples.csv`
* First optimized run: `results/kernel4_ofdm/optimized_benchmark.txt`
* Repeat optimized run: `results/kernel4_ofdm/optimized_benchmark_repeat.txt`

## 8. Conclusion

The twiddle-factor reuse optimization reduced repeated trigonometric calculations and substantially lowered measured execution times across the supported FFT sizes.

The optimized implementation passed all recorded correctness checks. The benchmark results support the performance improvement, while the profiling results remain qualitative because the available event-specific report was sparse.

Kernel 4 should be considered ready for further integration testing once the complete repository regression suite, final artifact review, and Git commit have been completed.
