# Kernel 3: QAM Mapping and Demapping — Benchmark Summary

## 1. Objective

Measure the throughput of the Kernel 3 QAM mapping and demapping implementation for:

- QPSK
- 16-QAM
- 64-QAM
- 256-QAM

This benchmark measures mapping followed by demapping. The reported throughput
must not be interpreted as mapping-only or demapping-only performance.

## 2. Benchmark Configuration

| Parameter | Value |
|---|---|
| Symbols per iteration | 1,000,000 |
| Timed iterations | 100 |
| Total symbols processed per modulation | 100,000,000 |
| Compiler | GCC |
| Optimization level | `-O2` |
| C standard | C11 |
| Warning flags | `-Wall -Wextra -Wpedantic` |
| Timer | `clock_gettime(CLOCK_MONOTONIC)` |
| Measurement status | Single recorded run |

Compilation command:

```bash
gcc -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra -Wpedantic -std=c11 \
  -Ikernels/kernel3_qam/include \
  tests/kernel3_qam/benchmark_qam.c \
  kernels/kernel3_qam/src/qam.c \
  -o /tmp/benchmark_qam
```

The compiler produced no warnings or errors in the recorded compilation.

## 3. Measured Results

| Modulation | Elapsed time (s) | Symbol throughput (Msymbol/s) | Bit throughput (Mbit/s) |
|---|---:|---:|---:|
| QPSK | 0.169888 | 588.623 | 1177.245 |
| 16-QAM | 0.342612 | 291.875 | 1167.501 |
| 64-QAM | 0.510127 | 196.029 | 1176.177 |
| 256-QAM | 0.591685 | 169.009 | 1352.070 |

These are the measurements from one recorded benchmark run on the development
machine. They are not statistical averages across multiple independent runs.

## 4. Interpretation

### 4.1 Symbol throughput

QPSK achieved the highest measured symbol throughput at 588.623 Msymbol/s.
Symbol throughput decreased as the modulation order increased in this run.

Higher-order modulation processes more bits per symbol, so symbol throughput
alone does not indicate total bit-processing capacity.

### 4.2 Bit throughput

256-QAM achieved the highest measured bit throughput at 1352.070 Mbit/s.
Each 256-QAM symbol represents 8 bits, compared with 2 bits for QPSK,
4 bits for 16-QAM, and 6 bits for 64-QAM.

The results illustrate why both symbol throughput and bit throughput are
useful when comparing modulation schemes.

### 4.3 Measurement scope

The benchmark measures the combined mapping-and-demapping workload for each
modulation scheme. It does not independently measure mapping latency,
demapping latency, or end-to-end PHY-chain performance.

These figures should be treated as an initial performance baseline. Repeat
the benchmark under controlled conditions before drawing conclusions about
small performance differences or claiming a stable maximum throughput.

## 5. Correctness and Performance Are Separate

Benchmark throughput alone does not establish correctness. Correctness is
validated separately by the Kernel 3 reference and C tests.

## 6. Reproduction

From the repository root:

```bash
gcc -D_POSIX_C_SOURCE=200809L -O2 -Wall -Wextra -Wpedantic -std=c11 \
  -Ikernels/kernel3_qam/include \
  tests/kernel3_qam/benchmark_qam.c \
  kernels/kernel3_qam/src/qam.c \
  -o /tmp/benchmark_qam

/tmp/benchmark_qam >&2
```

## 7. Conclusion

The initial Kernel 3 benchmark completed for all four supported modulation
schemes. The recorded results provide a baseline for future optimization and
comparison. Any future performance comparison should use the same workload,
compiler settings, and measurement methodology.
