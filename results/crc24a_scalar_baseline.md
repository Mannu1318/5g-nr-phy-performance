# CRC24A Scalar Baseline Performance

## 1. Purpose

This experiment establishes the initial performance baseline for the
standalone CRC24A scalar implementation used in the 5G NR PHY
performance study.

The same CRC24A algorithm and benchmark workload were compiled with
different GCC optimization levels. No manual SIMD or multithreading
optimization was introduced.

The purpose is to measure the effect of compiler optimization before
manual performance optimization.

---

## 2. Environment

CPU:

    Intel Core i7-12700

CPU configuration:

    12 physical cores
    20 logical processors
    1 socket
    8 P-cores
    4 E-cores

Instruction-set capability relevant to this project:

    AVX2: supported
    AVX-512: not supported

Compiler:

    GCC 13.3.0

Operating system:

    Ubuntu 24.04.4 LTS

---

## 3. Implementation

Kernel:

    CRC24A

Implementation:

    kernels/crc24a_scalar.c

The implementation processes one logical input bit at a time using
scalar integer operations.

The CRC24A polynomial used by the implementation is:

    0x864CFB

CRC width:

    24 bits

The scalar implementation was first validated against the Python
reference implementation.

Validation input:

    "123456789"

Expected CRC:

    0xCDE703

The C implementation produced:

    0xCDE703

Therefore, the C scalar implementation matched the Python reference
for the validation case.

---

## 4. Benchmark Configuration

Input size:

    1,048,576 logical bits

Equivalent logical input size:

    1 Mi bit

Iterations:

    100

Input representation:

    One uint8_t per logical bit

Input pattern:

    0 1 0 1 0 1 ...

Timing method:

    clock_gettime(CLOCK_MONOTONIC)

Performance metric:

    Throughput in Gbit/s

Throughput calculation:

    total_bits / total_time / 1e9

---

## 5. Results

| GCC optimization | Total time (s) | Throughput (Gbit/s) | Relative to -O0 |
|-------------------|----------------:|--------------------:|----------------:|
| -O0               | 0.504999        | 0.208               | 1.00x           |
| -O2               | 0.106847        | 0.981               | 4.72x           |
| -O3               | 0.099095        | 1.058               | 5.09x           |

---

## 6. Observations

The transition from -O0 to -O2 produced a substantial performance
improvement.

Approximate improvement:

    0.981 / 0.208 = 4.72x

The transition from -O2 to -O3 produced a smaller additional
improvement.

Approximate improvement:

    1.058 / 0.981 = 1.08x

Therefore, most of the compiler-only performance improvement was
obtained by moving from -O0 to -O2.

The -O3 result provides a useful optimized-scalar reference point
before introducing manual SIMD optimization.

---

## 7. Interpretation

These measurements demonstrate that compiler optimization alone can
significantly improve the performance of the scalar CRC24A kernel.

However, the implementation is still fundamentally scalar and
processes one logical bit per loop iteration.

The next optimization stages will investigate:

    1. SIMD/AVX2
    2. Multithreading
    3. Memory representation and cache behavior

The optimized scalar result should be treated as the baseline for
manual AVX2 optimization rather than comparing AVX2 directly against
the unoptimized -O0 result.

---

## 8. Reproducibility

Benchmark source:

    tests/benchmark_crc24a_scalar.c

CRC implementation:

    kernels/crc24a_scalar.c

The benchmark was compiled using:

    gcc -Wall -Wextra -O0 ...
    gcc -Wall -Wextra -O2 ...
    gcc -Wall -Wextra -O3 ...

The benchmark executable is generated locally and is excluded from
Git tracking.

The benchmark source and experimental documentation are tracked in
the repository.

---

## 9. Repeated Measurement

To evaluate run-to-run timing variation, the optimized scalar benchmark
was executed using 10 independent timed samples.

Configuration:

    GCC optimization: -O3
    Samples: 10
    Iterations per sample: 100
    Input size: 1,048,576 bits

Measured results:

| Metric | Result |
|--------|-------:|
| Minimum time | 0.087804 s |
| Average time | 0.090954 s |
| Maximum time | 0.102485 s |
| Throughput at maximum time | 1.023 Gbit/s |
| Average throughput | 1.153 Gbit/s |
| Throughput at minimum time | 1.194 Gbit/s |

The repeated measurements demonstrate observable run-to-run variation.
Therefore, a single benchmark execution should not be treated as the
sole representative performance measurement.

For subsequent optimization comparisons, the benchmark will use the
same workload and repeated-sample methodology.

The average throughput of 1.153 Gbit/s is used as the current
representative scalar -O3 measurement, while the minimum and maximum
observations provide context for measurement variability.

---

## 10. Phase 3 Profiling

The CRC24A scalar `-O3` benchmark was profiled using Linux `perf`.

### 10.1 System-level profiling

The following counters were available:

    task-clock
    context-switches
    cpu-migrations
    page-faults

Measured results:

| Counter | Result |
|---------|-------:|
| Task-clock | 899.36 ms |
| Context switches | 0 |
| CPU migrations | 0 |
| Page faults | 318 |
| Wall-clock time | 900.55 ms |
| User CPU time | 897.35 ms |
| System CPU time | 3.00 ms |

The task-clock and wall-clock times were very close, indicating that
the benchmark spent almost all of its execution time actively using
the CPU rather than waiting.

No context switches or CPU migrations occurred during this particular
measurement.

The observed page faults are associated with normal process and memory
initialization and are not considered evidence of a CRC computation
bottleneck.

### 10.2 Instruction, branch, and cache profiling

The following hardware events were measured:

    instructions
    branches
    branch-misses
    cache-references
    cache-misses

Because the Intel Core i7-12700 uses a hybrid P-core/E-core architecture,
Linux `perf` reports these events separately as `cpu_core` and `cpu_atom`.

Combined measurements were approximately:

| Metric | Combined result |
|--------|----------------:|
| Instructions | 16.70 billion |
| Branches | 1.274 billion |
| Branch misses | 185 thousand |
| Cache references | 5.13 million |
| Cache misses | 122 thousand |

The benchmark processed approximately 1.049 billion logical input bits
during the profiling run. The instruction count therefore corresponds
to approximately 15.9 instructions per logical input bit.

The measured branch-miss count was very small relative to the total
number of branches. Therefore, branch misprediction does not appear
to be a major performance bottleneck in this implementation.

Cache misses were also relatively limited in the measured counters.
Further cache analysis will be performed later as part of the project's
memory and cache optimization phase.

### 10.3 Compiler-generated assembly

The `-O3` executable was inspected using:

    objdump -d -M intel ./tests/benchmark_crc24a_scalar_O3

The generated CRC loop uses a conditional move (`cmovne`) rather than
a conditional branch for the polynomial XOR operation.

This corresponds to the source-level operation:

    if (top_bit ^ bit)
    {
        crc ^= CRC24A_POLY;
    }

The compiler therefore already removes the unpredictable branch from
the hot loop.

The generated loop processes one logical input bit per iteration and
maintains a loop-carried CRC state. Each iteration depends on the CRC
state produced by the previous iteration.

This dependency is important for future SIMD optimization because the
CRC state cannot simply be divided into independent operations on
individual bits without additional polynomial-based techniques.

### 10.4 Input representation observation

The scalar baseline represents each logical input bit using one
`uint8_t` element containing either `0` or `1`.

Therefore, an input of:

    1,048,576 logical bits

currently occupies:

    1,048,576 bytes

This is an intentionally simple representation for the baseline.
A packed-bit representation would reduce the input storage requirement
by approximately 8×.

The effect of data representation, memory bandwidth, and cache behavior
will be investigated later in the memory/cache optimization phase.

### 10.5 Profiling conclusions

The profiling results establish the following baseline observations:

1. The CRC kernel is primarily CPU-computation dominated.
2. Scheduling interference was negligible during the measured run.
3. Branch misprediction is not a significant bottleneck in the current
   scalar implementation.
4. GCC `-O3` already converts the conditional CRC update into a
   conditional move.
5. The CRC state creates a loop-carried dependency between iterations.
6. The current one-byte-per-bit representation is simple but
   memory-inefficient compared with packed bits.
7. Straightforward bit-by-bit AVX2 vectorization is therefore not
   expected to be sufficient; any SIMD optimization must account for
   the CRC state dependency.

These observations will guide the optimization work in the subsequent
phases.
