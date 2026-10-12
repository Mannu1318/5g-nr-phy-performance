# Kernel 3 — QAM Mapping and Demapping Profiling

## Purpose

Documents profiling work for QPSK, 16-QAM, 64-QAM, and 256-QAM mapping and demapping.

## Benchmark Sources

Benchmark programs are maintained in `tests/kernel3_qam/`, including combined and separate mapping/demapping benchmarks, 256-QAM demapping baselines and optimizations, and packed-input experiments.

## Existing Results

See `results/kernel3_qam/benchmark_summary.md` for recorded benchmark results.

## Profiling Workflow

Compile the selected benchmark with optimization and debug symbols, then run these commands from the repository root:

```bash
perf stat ./tests/kernel3_qam/benchmark_qam
perf record -g ./tests/kernel3_qam/benchmark_qam
perf report
```

Available counters depend on CPU support, kernel configuration, permissions, and the installed `perf` version.

## Status

Benchmark sources and benchmark results exist. The commands above are instructions; they do not establish that a new profiling run has been completed. Record actual measurements and configurations before drawing profiling conclusions.
