# Kernel 3 — 5G NR QAM Mapping and Demapping Specification

## 1. Purpose

Kernel 3 implements QAM modulation and demodulation for the 5G NR PHY performance-engineering project.

The kernel converts binary input bits into complex-valued QAM symbols at the transmitter and converts received complex-valued QAM symbols back into binary bits at the receiver.

The supported modulation schemes are:

* QPSK
* 16-QAM
* 64-QAM
* 256-QAM

The primary objectives are:

* Correctness
* Deterministic behavior
* Python reference implementation
* C scalar implementation
* Python/C cross-validation
* Performance benchmarking
* Linux `perf` profiling
* Optimization
* Lookup-table investigation
* AVX2/SIMD feasibility investigation

---

## 2. Reference Specification

The QAM mapping conventions are based on:

**3GPP TS 38.211 — NR; Physical channels and modulation**

Relevant section:

**Clause 5.1 — Modulation mapper**

The implementation will reproduce the specified NR bit-to-symbol mapping conventions for the supported modulation schemes.

---

## 3. Kernel Scope

Kernel 3 contains two operations:

```text
                 KERNEL 3

TX:
Binary bits
    |
    v
QAM Mapper
    |
    v
Complex QAM symbols


RX:
Complex QAM symbols
    |
    v
QAM Demapper
    |
    v
Recovered binary bits
```

The demapper will initially use **hard-decision demapping**.

Soft-output demapping and LLR generation are outside the scope of this kernel.

---

## 4. Supported Modulation Schemes

| Modulation |   M | Bits/Symbol |
| ---------- | --: | ----------: |
| QPSK       |   4 |           2 |
| 16-QAM     |  16 |           4 |
| 64-QAM     |  64 |           6 |
| 256-QAM    | 256 |           8 |

The number of bits per symbol is:

$$
Q_m = \log_2(M)
$$

---

## 5. Input and Output

### 5.1 Mapper Input

The mapper accepts:

* Binary input bits
* Modulation order

Valid modulation orders:

```text
4
16
64
256
```

Each input bit must be either:

```text
0
1
```

The input length must be an exact multiple of the number of bits per symbol.

---

### 5.2 Mapper Output

The mapper produces complex-valued QAM symbols:

$$
s = I + jQ
$$

where:

* \(I\) is the in-phase component
* \(Q\) is the quadrature component

The constellation is normalized to unit average symbol energy.

---

### 5.3 Demapper Input

The demapper accepts:

* Complex-valued QAM symbols
* Modulation order

The initial correctness tests assume ideal symbols without noise or channel distortion.

---

### 5.4 Demapper Output

The demapper produces the corresponding binary bits.

For ideal symbols:

```text
demap(map(bits)) == bits
```

must always hold.

---

## 6. Bit Ordering

For all supported QAM schemes:

* Even-indexed bits contribute to the I component.
* Odd-indexed bits contribute to the Q component.

### QPSK

```text
I <- b0
Q <- b1
```

### 16-QAM

```text
I <- b0, b2
Q <- b1, b3
```

### 64-QAM

```text
I <- b0, b2, b4
Q <- b1, b3, b5
```

### 256-QAM

```text
I <- b0, b2, b4, b6
Q <- b1, b3, b5, b7
```

---

## 7. QPSK Mapping

Two bits produce one complex symbol:

```text
b0 b1
```

The NR mapping is:

$$
d =
\frac{1}{\sqrt{2}}
\left[
(1-2b_0) + j(1-2b_1)
\right]
$$

The unnormalized I/Q levels are:

```text
I,Q ∈ {-1,+1}
```

The mapping is:

| Bits |  I |  Q |
| ---- | -: | -: |
| 00   | +1 | +1 |
| 01   | +1 | -1 |
| 10   | -1 | +1 |
| 11   | -1 | -1 |

Normalization factor:

$$
\frac{1}{\sqrt{2}}
$$

---

## 8. 16-QAM Mapping

Four bits produce one complex symbol:

```text
b0 b1 b2 b3
```

The I component is determined by:

```text
b0, b2
```

The Q component is determined by:

```text
b1, b3
```

The unnormalized I/Q levels are:

```text
-3, -1, +1, +3
```

The normalization factor is:

$$
\frac{1}{\sqrt{10}}
$$

The normalized symbol is:

$$
d = \frac{I+jQ}{\sqrt{10}}
$$

---

## 9. 64-QAM Mapping

Six bits produce one complex symbol:

```text
b0 b1 b2 b3 b4 b5
```

The I component is determined by:

```text
b0, b2, b4
```

The Q component is determined by:

```text
b1, b3, b5
```

The unnormalized I/Q levels are:

```text
-7, -5, -3, -1, +1, +3, +5, +7
```

The normalization factor is:

$$
\frac{1}{\sqrt{42}}
$$

The normalized symbol is:

$$
d = \frac{I+jQ}{\sqrt{42}}
$$

---

## 10. 256-QAM Mapping

Eight bits produce one complex symbol:

```text
b0 b1 b2 b3 b4 b5 b6 b7
```

The I component is determined by:

```text
b0, b2, b4, b6
```

The Q component is determined by:

```text
b1, b3, b5, b7
```

The unnormalized I/Q levels are:

```text
-15, -13, -11, -9,
-7, -5, -3, -1,
+1, +3, +5, +7,
+9, +11, +13, +15
```

The normalization factor is:

$$
\frac{1}{\sqrt{170}}
$$

The normalized symbol is:

$$
d = \frac{I+jQ}{\sqrt{170}}
$$

---

## 11. Normalization

For square M-QAM, the normalization factor is:

$$
\alpha =
\sqrt{\frac{3}{2(M-1)}}
$$

Therefore:

| Modulation | Normalization    |
| ---------- | ---------------- |
| QPSK       | \(1/\sqrt{2}\)   |
| 16-QAM     | \(1/\sqrt{10}\)  |
| 64-QAM     | \(1/\sqrt{42}\)  |
| 256-QAM    | \(1/\sqrt{170}\) |

The normalized constellation has unit average symbol energy:

$$
E[|s|^2] = 1
$$

---

## 12. Demapping

Kernel 3 uses hard-decision demapping.

The demapper determines the nearest valid constellation point and converts the corresponding I/Q levels back into the original bit pattern.

Conceptually:

```text
Received complex symbol
        |
        v
Determine nearest I/Q levels
        |
        v
Convert I level -> I bits
Convert Q level -> Q bits
        |
        v
Reconstruct original bit order
```

For ideal symbols:

```text
bits
  |
  v
QAM mapper
  |
  v
complex symbol
  |
  v
QAM demapper
  |
  v
bits'
```

The required condition is:

```text
bits' == bits
```

---

## 13. Error Handling

The implementation must reject invalid modulation orders.

Valid values:

```text
4
16
64
256
```

The mapper must reject non-binary input values.

Valid bit values:

```text
0
1
```

The mapper must reject input lengths that are not divisible by the required bits per symbol.

Required conditions:

```text
QPSK:
input_length % 2 == 0

16-QAM:
input_length % 4 == 0

64-QAM:
input_length % 6 == 0

256-QAM:
input_length % 8 == 0
```

---

## 14. Correctness Requirements

### 14.1 Exhaustive Testing

Every possible bit pattern must be tested for every supported modulation scheme.

Number of patterns:

```text
QPSK    -> 4
16-QAM  -> 16
64-QAM  -> 64
256-QAM -> 256
```

For every pattern:

```text
demap(map(bits)) == bits
```

must hold.

---

### 14.2 Randomized Testing

Random binary sequences must be generated and tested using:

```text
mapper -> demapper
```

The recovered sequence must exactly match the original sequence.

---

### 14.3 Boundary Testing

Tests must include:

* One symbol
* Multiple symbols
* Large input sequences
* Minimum valid input
* Exact symbol boundaries
* Invalid non-divisible input lengths
* Invalid bit values
* Invalid modulation orders

---

### 14.4 Python/C Cross-Validation

The Python implementation will serve as the initial behavioral reference.

The C implementation must produce equivalent mapping and demapping results.

Validation flow:

```text
Python reference
       |
       v
Golden outputs
       |
       v
C implementation
       |
       v
Compare outputs
```

---

## 15. Performance Measurement

After correctness is established, performance will be measured.

Primary metrics:

* Total execution time
* Symbols processed per second
* Bits processed per second
* Time per symbol
* Cycles per symbol
* Cycles per input bit

Large input buffers will be used to reduce measurement noise.

---

## 16. Profiling

Linux `perf` will be used to investigate the implementation.

Planned tools include:

```text
perf stat
perf record
perf report
```

Potential hardware/software events include:

* cycles
* instructions
* branches
* branch misses
* cache references
* cache misses

The exact available events will depend on the CPU and Linux performance-counter configuration.

---

## 17. Optimization Investigation

After establishing a scalar baseline, possible optimizations include:

1. Direct bit manipulation
2. Reduced branching
3. Precomputed constellation tables
4. Lookup-table based mapping
5. Efficient hard-decision demapping
6. Improved memory access
7. Loop optimization
8. Compiler optimization
9. AVX2/SIMD investigation

Optimization decisions must be based on measurements and profiling results.

---

## 18. Reference and Optimized Implementations

The project will maintain a distinction between:

### Reference implementation

Priorities:

* Readability
* Mathematical transparency
* Correctness
* Easy validation

### Optimized implementation

Priorities:

* Throughput
* Low instruction count
* Efficient memory access
* Reduced branching
* SIMD/vectorization where beneficial

The optimized implementation must always be validated against the reference implementation.

---

## 19. Kernel Boundary

### Transmitter side

Kernel 3 begins with:

```text
Binary scrambled bits
```

and produces:

```text
Complex QAM symbols
```

### Receiver side

Kernel 3 accepts:

```text
Complex symbols after receiver-side processing
```

and produces:

```text
Recovered binary bits
```

Kernel 3 does not implement:

* CRC
* Bit scrambling
* Bit descrambling
* OFDM
* FFT/IFFT
* Channel estimation
* MIMO detection
* Channel coding
* Channel decoding

These operations belong to other components of the project.

---

## 20. Planned Interface

Conceptually:

```text
qam_map(bits, modulation_order)
    -> complex symbols

qam_demap(symbols, modulation_order)
    -> bits
```

The exact C API will be finalized during implementation.

---

## 21. Definition of Done

Kernel 3 is considered complete when:

* [ ] 3GPP mapping convention documented
* [ ] QPSK mapper implemented
* [ ] 16-QAM mapper implemented
* [ ] 64-QAM mapper implemented
* [ ] 256-QAM mapper implemented
* [ ] Hard-decision demapper implemented
* [ ] Python reference implementation complete
* [ ] Exhaustive constellation tests pass
* [ ] Randomized tests pass
* [ ] Invalid-input tests pass
* [ ] C scalar implementation complete
* [ ] Python/C cross-validation passes
* [ ] Baseline benchmark completed
* [ ] `perf` profiling completed
* [ ] Optimization experiments completed
* [ ] Lookup-table investigation completed
* [ ] AVX2/SIMD feasibility investigated
* [ ] Final benchmark completed
* [ ] Results documented
* [ ] Git commit created
* [ ] Changes pushed to repository

---

## 22. Kernel 3 Workflow

```text
Specification
      |
      v
Python reference
      |
      v
Correctness testing
      |
      v
C scalar implementation
      |
      v
Python/C cross-validation
      |
      v
Benchmarking
      |
      v
perf profiling
      |
      v
Optimization
      |
      v
Lookup-table investigation
      |
      v
AVX2 investigation
      |
      v
Final benchmarking
      |
      v
Documentation
      |
      v
Git commit and push
      |
      v
KERNEL 3 COMPLETE
```

