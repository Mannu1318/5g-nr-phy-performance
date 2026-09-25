# 5G NR L1 PHY Performance Analysis
## Environment and Test Setup

### Hardware

- CPU: 12th Gen Intel(R) Core(TM) i7-12700
- Architecture: x86_64
- Physical cores: 12
- Logical CPUs / threads: 20
- CPU sockets: 1
- Maximum CPU frequency: up to 4.9 GHz
- L3 cache: 25 MiB
- NUMA nodes: 1
- CPU vendor: GenuineIntel

### CPU Instruction Set

- AVX2: Supported
- AVX-512: Not present in the reported CPU flags
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
- perf: 7.0.14
- Python: 3.12.3

### Python Analysis Libraries

- NumPy: 1.26.4
- SciPy: 1.11.4
- Matplotlib: 3.6.3
- Pandas: Installed in project virtual environment

### CPU Topology

The system contains 12 physical CPU cores and 20 logical CPUs.

Logical CPUs 0–15 correspond to the higher-frequency physical cores with two logical threads per core. Logical CPUs 16–19 correspond to four additional lower-frequency cores with one logical CPU each.

Detailed CPU affinity and P-core/E-core experiments will be performed during the multithreading optimization phase.

### Project Environment

The project uses a Python virtual environment:

`.venv/`

The virtual environment is excluded from Git tracking through `.gitignore`.

### Performance Analysis Tools

The main performance-analysis tool will be Linux `perf`.

Planned measurements include:

- CPU cycles
- Instructions
- Instructions per cycle (IPC)
- Cache references
- Cache misses
- Kernel execution time
- Cycles per bit
- Cycles per symbol
- Throughput
- Latency

### Project Scope

This project implements standalone 5G NR Layer-1 PHY kernels and evaluates their performance on the local Intel Core i7-12700 system.

The project does not require:

- Intel Xeon Scalable hardware
- AVX-512
- ACC100/FPGA hardware
- O-RAN fronthaul hardware

The optimization study will focus on:

1. Scalar baseline implementations
2. AVX2 SIMD optimization
3. Multithreading
4. CPU core placement
5. Memory and cache optimization
6. System-level performance sweeps

### Status

Phase 0 — Environment Setup: In Progress

Next step: complete project configuration and begin Phase 1 scope definition.
