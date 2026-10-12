#include "channel_estimation.h"

#include <math.h>
#include <stdint.h>

/* Check that both components of a complex sample are finite. */
static int sample_is_finite(channel_sample_t value)
{
    return isfinite(value.real) && isfinite(value.imag);
}

/*
 * Divide two complex numbers:
 *
 * (a + jb) / (c + jd)
 *   = ((ac + bd) + j(bc - ad)) / (c*c + d*d)
 */
static channel_sample_t complex_divide(
    channel_sample_t numerator,
    channel_sample_t denominator
)
{
    /*
     * Use scaled complex division to avoid directly calculating
     * c*c + d*d, which can overflow or underflow.
     *
     * The caller validates that the denominator is finite and nonzero.
     */
    channel_sample_t result;

    if (fabs(denominator.real) >= fabs(denominator.imag)) {
        double ratio = denominator.imag / denominator.real;
        double scaled_denominator =
            denominator.real + denominator.imag * ratio;

        result.real =
            (numerator.real + numerator.imag * ratio) /
            scaled_denominator;

        result.imag =
            (numerator.imag - numerator.real * ratio) /
            scaled_denominator;
    } else {
        double ratio = denominator.real / denominator.imag;
        double scaled_denominator =
            denominator.imag + denominator.real * ratio;

        result.real =
            (numerator.real * ratio + numerator.imag) /
            scaled_denominator;

        result.imag =
            (numerator.imag * ratio - numerator.real) /
            scaled_denominator;
    }

    return result;
}

/*
 * Estimate the channel at requested subcarrier indices.
 *
 * The LS estimate at pilot k is:
 *     H_hat[k] = Y[k] / X_p[k]
 *
 * Between adjacent pilots, linear interpolation is used independently
 * for the real and imaginary components.
 */
int estimate_channel(
    const channel_sample_t *pilot_symbols,
    const channel_sample_t *received_pilots,
    const size_t *pilot_indices,
    size_t n_pilots,
    const size_t *estimate_indices,
    size_t n_estimates,
    channel_sample_t *estimates
)
{
    if (pilot_symbols == NULL || received_pilots == NULL ||
        pilot_indices == NULL || n_pilots == 0 ||
        (n_estimates > 0 &&
         (estimate_indices == NULL || estimates == NULL))) {
        return -1;
    }

    /* Validate all pilot inputs before producing any estimates. */
    for (size_t i = 0; i < n_pilots; ++i) {
        if (!sample_is_finite(pilot_symbols[i]) ||
            !sample_is_finite(received_pilots[i])) {
            return -2;
        }

        if (pilot_symbols[i].real == 0.0 &&
            pilot_symbols[i].imag == 0.0) {
            return -2;
        }

        if (i > 0 && pilot_indices[i] <= pilot_indices[i - 1]) {
            return -1;
        }
    }

    /* Validate requests, including the single-pilot restriction. */
    for (size_t i = 0; i < n_estimates; ++i) {
        size_t k = estimate_indices[i];

        if (n_pilots == 1 && k != pilot_indices[0]) {
            return -1;
        }

        if (k < pilot_indices[0] || k > pilot_indices[n_pilots - 1]) {
            return -1;
        }
    }

    /* Empty requests are valid once the pilot inputs have been checked. */
    if (n_estimates == 0) {
        return 0;
    }

    /*
     * Locate the interpolation interval with binary search, calculate
     * the required LS pilot estimates, and interpolate each request.
     * Requested subcarrier indices may appear in any order.
     */
    for (size_t i = 0; i < n_estimates; ++i) {
        size_t k = estimate_indices[i];

        /*
         * Find the first pilot index greater than k.
         * The preceding pilot is the left endpoint. This binary search
         * supports requested subcarrier indices in arbitrary order.
         */
        size_t low = 0;
        size_t high = n_pilots;

        while (low < high) {
            size_t mid = low + (high - low) / 2;

            if (pilot_indices[mid] <= k) {
                low = mid + 1;
            } else {
                high = mid;
            }
        }

        size_t left = low - 1;

        channel_sample_t left_estimate =
            complex_divide(received_pilots[left], pilot_symbols[left]);

        /* Exact pilot match, or the only available pilot. */
        if (pilot_indices[left] == k || n_pilots == 1) {
            estimates[i] = left_estimate;
            continue;
        }

        size_t right = left + 1;
        channel_sample_t right_estimate =
            complex_divide(received_pilots[right], pilot_symbols[right]);

        double alpha =
            (double)(k - pilot_indices[left]) /
            (double)(pilot_indices[right] - pilot_indices[left]);

        estimates[i].real =
            (1.0 - alpha) * left_estimate.real +
            alpha * right_estimate.real;

        estimates[i].imag =
            (1.0 - alpha) * left_estimate.imag +
            alpha * right_estimate.imag;
    }

    return 0;
}
