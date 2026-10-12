# Kernel 2 — 5G NR Bit Scrambling Results

## 1. Overview

This report records the measured performance of the Kernel 2
5G NR bit-scrambling implementation.

The benchmark compares the scalar implementation with an optimized
implementation that combines mathematical 8-step Gold-sequence
generation and XOR scrambling.

Detailed experiment notes are maintained in:

`docs/kernel2-performance-baseline.md`

## 2. Benchmark Configuration

| Parameter | Value |
|---|---|
| Input length | 1,000,000 bits |
| Iterations | 100 |
| Total bits processed | 100,000,000 |
| Compiler | GCC 13.3.0 |
| Compiler optimization | `-O2` |
| Bit representation | One bit per `uint8_t` |
| Processor | Intel Core i7-12700 |

These values are taken from the existing benchmark documentation.

## 3. Throughput Results

| Implementation | Throughput |
|---|---:|
| Scalar implementation (`-O2`) | 696.61 Mbit/s |
| 8-step generation with temporary Gold buffer | 833.04 Mbit/s |
| 8-step generation with fused XOR | 900.17 Mbit/s |

These are previously recorded measurements, not a new benchmark run.

## 4. Performance Improvement

Using the scalar implementation as the baseline:

- Absolute throughput improvement: 203.56 Mbit/s
- Relative throughput improvement: approximately 29.2%
- Throughput ratio: approximately 1.29x

Compared with the 8-step implementation that uses a temporary Gold
buffer, the fused implementation improves throughput by approximately
8.1%.

## 5. Correctness Validation

The fused implementation was cross-validated against the scalar
implementation for the following input lengths and conditions:

- 16-bit sequence
- 10,000-bit sequence
- 10,000-bit sequence with `q = 1`
- 100,000-bit sequence
- 1,000,000-bit sequence

All tests passed according to the existing performance report.

## 6. Profiling Observations

The existing `perf stat` measurements for the fused implementation
reported approximately:

| Metric | Recorded value |
|---|---:|
| Core cycles | 467.6 million |
| Core instructions | 2.567 billion |
| Core branches | 133.7 million |
| Branch misses | 761 |
| Cache references | 3.05 million |
| Cache misses | 3,709 |
| Instructions per cycle (IPC) | 5.49 |

The recorded core instruction count decreased from approximately
3.496 billion for the previous 8-step implementation to 2.567 billion
for the fused implementation.

Recorded core cycles decreased from approximately 585.9 million to
467.6 million.

The existing `perf report` analysis attributed approximately 100% of
sampled core cycles to `scramble_bits_fused()`.

## 7. Selected Implementation

The fused implementation was selected as the final optimized
end-to-end Kernel 2 scrambling implementation.

Its documented design combines:

1. Packed 31-bit LFSR state
2. 1600-bit Gold-sequence warm-up
3. Mathematical 8-step LFSR advancement
4. Direct Gold-sequence generation
5. Immediate XOR with the input
6. No temporary Gold-sequence buffer

## 8. Limitations

- The throughput figures are measurements from the existing
  benchmark documentation; this report does not represent a new run.
- Results describe the specified benchmark workload and machine.
- Performance may vary with compiler options, processor, input size,
  and system load.
- These measurements do not establish end-to-end 5G NR PHY performance.

## 9. Detailed Reference

See `docs/kernel2-performance-baseline.md` for the detailed optimization
experiments, comparisons, and profiling discussion.
