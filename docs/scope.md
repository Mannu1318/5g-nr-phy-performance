# 5G NR Layer-1 PHY Performance Analysis and Optimization

## 1. Project Objective

The objective of this project is to study the performance characteristics of selected 5G New Radio (NR) Layer-1 Physical (PHY) processing kernels on a general-purpose Intel Core i7-12700 processor.

The project follows the performance-analysis concepts used in Intel FlexRAN reference architectures, while implementing selected PHY computational kernels independently rather than reproducing the complete FlexRAN software stack.

The main goals are:

1. Implement correct scalar reference versions of selected 5G NR PHY kernels.
2. Validate the implementations using deterministic test cases and reference results.
3. Measure baseline execution time and throughput.
4. Profile the implementations to identify computational hotspots.
5. Optimize selected kernels using AVX2 SIMD instructions.
6. Study the effects of multithreading and CPU-core placement.
7. Investigate memory access patterns, cache behavior, and data layout.
8. Perform a controlled parameter sweep to understand how workload size affects performance.
9. Compare scalar, optimized, and parallel implementations using reproducible measurements.

---

## 2. Hardware and Software Environment

### 2.1 Target Hardware

The primary experimental platform is:

* CPU: Intel Core i7-12700
* Architecture: Intel hybrid x86-64 architecture
* P-cores: 8
* E-cores: 4
* Logical processors: 20
* Maximum reported frequency: approximately 4.9 GHz
* L1 cache: approximately 512 KiB instruction and 512 KiB data
* L2 cache: approximately 12 MiB
* L3 cache: approximately 25 MiB
* NUMA nodes: 1
* SIMD support: AVX2
* AVX-512: Not available

The hybrid P-core/E-core architecture is an important characteristic of the experimental platform and will be considered during multithreading and CPU-placement experiments.

### 2.2 Software Environment

The development and measurement environment includes:

* Ubuntu 24.04 LTS
* GCC 13.3
* Python 3.12
* NumPy
* SciPy
* Matplotlib
* Pandas
* CMake
* Git
* Linux `perf`

Python will primarily be used for reference implementations, validation, experiment control, and result analysis.

C/C++ will be used for performance-oriented kernel implementations and optimization experiments.

---

## 3. Selected PHY Kernels

The project focuses on six computational kernels representing different classes of PHY processing workloads.

### 3.1 CRC Attach and Check

CRC (Cyclic Redundancy Check) processing will be implemented as a bit-oriented error-detection kernel.

The transmitter-side operation will generate and attach the CRC, while the receiver-side operation will verify the CRC.

The primary performance characteristics of interest are:

* Bit-level operations
* XOR and shift operations
* Loop efficiency
* Memory access
* Potential SIMD or word-oriented optimization

Correctness will be verified against deterministic reference results.

---

### 3.2 Bit Scrambling

The scrambling kernel will apply a deterministic pseudorandom sequence to an input bit stream using XOR operations.

The corresponding descrambling operation will be used during validation to verify that the original data can be recovered.

The main performance characteristics are:

* Repetitive XOR operations
* Bit/byte representation
* Memory bandwidth
* Data layout
* SIMD optimization opportunities

The exact 5G NR scrambling sequence and parameterization will be specified when the kernel implementation is defined.

---

### 3.3 QAM Mapping and Demapping

The QAM kernel will convert groups of input bits into complex modulation symbols and perform the reverse operation during demapping.

The project will examine:

* QPSK
* 16-QAM
* 64-QAM
* 256-QAM

The main performance characteristics are:

* Bit-to-symbol conversion
* Lookup or arithmetic operations
* Complex I/Q data processing
* Branch behavior
* Data layout
* SIMD opportunities

Mapping and demapping correctness will be verified using known input/output vectors and round-trip tests.

---

### 3.4 OFDM FFT/IFFT

The OFDM kernel will implement the frequency-domain to time-domain and time-domain to frequency-domain transformations required by an OFDM processing chain.

The main computational operations are FFT and IFFT.

The project will investigate:

* Different FFT sizes
* Execution time
* Computational scaling
* Memory access patterns
* Cache effects
* SIMD optimization

The implementation will be treated as a numerical processing kernel rather than a complete 5G NR OFDM transmitter or receiver.

---

### 3.5 Simple LS Channel Estimation

A simplified Least-Squares (LS) channel-estimation kernel will be implemented using known reference symbols.

The simplified model is:

```
y = h x + n
```

where:

* `x` is the transmitted reference symbol,
* `h` is the channel coefficient,
* `n` is noise,
* `y` is the received symbol.

For a simplified single-channel case, the channel estimate can be expressed as:

```
h_hat = y / x
```

for non-zero known reference symbols.

The project will focus on the computational characteristics of repeated complex-valued channel estimation rather than implementing every detail of a complete 5G NR reference-signal processing chain.

---

### 3.6 2x2 MIMO Zero-Forcing Detection

A 2x2 MIMO zero-forcing detection kernel will be implemented to study a small complex-valued linear-algebra workload.

The simplified MIMO model is:

```
Y = H X + N
```

where:

* `H` is the channel matrix,
* `X` is the transmitted vector,
* `N` is noise,
* `Y` is the received vector.

The zero-forcing detector will estimate the transmitted vector using the channel matrix.

The kernel will be used to investigate:

* Complex multiplication
* Complex addition/subtraction
* Matrix operations
* Small-matrix inversion or equivalent processing
* SIMD opportunities
* Data layout
* Repeated linear-algebra workloads

The project specifically limits this study to a 2x2 MIMO configuration.

---

## 4. Scope of the Study

### 4.1 In Scope

The following activities are included:

* Scalar reference implementations
* Correctness validation
* Deterministic test vectors
* Runtime benchmarking
* Throughput measurement
* Performance profiling
* AVX2 optimization
* Multithreading experiments
* CPU-core placement experiments
* Memory-access analysis
* Cache-related analysis
* Data-layout experiments
* Workload-size sweeps
* Comparison of scalar and optimized implementations
* Reproducible benchmark scripts
* Visualization and analysis of collected results

---

### 4.2 Out of Scope

The following are outside the primary scope:

* Complete Intel FlexRAN source-code reproduction
* Hardware FEC acceleration
* ACC100 accelerator integration
* FPGA implementation
* Full O-RAN fronthaul implementation
* Complete 5G NR Layer-1 implementation
* Full commercial-grade base-station software
* Real-time over-the-air 5G transmission
* Complete protocol-stack implementation
* Hardware-specific AVX-512 optimization, because AVX-512 is unavailable on the target processor

An optional attempt to build or inspect the official FlexRAN environment may be performed separately, but it is not required for successful completion of the core project.

---

## 5. Correctness Validation Strategy

Performance measurements are meaningful only after correctness has been established.

Each kernel will therefore follow this development sequence:

```
Reference implementation
        ↓
Deterministic test cases
        ↓
Scalar C/C++ implementation
        ↓
Compare results
        ↓
Performance benchmark
        ↓
Optimization
        ↓
Revalidate optimized implementation
```

Optimized implementations must produce results equivalent to the validated reference implementation within the numerical tolerance appropriate to the kernel.

For numerical kernels such as FFT, channel estimation, and MIMO detection, floating-point comparison tolerances will be defined rather than requiring exact bit-for-bit equality.

For bit-oriented kernels such as CRC and scrambling, exact equality will normally be required.

---

## 6. Performance Metrics

The following metrics will be collected where applicable:

### Execution Time

The time required to process a defined input workload.

### Throughput

The amount of data or number of processing elements handled per unit time.

Examples include:

* bits/second
* symbols/second
* samples/second

### Speedup

The relative improvement compared with the scalar baseline:

```
Speedup = Baseline Time / Optimized Time
```

### CPU Utilization

CPU activity will be examined during selected experiments.

### Hardware Performance Counters

Linux `perf` will be used where appropriate to examine hardware-level behavior such as:

* CPU cycles
* Instructions
* Instructions per cycle (IPC)
* Cache-related events
* Branch-related events

The availability and interpretation of individual hardware counters may depend on the processor and Linux performance-monitoring configuration.

---

## 7. Optimization Stages

The project will use a controlled optimization sequence.

### Stage 1 — Scalar Baseline

Implement the simplest correct version of each selected kernel.

Purpose:

* Establish correctness
* Establish baseline runtime
* Provide a reference for all later optimizations

### Stage 2 — Profiling

Profile the scalar implementation to identify computational hotspots.

Purpose:

* Determine where execution time is spent
* Identify optimization targets
* Avoid optimizing code without measurement

### Stage 3 — AVX2 Optimization

Apply AVX2 SIMD optimization to suitable kernels.

Potential targets include:

* Element-wise operations
* Complex arithmetic
* Repetitive arithmetic
* Data-parallel transformations

The optimized implementation will always be compared against the validated scalar implementation.

### Stage 4 — Multithreading

Evaluate parallel execution across multiple CPU threads.

Experiments will consider the hybrid P-core/E-core architecture.

### Stage 5 — Memory and Cache Optimization

Investigate:

* Data layout
* Contiguous memory access
* Alignment where relevant
* Cache locality
* Working-set size
* Reuse of data

### Stage 6 — System-Level Benchmark Sweep

Combine the previous optimization techniques and evaluate performance across different workload parameters.

---

## 8. Benchmark Parameters

The final benchmark matrix will vary workload characteristics appropriate to each kernel.

Potential dimensions include:

* Input size
* Number of symbols
* FFT size
* Modulation order
* Number of MIMO operations
* Number of threads
* CPU placement
* Scalar versus AVX2 implementation
* Different data layouts where applicable

The exact parameter values will be defined during the benchmark-design stage after the individual kernels and their correctness tests are implemented.

---

## 9. Reproducibility

Each performance experiment should record sufficient information to reproduce the result.

Benchmark records should include, where applicable:

* Kernel name
* Implementation version
* Input size
* Algorithm parameters
* Number of iterations
* Number of threads
* CPU placement
* Execution time
* Throughput
* Speedup
* Relevant `perf` measurements
* Date/time of experiment
* Build configuration

Raw benchmark results will be stored separately from source code and used to generate plots and summary tables.

---

## 10. Expected Final Outcome

The final project will provide a measured comparison of scalar and optimized implementations of selected 5G NR PHY computational kernels on the Intel Core i7-12700 platform.

The study is intended to demonstrate how:

* Algorithmic structure,
* SIMD vectorization,
* multithreading,
* CPU placement,
* memory access,
* cache behavior,
* and workload size

affect the performance of representative PHY processing workloads.

The final results will be presented as reproducible measurements rather than claims of reproducing the performance of a complete Intel FlexRAN deployment.

---

## 11. Project Success Criteria

The project will be considered successful when:

1. All six selected kernels have working reference/scalar implementations.
2. Kernel correctness has been validated with deterministic tests.
3. Baseline performance measurements have been collected.
4. Significant performance hotspots have been identified through profiling.
5. At least selected kernels have been optimized using AVX2 where technically appropriate.
6. Multithreading behavior has been measured.
7. Memory/cache behavior has been investigated.
8. Benchmark results have been collected across defined workload parameters.
9. Results are reproducible using documented scripts and configurations.
10. The final report clearly distinguishes measured results from assumptions and limitations.
