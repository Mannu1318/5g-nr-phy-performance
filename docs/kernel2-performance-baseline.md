# Kernel 2 — Scrambling Performance Baseline

## Gold Sequence Generation

Benchmark configuration:

- Sequence length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- CPU: Intel Core i7-12700
- Representation: one bit per uint8_t
- Algorithm: 5G NR Gold sequence generation

## Compiler Baseline

| Optimization | Time (s) | Throughput |
|---|---:|---:|
| -O0 | 0.378428 | 264.25 Mbit/s |
| -O2 | 0.129885 | 769.91 Mbit/s |

## Profiling

At -O0:

- generate_gold_sequence(): 99.92% self CPU samples

At -O2:

- generate_gold_sequence(): 98.86% self CPU samples
- __memset(): 0.44%
- malloc-related functions: ~0.44%

Conclusion:

The Gold sequence generator remains the dominant computational workload after compiler optimization.

The -O2 result is the optimized scalar compiler baseline for further optimization work.
## Packed LFSR State Experiment

The first optimization experiment replaced the array-based LFSR state
with two 31-bit states stored in `uint32_t` variables.

The original implementation stores generated `x1` and `x2` bits in
byte-per-bit arrays. The packed-state implementation instead advances
the two LFSRs directly using shifts and XOR operations.

### Correctness

The packed implementation was cross-validated against the scalar
implementation.

Tests included:

- Gold sequence comparison
- Scrambling output comparison
- 10,000-bit long-sequence comparison
- `q = 1` Gold sequence comparison

Result:

**All packed LFSR cross-validation tests passed.**

### Performance

Benchmark configuration:

- Sequence length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- Output representation: one bit per `uint8_t`
- Compiler: GCC 13.3.0

| Implementation | Optimization | Throughput |
|---|---|---:|
| Scalar array | `-O0` | 264.25 Mbit/s |
| Scalar array | `-O2` | 769.91 Mbit/s |
| Packed LFSR state | `-O2` | 559.94 Mbit/s |
| Packed LFSR state | `-O3` | 584.70 Mbit/s |

The packed LFSR implementation was slower than the optimized scalar
implementation.

`-O3` improved the packed implementation compared with `-O2`, but it
remained below the scalar `-O2` baseline.

## Packed-Bit Output Experiment

The second optimization experiment changed the output representation so
that eight scrambling bits are stored in one byte instead of storing one
bit per `uint8_t`.

For example:

    c[0] ... c[7]
       ↓
    one output byte

The implementation uses an LSB-first representation, where scrambling
bit `c[n]` is stored at bit position `n % 8`.

### Correctness

The packed-bit implementation was cross-validated against the scalar
Gold-sequence implementation.

Test lengths included:

- 1 bit
- 7 bits
- 8 bits
- 9 bits
- 15 bits
- 16 bits
- 17 bits
- 31 bits
- 32 bits
- 33 bits
- 63 bits
- 64 bits

All tests passed.

### Memory Reduction

For a 1,000,000-bit sequence:

- Byte-per-bit representation: 1,000,000 bytes
- Packed-bit representation: 125,000 bytes

This represents an 8× reduction in output storage.

### Performance

Benchmark configuration:

- Sequence length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- Compiler: GCC 13.3.0
- Optimization: `-O2`

| Implementation | Throughput |
|---|---:|
| Scalar array | 769.91 Mbit/s |
| Packed-bit output | 523.08 Mbit/s |

The packed-bit implementation was approximately 32% slower than the
scalar `-O2` baseline.

### Performance Analysis

Although packed output substantially reduces memory usage, it introduces
additional work in the inner loop for bit positioning and byte
construction.

The underlying Gold-sequence generation remains a bit-by-bit LFSR
operation, so reducing output storage does not remove the main
computational dependency.

Therefore, memory reduction alone did not translate into higher
throughput.

### Engineering Conclusion

The packed-bit representation is functionally correct and reduces output
storage by 8×, but it does not improve throughput on the test CPU.

The scalar `-O2` implementation therefore remains the current performance
winner.

Future optimization should focus on reducing the cost of the
bit-by-bit Gold-sequence recurrence rather than only changing the output
representation.
### Performance Analysis

`perf stat` showed that the packed implementation had very low cache
activity and a low branch-miss rate. Therefore, cache misses and branch
misprediction were not the main performance problems.

The packed implementation performs multiple shift and XOR operations
for every generated bit. The LFSR state also creates a sequential
dependency between iterations.

This indicates that reducing memory storage alone does not guarantee
higher throughput.

### Engineering Conclusion

The packed LFSR state representation was functionally correct but did
not improve throughput on the test CPU.

Therefore, the scalar `-O2` implementation remains the current
performance baseline.

The packed-LFSR experiment is retained as a measured optimization
attempt rather than being adopted as the final implementation.

The next optimization experiment will investigate packed output bits,
processing multiple scrambling bits per output byte.

## Mathematical 8-Step LFSR Transformation

The previous optimization experiments showed that simply changing the
representation or grouping the loop did not remove the fundamental
per-bit dependency of the LFSR recurrence.

The LFSR state transition is linear over GF(2). Therefore, multiple
successive state transitions can be combined into a single mathematical
transformation.

For Kernel 2, an 8-step transformation was derived for both LFSRs:

- x1: `x1[n+31] = x1[n+3] XOR x1[n]`
- x2: `x2[n+31] = x2[n+3] XOR x2[n+2] XOR x2[n+1] XOR x2[n]`

Instead of advancing the state once for every output bit, the optimized
implementation generates eight output bits and then advances each LFSR
state by eight positions using the derived transformation.

### Validation

The 8-step transformation was independently validated against eight
ordinary one-bit LFSR transitions.

Validation was performed for multiple initial states for both x1 and x2.

The complete scrambling implementation was then cross-validated against
the scalar reference implementation for:

- 16-bit sequences
- 10,000-bit sequences
- q = 1
- Gold sequence generation
- scrambling output

All cross-validation tests passed.

### Performance

Benchmark configuration:

- Sequence length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- Compiler: GCC 13.3.0
- Optimization: `-O2`
- Representation: one bit per `uint8_t`

| Implementation | Throughput |
|---|---:|
| Scalar `-O0` | 264.25 Mbit/s |
| Scalar `-O2` | 769.91 Mbit/s |
| Packed LFSR `-O2` | 559.94 Mbit/s |
| Packed output `-O2` | 523.08 Mbit/s |
| Multi-bit loop `-O2` | 572.35 Mbit/s |
| Mathematical 8-step LFSR `-O2` | **1239.89 Mbit/s** |

The 8-step implementation achieved approximately **1.61× the throughput**
of the scalar `-O2` implementation.

The elapsed time for 100 million processed bits decreased from:

- Scalar `-O2`: 0.129885 s
- 8-step transformation: 0.080652 s

This corresponds to approximately a **37.9% reduction in elapsed time**.

### Performance Profiling

`perf stat` showed that the optimized implementation executes with
very high instruction throughput.

For the main `cpu_core` event:

- Cycles: approximately 375 million
- Instructions: approximately 2.30 billion
- IPC: approximately 6.12
- Branch misses: approximately 714
- Cache misses: approximately 2,403

Branch and cache misses were extremely small compared with the total
workload.

`perf record` / `perf report` showed that approximately **100% of sampled
CPU cycles** were attributed to `generate_gold_sequence_multistep()`.

This confirms that the main computational workload remains the Gold
sequence generator itself rather than memory allocation, library calls,
or cache behavior.

### Optimization Conclusion

The mathematical 8-step transformation is the first optimization of
Kernel 2 that provides a significant throughput improvement over the
optimized scalar implementation.

Unlike the packed-state and simple loop-grouping experiments, the
8-step method reduces the effective number of sequential LFSR state
transitions.

The implementation is therefore retained as the current optimized
baseline for further investigation.

The next optimization candidate is a larger multi-step transformation,
such as 16-step advancement. This will only be adopted if it provides
a measurable improvement without making the implementation unnecessarily
complex.

## 16-Step Mathematical LFSR Experiment

After validating the mathematical 8-step LFSR transformation, a
16-step transformation was investigated to determine whether a larger
state advance could provide additional performance.

### Mathematical Transformation

The 16-step transformation was derived using the linearity of the
31-bit LFSR over GF(2).

For x1, sixteen dependency masks were derived and validated against
sixteen ordinary scalar LFSR advances.

For x2, sixteen dependency masks were similarly derived and validated.

Both transformations matched the reference implementation across
multiple test states.

### Correctness Validation

The implementation was cross-validated against the trusted scalar
Gold sequence generator using:

- 16-bit sequence
- 10,000-bit sequence
- `q=1` configuration
- 100,000-bit sequence

All tests passed.

### Benchmark

Benchmark configuration:

- Sequence length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- Compiler: GCC 13.3.0
- Optimization: `-O2`
- Representation: one bit per `uint8_t`

| Implementation | Throughput |
|---|---:|
| Scalar `-O0` | 264.25 Mbit/s |
| Scalar `-O2` | 769.91 Mbit/s |
| Mathematical 8-step | **1239.89 Mbit/s** |
| Mathematical 16-step | 944.53 Mbit/s |

The 16-step implementation was approximately **23.8% slower** than
the 8-step implementation.

Although the 16-step transformation reduces the number of sequential
LFSR state updates further, each transformation requires substantially
more parity calculations and state-generation work.

Therefore, the reduction in loop iterations does not compensate for
the increased computational cost of each transformation.

### Performance Profiling

`perf stat` for the 16-step implementation showed approximately:

- Cycles: 473.7 million
- Instructions: 2.379 billion
- Branches: 112.7 million
- Branch misses: 3,090
- Cache references: 260,502
- Cache misses: 3,182
- IPC: approximately 5.02

Branch and cache misses were extremely small compared with the total
workload.

`perf report` attributed approximately **100% of sampled CPU cycles**
to `generate_gold_sequence_16step()`.

This confirms that the performance difference is primarily caused by
the computational structure of the 16-step transformation rather than
memory allocation, cache misses, or branch misprediction.

### Decision

The 16-step implementation is mathematically correct and fully
validated, but it does not outperform the 8-step implementation.

It is therefore **rejected as the final optimization**.

The mathematical 8-step implementation remains the optimized Kernel 2
Gold sequence baseline.

This experiment demonstrates an important performance-engineering
principle:

> A mathematically more aggressive optimization does not necessarily
> produce better hardware performance. The optimal transformation must
> be determined experimentally.

## Fused Gold Generation and Scrambling

After selecting the mathematical 8-step LFSR transformation, an
additional optimization was investigated.

The previous optimized implementation generated the Gold sequence into
a temporary buffer and then performed a separate XOR pass:

    Gold generation → temporary buffer → XOR with input

This introduced an additional memory pass and required a temporary
sequence buffer.

The fused implementation removes this intermediate buffer.

Instead, eight Gold-sequence bits are generated and immediately XORed
with the corresponding input bits:

    Gold generation → immediate XOR → output

The LFSR state transformation remains the validated mathematical
8-step transformation.

### Correctness Validation

The fused implementation was cross-validated against the trusted
scalar implementation using:

- 16-bit sequence
- 10,000-bit sequence
- 10,000-bit sequence with q=1
- 100,000-bit sequence
- 1,000,000-bit sequence

All tests passed.

### Benchmark

Benchmark configuration:

- Input length: 1,000,000 bits
- Iterations: 100
- Total processed: 100,000,000 bits
- Compiler: GCC 13.3.0
- Optimization: `-O2`
- Representation: one bit per `uint8_t`

| Implementation | Throughput |
|---|---:|
| Scalar `-O2` | 696.61 Mbit/s |
| 8-step + temporary Gold buffer | 833.04 Mbit/s |
| 8-step + fused XOR | **900.17 Mbit/s** |

The fused implementation improves throughput by approximately:

- 29.2% compared with the scalar `-O2` implementation
- 8.1% compared with the previous 8-step optimized implementation

### Performance Profiling

`perf stat` showed approximately:

- Core cycles: 467.6 million
- Core instructions: 2.567 billion
- Core branches: 133.7 million
- Branch misses: 761
- Cache references: 3.05 million
- Cache misses: 3,709
- IPC: approximately 5.49

Branch and cache misses remained extremely small.

Compared with the previous 8-step implementation, the fused version
reduced the measured core instruction count from approximately
3.496 billion to 2.567 billion.

Core cycles decreased from approximately 585.9 million to 467.6
million.

This confirms that eliminating the temporary Gold-sequence buffer and
the separate XOR pass reduces the overall computational work.

### `perf report`

Sampling with:

    perf record -g ./tests/benchmark_scrambling_fused

showed approximately 100% of sampled core cycles inside:

    scramble_bits_fused()

The small `[unknown]` entry was a profiling artifact and was not
considered a significant contributor.

### Final Decision

The fused implementation is selected as the final optimized
end-to-end Kernel 2 scrambling implementation.

The final implementation combines:

1. 31-bit packed LFSR state
2. 1600-bit Gold sequence warm-up
3. Mathematical 8-step LFSR advancement
4. Direct Gold-sequence generation
5. Immediate XOR with the input
6. No temporary Gold-sequence buffer

The final measured throughput is:

    900.17 Mbit/s

This represents approximately 1.29× the throughput of the scalar
`-O2` implementation.

The 16-step mathematical transformation was investigated separately
but rejected because it was slower than the 8-step transformation.

The fused 8-step implementation is therefore the final Kernel 2
performance baseline.
