# Kernel 2 — 5G NR Bit Scrambling Profiling

## Purpose

This directory organizes profiling documentation for the PDSCH bit-scrambling kernel.

## Existing profiling evidence

The detailed performance investigation is documented in:

- [`kernel2-performance-baseline.md`](../../docs/kernel2-performance-baseline.md)
- [`benchmark_summary.md`](../../results/kernel2_scrambling/benchmark_summary.md)

The documentation includes comparisons of scrambling implementations and recorded `perf stat` and `perf report` observations.

## Scope

The profiling results concern the specific implementations and benchmark configurations described in those reports. They should not be interpreted as measurements of a complete 5G NR PHY receiver or transmitter.

## Reproducibility

Consult the linked reports for the commands, compiler settings, and benchmark configurations. Hardware performance-counter measurements can vary with CPU activity and system configuration.
