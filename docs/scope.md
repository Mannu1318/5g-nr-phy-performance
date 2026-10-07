# Simplified 5G NR PHY End-to-End Performance Engineering

## 1. Project Objective

The objective of this project is to design, implement, validate, measure, profile, and optimize a simplified end-to-end 5G New Radio (NR) Layer-1 Physical (PHY) processing chain on a general-purpose Intel Core i7-12700 processor.

The project evolved from studying individual PHY computational kernels into an integrated transmitter and receiver processing chain, with emphasis on understanding how the stages interact while applying systematic performance engineering techniques.

The main goals are:
1. Implement correct reference and optimized versions of the major stages in the simplified 5G NR PHY transmitter and receiver chain.
2. Validate individual stages using deterministic test cases and reference results.
3. Integrate the stages into a functional end-to-end TX/channel/RX processing flow.
4. Measure baseline execution time, throughput, and end-to-end performance.
5. Profile the implementation to identify computational hotspots and performance bottlenecks.
6. Optimize selected computationally intensive stages using AVX2 SIMD instructions and other suitable techniques.
7. Study the effects of multithreading, CPU-core placement, memory access patterns, cache behavior, and data layout.
8. Perform controlled parameter sweeps to understand how workload size, modulation, FFT configuration, and other system parameters affect performance.
9. Compare scalar, optimized, and parallel implementations and evaluate both individual-kernel and complete-chain performance using reproducible measurements.

---
## 2. End-to-End PHY Processing Architecture

The project models a simplified end-to-end 5G NR PHY processing chain consisting of transmitter-side processing, a simplified wireless channel, and receiver-side processing. The individual stages are studied independently for performance engineering and are also integrated to evaluate complete-chain behavior.

### 2.1 Transmitter Processing

```text
Information Bits
      ↓
CRC Attachment
      ↓
Bit Scrambling
      ↓
QAM Mapping
      ↓
OFDM / IFFT
      ↓
2×2 MIMO Transmission
      ↓
Simplified Channel
```

### 2.2 Receiver Processing

```text
Received Signal
      ↓
Channel Estimation
      ↓
2×2 MIMO Zero-Forcing Detection
      ↓
OFDM / FFT
      ↓
QAM Demapping
      ↓
Bit Descrambling
      ↓
CRC Verification
      ↓
Recovered Bits
```

The receiver reconstructs the transmitted information bits by reversing the corresponding transmitter operations. Bit scrambling and descrambling use the self-inverse XOR operation, while CRC verification provides an integrity check on the recovered information bits.

This architecture is intentionally simplified for performance-engineering study. It is not intended to represent a complete production-grade or fully 3GPP-compliant 5G NR modem implementation.


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


## 3. Selected PHY Processing Kernels

The project is organized around six major PHY processing areas that together form a simplified end-to-end transmitter and receiver chain.

Each processing area is studied as an individual computational kernel using the project workflow:

```text
Understand → Implement → Validate → Measure → Profile → Optimize → Analyze
```

The kernels are then connected to form the simplified TX/channel/RX processing flow.

### 3.1 CRC Attach and Check

CRC processing provides error-detection functionality at the transmitter and receiver.

At the transmitter:

Information Bits → CRC Generation → CRC Attachment

At the receiver:

Recovered Bits → CRC Verification → Valid/Invalid Result

The project uses the CRC24A algorithm specified for 5G NR in 3GPP TS 38.212, Clause 5.1.

The CRC kernel has already been implemented, validated, benchmarked, profiled, and optimized as Kernel 1.

Performance analysis includes:

Bit-level operations
XOR and shift operations
Loop efficiency
Memory access
Lookup-table optimization
SIMD/AVX2 investigation
### 3.2 Bit Scrambling and Descrambling

Bit scrambling is applied after CRC attachment at the transmitter.

The corresponding descrambling operation is performed at the receiver.

TX: Information + CRC → Scrambling → Scrambled Bits
RX: Descrambling → Recovered Bits

The scrambling sequence uses the 5G NR pseudorandom sequence defined in 3GPP TS 38.211.

Scrambling and descrambling use XOR operations. Since XOR is self-inverse, applying the same sequence again recovers the original bits.

The scrambling kernel has already been implemented, validated, benchmarked, profiled, and optimized as Kernel 2.

Performance analysis includes:

LFSR sequence generation
XOR operations
Bit/byte representation
Memory access
Data layout
SIMD optimization opportunities
### 3.3 QAM Mapping and Demapping

QAM processing converts groups of bits into complex-valued modulation symbols at the transmitter and performs the reverse operation at the receiver.

TX: Bits → QAM Mapping → Complex Symbols
RX: Complex Symbols → QAM Demapping → Bits

The project will investigate:

QPSK
16-QAM
64-QAM
256-QAM

Performance analysis will include:

Bit-to-symbol conversion
Symbol-to-bit conversion
Lookup-table versus arithmetic approaches
Complex I/Q processing
Branch behavior
Data layout
SIMD opportunities

Correctness will be validated using deterministic vectors and mapping/demapping round-trip tests.

### 3.4 OFDM FFT/IFFT

OFDM processing connects the frequency-domain modulation symbols with the time-domain waveform.

At the transmitter:

Frequency-Domain Symbols → IFFT → Time-Domain Samples

At the receiver:

Time-Domain Samples → FFT → Frequency-Domain Symbols

The project will investigate:

Different FFT sizes
FFT/IFFT execution time
Computational scaling
Memory access patterns
Cache behavior
SIMD optimization opportunities

The implementation is intended as a simplified numerical OFDM kernel rather than a complete 3GPP NR waveform implementation.

### 3.5 Channel Estimation

Channel estimation is performed at the receiver using known reference symbols.

The simplified channel model is:

y = h x + n

where:

x is the transmitted reference symbol,
h is the channel coefficient,
n is noise,
y is the received symbol.

For a simplified single-channel case:

h_hat = y / x

for non-zero known reference symbols.

The kernel will focus on repeated complex-valued channel-estimation operations and their performance characteristics rather than implementing every detail of complete 5G NR reference-signal processing.

### 3.6 2×2 MIMO Transmission and Zero-Forcing Detection

The MIMO stage models transmission over two spatial streams and receiver-side zero-forcing detection.

The simplified system model is:

Y = H X + N

where:

H is the 2×2 channel matrix,
X is the transmitted symbol vector,
N is noise,
Y is the received vector.

At the transmitter, two spatial streams are formed for 2×2 MIMO transmission.

At the receiver, the zero-forcing detector estimates the transmitted vector using the channel matrix:

X_hat ≈ H⁻¹ Y

The kernel will investigate:

Complex multiplication
Complex addition/subtraction
Small-matrix operations
Matrix inversion or equivalent processing
Data layout
SIMD opportunities
Repeated linear-algebra workloads

The study is limited to a simplified 2×2 MIMO configuration.

## 4. Scope of the Study

### 4.1 In Scope

The project includes the implementation, integration, validation, measurement, and optimization of a simplified end-to-end 5G NR PHY processing chain.

The main activities include:

* Python reference implementations for algorithm development and validation
* Scalar C implementations for performance measurement
* Transmitter-side processing from information bits to a simplified transmitted waveform
* Receiver-side processing from received samples to recovered information bits
* CRC generation and receiver-side CRC verification
* Bit scrambling and receiver-side descrambling
* QAM mapping and demapping
* OFDM IFFT and FFT processing
* Simplified LS channel estimation
* Simplified 2×2 MIMO transmission and zero-forcing detection
* Deterministic correctness testing
* End-to-end round-trip validation
* Runtime benchmarking
* Throughput measurement
* Performance profiling using Linux perf
* AVX2 optimization where applicable
* Multithreading experiments
* CPU-core placement experiments
* Memory-access and data-layout analysis
* Cache-related performance analysis
* Workload-size sweeps
* Comparison of scalar and optimized implementations
* Reproducible benchmark scripts
* Visualization and analysis of collected performance results

The complete chain is treated as a simplified engineering model rather than a production-grade 5G NR modem.

### 4.2 Out of Scope

The following are outside the primary scope:

* Complete 3GPP-compliant 5G NR Layer-1 implementation
* Complete Intel FlexRAN source-code reproduction
* Hardware FEC acceleration
* ACC100 accelerator integration
* FPGA implementation
* Full O-RAN fronthaul implementation
* Full commercial-grade base-station software
* Real-time over-the-air 5G transmission
* Complete 5G NR protocol-stack implementation
* Complete physical-channel processing for every NR channel
* Full 3GPP reference-signal implementation
* Hardware-specific AVX-512 optimization, because AVX-512 is unavailable on the target processor

An optional attempt to build or inspect the official FlexRAN environment may be performed separately, but it is not required for successful completion of the core project.

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

After individual kernel validation, the integrated TX/channel/RX chain will also be tested using controlled inputs to verify that the receiver can recover the expected information and that the final CRC check succeeds under the simplified channel model.


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


## 10. Expected Final Outcome

The final project will provide a measured performance study of a simplified end-to-end 5G NR PHY processing chain on the Intel Core i7-12700 platform.

The completed chain will demonstrate the flow from information bits through transmitter-side processing, a controlled channel model, and receiver-side processing to recovered information bits and final CRC verification.

The study will compare scalar and optimized implementations and investigate how:

* Algorithmic structure,
* SIMD vectorization,
* multithreading,
* CPU placement,
* memory access,
* cache behavior,
* data layout,
* and workload size

affect the performance of representative PHY processing stages.

The final results will be presented as reproducible measurements. They will describe the behavior of the simplified implementation and will not claim to reproduce the performance of a complete commercial 5G modem or Intel FlexRAN deployment.


## 11. Project Success Criteria

The project will be considered successful when:

1. All six selected PHY processing areas have working reference/scalar implementations.
2. Individual kernel correctness has been validated with deterministic tests.
3. The transmitter, simplified channel, and receiver stages can be integrated into an end-to-end processing flow.
4. The receiver can recover the expected information under the defined controlled channel conditions.
5. Final receiver-side CRC verification succeeds for valid end-to-end test cases.
6. Baseline performance measurements have been collected for the selected kernels and integrated chain where applicable.
7. Significant performance hotspots have been identified through profiling.
8. Selected computationally intensive kernels have been optimized using AVX2 where technically appropriate.
9. Multithreading, memory access, cache behavior, and workload-size effects have been investigated.
10. Benchmark results are reproducible using documented scripts and configurations.
11. The final report clearly distinguishes measured results, assumptions, simplifications, and limitations of the study.
