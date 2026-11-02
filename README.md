# 5G NR PHY Performance Engineering

An educational implementation and performance study of selected 5G NR Physical Layer (PHY) processing kernels using Python and C, progressing from standalone algorithms to an experimental end-to-end 2x2 MIMO link.

## Project Overview

This project explores how selected 5G NR PHY algorithms can be specified, implemented, validated, benchmarked, profiled, integrated, and experimentally evaluated.

Python reference implementations establish algorithm behavior. C implementations support cross-validation and performance-oriented experimentation.

> **Scope:** This is an educational and experimental implementation, not a complete or fully 3GPP-compliant 5G NR modem.

## Key Highlights

- Six standalone PHY processing kernels.
- Python reference and C implementations.
- Cross-validation between Python and C.
- Alternative C implementations and optimization experiments.
- Kernel benchmarking and Linux `perf` profiling.
- Experimental end-to-end 2x2 MIMO link.
- Reproducible AWGN and multipath experiments.
- Channel-estimation and receiver-performance comparisons.
- Technical specifications and experiment reports.

## Development Methodology

The project follows a correctness-first workflow:

Understand -> Specify -> Implement Python Reference -> Implement C -> Validate -> Benchmark -> Profile -> Optimize -> Analyze -> Document

Python reference implementations are developed first to establish expected behavior. C implementations are then developed and validated against the reference where applicable. Performance is evaluated after correctness has been established.

## Implemented PHY Kernels

| Kernel | Functionality | Implementation |
|---|---|---|
| 1. CRC24A | CRC generation and verification | Python and C |
| 2. Scrambling | NR pseudorandom sequence generation and bit scrambling/descrambling | Python and C variants |
| 3. QAM | QPSK, 16-QAM, 64-QAM, and 256-QAM mapping/demapping | Python and C |
| 4. OFDM | IFFT, FFT, subcarrier mapping/extraction, and cyclic-prefix processing | Python and C |
| 5. Channel Estimation | LS channel estimation and linear interpolation | Python and C |
| 6. MIMO Detection | 2x2 MIMO Zero-Forcing detection | Python and C |

### Kernel Details

**Kernel 1 — CRC24A**

Implements CRC24A generation and verification based on 3GPP TS 38.212, Clause 5.1. Includes alternative C implementations, validation, benchmarking, and profiling.

**Kernel 2 — Scrambling and Descrambling**

Implements NR pseudorandom sequence generation and XOR-based scrambling/descrambling, based on 3GPP TS 38.211. Includes alternative C implementations and sequence-validation and performance experiments.

**Kernel 3 — QAM Mapping and Demapping**

Implements mapping and demapping for QPSK, 16-QAM, 64-QAM, and 256-QAM, with deterministic and round-trip validation.

**Kernel 4 — OFDM Processing**

Implements transmitter IFFT, receiver FFT, subcarrier mapping and extraction, and cyclic-prefix insertion and removal.

**Kernel 5 — LS Channel Estimation**

Implements least-squares channel estimation using known pilot/reference observations and linear interpolation.

**Kernel 6 — 2x2 MIMO Zero-Forcing Detection**

Implements a 2x2 MIMO ZF detector with input validation and numerical-status handling, including singular and near-singular channel cases.

## Integrated 2x2 MIMO PHY Chain

The standalone kernels are connected through an experimental transmitter-channel-receiver simulation.

**Transmitter:** Payload bits -> CRC attachment -> scrambling -> QAM mapping -> resource-grid construction -> OFDM IFFT -> cyclic-prefix insertion.

**Channel:** AWGN, configured multipath profiles, and a 2x2 MIMO channel matrix with reproducible noise and channel experiments.

**Receiver:** Cyclic-prefix removal -> FFT -> resource-grid extraction -> channel estimation -> 2x2 MIMO ZF detection -> QAM demapping -> descrambling -> CRC verification -> payload comparison.

This is an experimental integration of selected PHY blocks, not a complete standardized NR modem.

## Experiments and Results

The integrated system is evaluated through reproducible experiments. Detailed configurations and measurements are available in the linked reports.

| Experiment | Evaluation | Detailed Report |
|---|---|---|
| AWGN sweep | End-to-end behavior across nine configured noise variances, with 100 trials per condition | [AWGN Report](results/integration_awgn/awgn_report.md) |
| Multipath evaluation | Flat and multipath channel behavior over 100 trials | [Multipath Report](results/integration_multipath_100trial/multipath_report.md) |
| Delay-domain channel estimation | Compares delay-domain LS estimation with LS plus linear interpolation on the tested integer-delay channel model | [Comparison Report](results/integration_multipath/delay_domain_comparison_full_20261030/delay_domain_comparison_report.md) |
| MMSE versus ZF | Compares detector performance using the same received data and exact oracle channel information | [MMSE vs ZF Report](results/integration_multipath/mmse_zf_comparison/mmse_zf_comparison_report.md) |
| Oracle-channel receiver | Uses the exact channel response as a diagnostic reference for receiver comparisons | [Oracle Comparison Report](results/integration_multipath/oracle_channel_comparison/oracle_comparison_report.md) |

### Interpretation Notes

- Experiment results apply to the tested configurations and channel models; they should not be generalized to all NR deployments.
- Delay-domain estimation results are specific to the tested integer-delay channel model.
- Oracle channel information is a diagnostic reference, not a practical channel-estimation method.
- MMSE and ZF comparisons are experimental evaluations, not claims of a production-ready receiver.

## Repository Structure

- `docs/` — Technical specifications, methodology, and experiment analysis.
- `integration/` — End-to-end simulation, channel models, and TX/RX chains.
- `kernels/` — Six standalone PHY kernel implementations.
- `profiling/` — Kernel profiling material.
- `report/` — Project reports.
- `results/` — Benchmark and experiment outputs.
- `scripts/` — Experiment and comparison runners.
- `tests/` — Kernel-level and integration tests.
- `environment.md` — Development environment details.
- `pytest.ini` — Pytest configuration.

## Development Environment

| Component | Configuration |
|---|---|
| Operating System | Ubuntu 24.04 LTS |
| Architecture | x86_64 |
| Processor | 12th Gen Intel Core i7-12700 |
| CPU Topology | 12 cores, 20 logical CPUs |
| Compiler | GCC 13.3.0 |
| Python | 3.12.3 |
| CMake | 3.28.3 |
| Git | 2.43.0 |
| Linux perf | 7.0.14 |
| NumPy | 2.5.3 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |
| Pandas | 3.0.6 |
| Pytest | 9.1.1 |

The processor supports AVX2. AVX-512 is not exposed by the current CPU configuration.

For additional environment details, see [environment.md](environment.md).

## Getting Started

Clone the repository from GitHub and enter the project directory:

`git clone https://github.com/Mannu1318/5g-nr-phy-performance.git`

`cd 5g-nr-phy-performance`

Create and activate a Python virtual environment:

`python3 -m venv .venv`

`source .venv/bin/activate`

Install the required dependencies:

`python -m pip install --upgrade pip`

`python -m pip install numpy scipy matplotlib pandas pytest`

Run the test suite:

`pytest -q`

The test suite covers standalone kernel behavior and integration-level validation.

## Running Experiments

The following scripts run the integrated experiments and receiver comparisons.

- AWGN sweep: `python scripts/run_integration_awgn.py`
- Multipath evaluation: `python scripts/run_integration_multipath.py`
- Delay-domain estimator comparison: `python scripts/compare_delay_domain_estimator.py`
- Delay-domain receiver comparison: `python scripts/compare_delay_domain_receiver.py`
- MMSE versus ZF comparison: `python scripts/compare_mmse_zf_receiver.py`
- Oracle-channel receiver comparison: `python scripts/compare_oracle_channel_receiver.py`

Use `--help` with a script to inspect its available options. Experiment outputs are written under the `results/` directory.

## Performance Engineering

The project evaluates performance after functional correctness has been established.

Performance-engineering activities include:

- Benchmarking alternative implementations of selected kernels.
- Measuring execution time, throughput, and speedup where applicable.
- Profiling using Linux `perf`.
- Investigating computational bottlenecks.
- Evaluating optimization approaches while preserving correctness.
- Comparing receiver and channel-estimation behavior under controlled experiments.

Optimization techniques and implementation variants differ between kernels. SIMD or multithreaded optimization is not claimed for every kernel.

## Scope and Limitations

This repository focuses on selected PHY algorithms and experimental integration. It does not currently implement:

- NR LDPC or Polar channel coding.
- A complete standardized NR frame and scheduling system.
- Full 3GPP TDL/CDL channel-model conformance.
- A production-ready real-time radio implementation.
- A complete NR modem or protocol stack.
- Over-the-air transmission and reception.

## Documentation

- [Project Scope](docs/scope.md)
- [Development Environment](environment.md)
- [Kernel Specifications](docs/kernel-specification.md)
- [QAM Specification](docs/kernel3-qam-specification.md)
- [OFDM Specification](docs/kernel4-ofdm-specification.md)
- [Channel Estimation Specification](docs/kernel5-channel-estimation-specification.md)
- [MIMO ZF Specification](docs/kernel6-zf-specification.md)
- [AWGN Experiment Specification](docs/integration-awgn-specification.md)
- [Multipath Experiment Specification](docs/integration-multipath-specification.md)
- [Delay-Domain Estimation Results](docs/delay-domain-channel-estimation-results.md)
- [MMSE versus ZF Results](docs/mmse-vs-zf-experiment-results.md)

## Project Outcome

This project demonstrates a structured approach to PHY algorithm development, from standalone Python reference implementations and C implementations through validation, performance analysis, and experimental end-to-end integration.

It provides a documented foundation for further work in 5G NR physical-layer algorithms, receiver design, numerical methods, and performance engineering.
