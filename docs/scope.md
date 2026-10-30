# Simplified 5G NR PHY Performance Engineering

## 1. Project Overview

This project implements, validates, benchmarks, profiles, and experimentally evaluates selected 5G New Radio (NR) Layer-1 Physical (PHY) processing kernels on an Intel Core i7-12700 processor.

The work progressed from standalone computational kernels to an integrated experimental 2×2 MIMO transmitter, channel, and receiver chain. It emphasizes algorithm correctness, Python-to-C validation, performance measurement, and analysis of channel and receiver behavior.

This is an educational performance-engineering implementation, **not a complete or fully 3GPP-compliant 5G NR modem**.

## 2. Development Methodology

The project follows this workflow:

```text
Understand → Specify → Implement Python Reference → Implement C
     → Validate → Benchmark → Profile → Optimize → Analyze → Document
```

Python reference implementations establish algorithm behavior. C implementations support cross-validation and performance-oriented experimentation. Correctness is established before performance results are interpreted.

Optimization is applied selectively where appropriate and supported by measurements.

## 3. Implemented PHY Kernels

Six standalone processing kernels have been implemented.

### Kernel 1 — CRC24A

Implements CRC24A generation and verification for the selected NR use case, based on 3GPP TS 38.212, Clause 5.1.

Work includes Python reference and C implementations, deterministic tests, Python/C validation, benchmarking, profiling, and performance-oriented implementation comparisons. This kernel does not implement complete transport-channel processing.

### Kernel 2 — Scrambling and Descrambling

Implements the NR pseudorandom scrambling sequence and XOR-based bit scrambling/descrambling, based on 3GPP TS 38.211.

Work includes Python reference and alternative C implementations, sequence-generation validation, long-sequence testing, benchmarking, and optimization experiments.

### Kernel 3 — QAM Mapping and Demapping

Implements:
- QPSK
- 16-QAM
- 64-QAM
- 256-QAM

Includes Python reference and C implementations, deterministic mapping/demapping tests, round-trip tests, and cross-validation.

### Kernel 4 — OFDM Processing

Implements simplified OFDM processing:
- Transmitter IFFT.
- Receiver FFT.
- Subcarrier mapping and extraction.
- Cyclic-prefix insertion and removal.

This is a numerical OFDM kernel, not a complete NR waveform implementation.

### Kernel 5 — LS Channel Estimation

Implements simplified least-squares channel estimation using known pilot/reference observations and linear interpolation. It is used by the principal integrated receiver and evaluated through deterministic tests and channel-estimation experiments.

### Kernel 6 — 2×2 MIMO Zero-Forcing Detection

Implements a 2×2 MIMO Zero-Forcing detector using the channel matrix and received symbol vector.

Includes Python reference and C implementations, input validation, numerical-status handling, singular/near-singular channel handling, and Python/C cross-validation.

## 4. Integrated 2×2 MIMO PHY Chain

The standalone kernels were brought together in an experimental 2×2 MIMO link.

### Transmitter

The simplified transmitter performs:
1. Payload bit generation.
2. CRC attachment.
3. Scrambling.
4. QAM mapping.
5. OFDM subcarrier mapping.
6. IFFT processing.
7. Cyclic-prefix insertion.

### Channel

The experimental channel supports:
- AWGN.
- Configured multipath propagation.
- A 2×2 MIMO channel matrix.
- Reproducible random channel and noise generation.

### Receiver

The receiver performs:
1. Cyclic-prefix removal.
2. FFT processing.
3. Resource-grid extraction.
4. Channel estimation.
5. 2×2 MIMO Zero-Forcing detection.
6. QAM demapping.
7. Descrambling.
8. CRC verification and payload comparison.

The integrated chain is an experimental link-level implementation. It does not include every processing stage required by a complete NR modem, including channel coding and full standardized frame/resource configuration.

## 5. Experiments and Performance Analysis

The project includes controlled experiments to evaluate link behavior and receiver processing. Results are empirical for the documented configurations and trial counts.

### 5.1 AWGN Sweep

A reproducible AWGN experiment evaluates the integrated link across nine configured noise variances, with 100 trials per condition.

The experiment records noise measurements, SNR, bit-error behavior, CRC outcomes, and payload recovery. Results are documented in `results/integration_awgn/awgn_report.md`.

### 5.2 Flat and Multipath Channel Comparison

A 100-trial experiment compares flat-channel and configured multipath-channel behavior at multiple noise levels.

It evaluates BER, packet/payload error behavior, CRC success, exact payload recovery, channel condition number, and channel-estimation error.

The multipath profile uses configured integer delays and relative path powers. It is a controlled educational channel model, not a standardized 3GPP TDL/CDL channel model.

Results are documented in `results/integration_multipath_100trial/multipath_report.md`.

### 5.3 Delay-Domain Channel Estimation

An experimental delay-domain least-squares estimator is compared with the existing Kernel 5 LS estimator using linear interpolation.

The comparison evaluates channel-estimation NMSE across configured noise variances. For the tested integer-delay channel model, the delay-domain estimator achieves lower NMSE than linear interpolation.

This finding is specific to the configured channel model and experiment. It does not establish universal superiority or guarantee equivalent end-to-end payload recovery.

Results are documented in:
- `results/integration_multipath/delay_domain_comparison_full_20261030/delay_domain_comparison_report.md`
- `docs/delay-domain-channel-estimation-results.md`

### 5.4 MMSE and Zero-Forcing Receiver Comparison

An isolated experiment compares MMSE and ZF detection using the same received data and exact oracle channel knowledge.

The experiment evaluates BER, CRC success, and payload recovery over multiple noise levels. MMSE reduces BER in the tested nonzero-noise conditions.

The experiment is deliberately isolated: the production ZF detector remains unchanged. The comparison uses oracle channel information, so it does not represent a complete practical receiver comparison.

Results are documented in `results/integration_multipath/mmse_zf_comparison/mmse_zf_comparison_report.md`.

### 5.5 Oracle-Channel Receiver Comparison

A further experiment compares three channel-information approaches:
- Kernel 5 LS estimation with linear interpolation.
- Experimental delay-domain LS estimation.
- Exact oracle channel frequency response.

All approaches use the same received grid, ZF detector, demapper, descrambler, CRC, and payload-scoring logic.

The results show that channel-estimation quality affects receiver performance in the tested multipath conditions. The oracle case provides a reference, but AWGN and other link limitations remain.

The oracle channel is an experimental reference and is not available to a practical receiver.

Results are documented in `results/integration_multipath/oracle_channel_comparison/oracle_comparison_report.md`.

## 6. Validation and Testing

Correctness is evaluated through:
- Deterministic unit tests for individual kernels.
- Python reference versus C implementation comparisons where applicable.
- Mapping/demapping and scrambling/descrambling round-trip tests.
- Numerical edge-case and invalid-input tests.
- Integrated transmitter–channel–receiver tests.
- Reproducible experiment tests and result checks.

The repository uses pytest. Run the test suite from the repository root using the command `pytest -q`.

The full regression suite was run using `pytest -q` during final documentation review and completed with **388 passed in 0.83 seconds**.

## 7. Performance Engineering

The project investigates performance at the kernel level through benchmarking and profiling, with particular attention to the difference between Python reference behavior and C implementations.

The work includes:
- Runtime benchmarking under documented input sizes and repetitions.
- Profiling to identify computational hotspots.
- Comparisons of alternative C implementations for selected kernels.
- Measurement-based optimization where justified.
- Documentation of correctness and performance trade-offs.

Performance results depend on the processor, compiler, compiler options, software versions, input sizes, and measurement conditions. They should be interpreted within their documented experimental context.

### Performance Metrics

The following metrics are evaluated where applicable:

- **Execution time:** Time required to process a defined workload.
- **Throughput:** Processing rate, expressed where appropriate in bits/second, symbols/second, or samples/second.
- **Speedup:** Ratio of baseline execution time to the compared implementation's execution time.
- **Hardware performance counters:** Selected Linux `perf` measurements, such as CPU cycles, instructions, instructions per cycle (IPC), and cache or branch events, where available.

The availability and interpretation of hardware counters depend on the processor and system configuration.

The project does not claim that every kernel uses multithreading, explicit SIMD, cache blocking, or CPU-affinity optimization. Such techniques are not presented as completed work unless supported by specific implementation and measurements.

## 8. Development Environment

The project was developed and tested in an Ubuntu 24.04 environment on an Intel Core i7-12700 system.

The development toolchain includes GCC, Python, NumPy, SciPy, Matplotlib, Pandas, pytest, CMake, and Linux perf. Exact versions and environment details are maintained in `environment.md`.

The environment document is the reference for reproducing the development setup.

## 9. Reproducibility and Interpretation

Experiments use documented configurations and fixed random seeds where applicable. Their reports record the relevant parameters, trial counts, metrics, and output locations.

Reported results are measurements from the specified implementation and test environment. They are not guarantees of performance on other hardware or under different channel conditions.

The experimental multipath model is a controlled educational model. Results should not be interpreted as standardized 3GPP channel-model conformance or as proof of performance in a deployed cellular network.

## 10. Project Scope and Limitations

The completed work focuses on selected PHY processing kernels and an experimental 2×2 MIMO link.

The project does not claim to implement:
- A complete 3GPP-compliant NR modem or full protocol stack.
- NR channel coding, including LDPC and Polar coding.
- Complete standardized NR frame, scheduling, and resource-allocation procedures.
- Standardized TDL/CDL channel-model conformance.
- A production-ready real-time radio implementation.
- Universal performance superiority of one estimator or detector.

Experimental delay-domain estimation and MMSE detection are comparison studies. They do not replace the production Kernel 5 estimator or Kernel 6 ZF detector.

## 11. Project Outcome

The project delivers six standalone PHY processing kernels, Python reference implementations, C implementations where applicable, validation tests, benchmarks, profiling work, and an integrated experimental 2×2 MIMO transmitter–channel–receiver chain.

It also includes reproducible AWGN and multipath experiments, channel-estimation comparisons, and receiver-performance investigations.

The final outcome is a documented educational performance-engineering project demonstrating how selected 5G NR PHY algorithms can be implemented, validated, measured, integrated, and analyzed using Python and C.
