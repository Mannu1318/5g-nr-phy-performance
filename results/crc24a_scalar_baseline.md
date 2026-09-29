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
