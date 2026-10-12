#ifndef CHANNEL_ESTIMATION_H
#define CHANNEL_ESTIMATION_H

#include <stddef.h>

/*
 * Complex-valued sample represented by separate real and imaginary parts.
 */
typedef struct {
    double real;
    double imag;
} channel_sample_t;

/*
 * Estimate a frequency-domain channel using LS pilot estimates and
 * linear interpolation between pilot subcarriers.
 *
 * Inputs:
 *   pilot_symbols    Known, nonzero transmitted pilot symbols.
 *   received_pilots  Received observations at pilot positions.
 *   pilot_indices    Strictly increasing, nonnegative subcarrier indices.
 *   n_pilots         Number of pilot entries.
 *   estimate_indices Requested subcarrier indices, in output order.
 *   n_estimates      Number of requested estimates.
 *
 * Output:
 *   estimates        Caller-allocated array with space for n_estimates
 *                    channel_sample_t values.
 *
 * Requirements:
 *   - Pilot arrays must have n_pilots entries.
 *   - Pilot indices must be strictly increasing.
 *   - Requested indices must lie within the pilot range.
 *   - A single pilot supports estimates only at that pilot index.
 *   - Empty estimate requests are permitted after pilot inputs are validated.
 *
 * Returns:
 *    0  Success.
 *   -1  Invalid pointers, lengths, or indices.
 *   -2  Invalid numeric input (non-finite values or zero pilot).
 *
 * The function does not allocate memory. Input and output arrays must not
 * overlap in a way that causes input values to be overwritten.
 */
int estimate_channel(
    const channel_sample_t *pilot_symbols,
    const channel_sample_t *received_pilots,
    const size_t *pilot_indices,
    size_t n_pilots,
    const size_t *estimate_indices,
    size_t n_estimates,
    channel_sample_t *estimates
);

#endif
