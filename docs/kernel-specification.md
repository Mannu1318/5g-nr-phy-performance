# Kernel Specification

## 1. CRC Attach and Check

### 1.1 Purpose

The CRC kernel provides error-detection processing for a block of input bits.

The transmitter-side operation calculates CRC parity bits from an input data block and attaches the parity bits to the data.

The receiver-side operation checks a received block by evaluating the CRC and determining whether the received data passes the CRC check.

The implementation is intended to represent a computationally important bit-processing kernel within a 5G NR Layer-1 PHY workload.

---

### 1.2 Standards Reference

The CRC implementation will be based on the applicable CRC procedures defined by:

* 3GPP TS 38.212 — NR; Multiplexing and channel coding.

For the initial implementation, this project will use CRC24A.

CRC length:
    24 bits

Generator polynomial:

    gCRC24A(D) =
    D^24 + D^23 + D^18 + D^17 + D^14 + D^11 +
    D^10 + D^7 + D^6 + D^5 + D^4 + D^3 + D + 1

The CRC procedure and bit ordering will follow the applicable
CRC calculation procedure defined in 3GPP TS 38.212.

The exact TS 38.212 release used for implementation and the
corresponding clause will be recorded before the reference
implementation is written.

The project will explicitly document the TS 38.212 release/version used so that the implementation remains reproducible.

---

### 1.3 Kernel Operations

The CRC implementation will provide two primary operations.

#### CRC Attach

Input:

* A sequence of input data bits.

Output:

* The original data bits followed by the calculated CRC parity bits.

Conceptually:

```
data bits
    +
CRC parity bits
    =
output block
```

#### CRC Check

Input:

* A received block containing data bits and CRC parity bits.

Output:

* A CRC validation result indicating whether the block passes the CRC check.

Conceptually:

```
received block
      ↓
CRC calculation/check
      ↓
  PASS / FAIL
```

---

### 1.4 Input Representation

The initial reference implementation will represent the input as a sequence of binary values.

For example:

```
0 1 1 0 1 0 0 1 ...
```

The implementation will distinguish clearly between:

* logical bits,
* storage representation,
* number of bits processed.

The first scalar implementation will prioritize clarity and correctness rather than attempting to optimize the representation.

---

### 1.5 Scalar Processing Model

The scalar baseline will process the input sequentially.

The conceptual processing loop will involve operations such as:

* reading an input bit,
* examining the current CRC state,
* applying XOR operations where required,
* shifting the CRC state,
* continuing until the complete input block has been processed.

The scalar version will serve as the correctness reference and performance baseline for later optimization.

---

### 1.6 Correctness Requirements

CRC correctness will be verified using deterministic test cases.

The tests will include:

1. Known input data with a known expected CRC.
2. CRC attachment followed by CRC checking.
3. Unmodified data that must pass the CRC check.
4. Modified data that should fail the CRC check.
5. Multiple input lengths.
6. Boundary cases such as very small and larger input blocks.

For bit-oriented CRC operations, expected results will normally be compared exactly.

---

### 1.7 Round-Trip Test

A fundamental test will be:

```
original data
      ↓
  CRC attach
      ↓
data + CRC
      ↓
   CRC check
      ↓
    PASS
```

A second test will intentionally modify one or more bits:

```
original data
      ↓
  CRC attach
      ↓
data + CRC
      ↓
 modify bit(s)
      ↓
   CRC check
      ↓
    FAIL
```

This provides a simple end-to-end correctness test.

---

### 1.8 Performance Metrics

The CRC kernel will be measured using:

* Execution time
* Processed bits per second
* Throughput
* Speedup relative to the scalar baseline
* CPU cycles where measurable
* Instructions where measurable
* IPC where useful

The primary performance comparison will initially be:

```
Scalar CRC
    vs.
Optimized CRC
```

---

### 1.9 Optimization Opportunities

Potential optimization areas include:

* Reducing loop overhead
* Processing multiple bits per operation
* Word-oriented processing
* Lookup-table approaches
* Improved memory access
* SIMD/vectorization where appropriate
* Reducing unnecessary branches

Optimization will only be applied after correctness of the scalar implementation has been established.

---

### 1.10 Initial Benchmark Dimensions

The CRC benchmark will eventually vary:

* Input block length
* Number of repeated blocks
* Scalar versus optimized implementation
* Potentially different CRC configurations where applicable

Exact benchmark sizes will be selected during benchmark design rather than assumed at this stage.

---

### 1.11 Project Boundary

The CRC kernel is a standalone computational study.

It does not attempt to reproduce the complete NR transport-channel processing chain.

The purpose is to isolate CRC computation so that its computational behavior can be measured, profiled, and optimized independently.


## Implementation Reference and CRC24A Configuration

The CRC implementation is based on:

3GPP TS 38.212 V19.4.0, Release 19
Clause 5.1 — CRC calculation

The selected CRC variant is CRC24A.

CRC length:

    L = 24 bits


Generator polynomial:

    gCRC24A(D) =
    D^24 + D^23 + D^18 + D^17 + D^14 + D^11 +
    D^10 + D^7 + D^6 + D^5 + D^4 + D^3 + D + 1

The corresponding polynomial representation with the leading D^24
term omitted is:
          
      0x864CFB


The CRC procedure follows the systematic encoding definition in
TS 38.212 Clause 5.1. The input bits are denoted a_0 ... a_(A-1)
and the parity bits are denoted p_0 ... p_(L-1).

The resulting CRC-attached sequence is:

    b_k = a_k
        for k = 0 ... A-1

    b_k = p_(k-A)
        for k = A ... A+L-1

For this project, the standalone CRC24A reference implementation will
operate on an explicitly defined sequence of binary input bits.

The implementation will process the input in the same bit order used
by the reference test vectors. The bit representation and processing
convention will be documented alongside the reference implementation
so that the Python and C implementations use the same definition.

Correctness will first be established using the Python reference
implementation before the optimized C implementation is developed.
