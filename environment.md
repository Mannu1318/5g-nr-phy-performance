# 5G NR PHY Performance Engineering
## Environment and Test Setup

### Hardware

- CPU: 12th Gen Intel Core i7-12700
- Architecture: x86_64
- Physical cores: 12 (8 P-cores and 4 E-cores)
- Logical CPUs: 20
- CPU sockets: 1
- Maximum reported frequency: 4.9 GHz
- L1 data cache: 512 KiB (12 instances)
- L1 instruction cache: 512 KiB (12 instances)
- L2 cache: 12 MiB
- L3 cache: 25 MiB
- NUMA nodes: 1

### CPU Instruction Set

- AVX2: Supported
- AVX-512: Not exposed by the current CPU configuration
- FMA: Supported
- SSE4.1/SSE4.2: Supported
- AES: Supported
- BMI2: Supported

### Operating System

- OS: Ubuntu 24.04 LTS
- Architecture: x86_64

### Development Tools

- GCC: 13.3.0
- CMake: 3.28.3
- Git: 2.43.0
- Linux perf: 7.0.14
- Python: 3.12.3
- pytest: 9.1.1

### Python Analysis Libraries

- NumPy: 2.5.3
- SciPy: 1.18.1
- Matplotlib: 3.11.2
- Pandas: 3.0.6

These versions were checked in the active project virtual environment during documentation finalization.

### CPU Topology Notes

The processor exposes 12 physical cores and 20 logical CPUs. The system has a hybrid CPU architecture.

The aggregate topology and cache information above were obtained using `lscpu`. No fixed logical-CPU-to-core-type mapping is claimed in this document.

### Project Environment

The project uses a Python virtual environment:

`.venv/`

The virtual environment is excluded from Git tracking through `.gitignore`.

Activate it from the repository root using:

`source .venv/bin/activate`

### Performance Analysis Tools

Linux `perf` is used for performance profiling and hardware-counter analysis where applicable.

Measurements and analysis across the project include:
- Execution time and throughput.
- CPU cycles and instruction counts.
- Instructions per cycle (IPC).
- Cache references and cache misses where measured.
- Kernel-specific performance metrics such as cycles per bit or cycles per symbol where applicable.

The availability and interpretation of hardware-counter measurements depend on the processor, kernel permissions, and profiling configuration.

### Project Scope

The repository implements six selected 5G NR PHY processing kernels and an experimental 2×2 MIMO transmitter–channel–receiver chain.

The work includes:
1. Python reference implementations.
2. C implementations and cross-validation where applicable.
3. Unit and integration testing.
4. Kernel benchmarking and profiling.
5. AWGN and multipath experiments.
6. Channel-estimation and receiver-comparison studies.
7. Technical specifications and experiment reports.

The implementation is educational and experimental. It is not a complete or fully 3GPP-compliant NR modem.

### Project Status

- Six standalone PHY kernels: implemented.
- Python reference and C implementations: completed where applicable.
- Kernel validation and Python/C cross-validation: completed where applicable.
- Integrated experimental 2×2 MIMO link: implemented.
- AWGN and multipath experiments: completed.
- Delay-domain channel-estimation comparison: completed.
- MMSE versus ZF comparison: completed.
- Oracle-channel receiver comparison: completed.
- Technical documentation and experiment reports: available in `docs/` and `results/`.
- Final repository review and regression testing: in progress.

### Reproducibility Notes

Experiment scripts, configurations, random seeds, CSV outputs, and reports are maintained in the repository where applicable.

For the latest test status, run `pytest -q` from the repository root with the project virtual environment activated.

Exact performance results are specific to the documented hardware, software versions, compiler settings, input configurations, and experiment trial counts.
