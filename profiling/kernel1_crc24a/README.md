# Kernel 1 — CRC24A Profiling

## Purpose

This directory organizes profiling documentation for the CRC24A kernel.

## Existing profiling evidence

The main performance and profiling analysis is documented in:

- [`crc24a_scalar_baseline.md`](../../results/kernel1_crc24a/crc24a_scalar_baseline.md)

That report includes benchmark measurements, hardware performance-counter observations, instruction analysis, and optimization investigations.

## Scope

The CRC24A kernel is evaluated as an individual computational component. The report should be consulted for the exact configurations, measurements, and limitations of each experiment.

## Reproducibility

Use the commands and compiler settings documented in the report when reproducing measurements. Hardware performance-counter results can vary with CPU activity, compiler settings, and available PMU events.
