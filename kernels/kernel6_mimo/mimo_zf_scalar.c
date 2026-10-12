#include "mimo_zf_scalar.h"

#include <float.h>
#include <math.h>

/* Return a complex NaN for failed estimates. */
static double complex complex_nan(void)
{
    return NAN + NAN * I;
}

/* Set both output symbols to complex NaN when output storage exists. */
static void set_nan_estimate(double complex x_hat[2])
{
    if (x_hat != NULL) {
        x_hat[0] = complex_nan();
        x_hat[1] = complex_nan();
    }
}

/* Check that both components of a complex number are finite. */
static int complex_is_finite(double complex value)
{
    return isfinite(creal(value)) && isfinite(cimag(value));
}

/*
 * Detect one symbol pair.
 *
 * H uses row-major order:
 * [h00, h01, h10, h11]
 */
zf_status zf_detect_single(
    const double complex H[4],
    const double complex y[2],
    double complex x_hat[2])
{
    double scale = 0.0;
    double complex g00, g01, g10, g11;
    double complex determinant;
    double frobenius_squared;
    double rho;
    double complex rhs0, rhs1;
    double complex x0, x1;
    double magnitude;

    if (x_hat == NULL) {
        return ZF_INVALID_SHAPE;
    }

    set_nan_estimate(x_hat);

    if (H == NULL || y == NULL) {
        return ZF_INVALID_SHAPE;
    }

    for (size_t i = 0; i < 4; ++i) {
        if (!complex_is_finite(H[i])) {
            return ZF_NONFINITE_INPUT;
        }
    }

    if (!complex_is_finite(y[0]) || !complex_is_finite(y[1])) {
        return ZF_NONFINITE_INPUT;
    }

    /*
     * Scale by the largest complex magnitude before evaluating
     * the determinant. cabs() may return infinity if the magnitude
     * is not representable even though the components are finite.
     */
    for (size_t i = 0; i < 4; ++i) {
        magnitude = cabs(H[i]);

        if (!isfinite(magnitude)) {
            return ZF_NUMERICAL_FAILURE;
        }

        if (magnitude > scale) {
            scale = magnitude;
        }
    }

    if (scale == 0.0) {
        return ZF_SINGULAR_CHANNEL;
    }

    g00 = H[0] / scale;
    g01 = H[1] / scale;
    g10 = H[2] / scale;
    g11 = H[3] / scale;

    determinant = g00 * g11 - g01 * g10;

    /*
     * Compute squared magnitudes directly. The channel has already
     * been normalized, so these component squares cannot overflow.
     */
    frobenius_squared =
        creal(g00) * creal(g00) + cimag(g00) * cimag(g00) +
        creal(g01) * creal(g01) + cimag(g01) * cimag(g01) +
        creal(g10) * creal(g10) + cimag(g10) * cimag(g10) +
        creal(g11) * creal(g11) + cimag(g11) * cimag(g11);

    if (!complex_is_finite(determinant) ||
        !isfinite(frobenius_squared) ||
        frobenius_squared == 0.0) {
        return ZF_NUMERICAL_FAILURE;
    }

    rho = cabs(determinant) / frobenius_squared;

    if (!isfinite(rho)) {
        return ZF_NUMERICAL_FAILURE;
    }

    if (rho <= ZF_NEAR_SINGULAR_THRESHOLD) {
        return ZF_NEAR_SINGULAR_CHANNEL;
    }

    /*
     * Since H = scale * G, solve G*x_hat = y/scale.
     * Reject non-finite intermediate values rather than returning
     * a corrupted estimate.
     */
    rhs0 = y[0] / scale;
    rhs1 = y[1] / scale;

    if (!complex_is_finite(rhs0) || !complex_is_finite(rhs1)) {
        return ZF_NUMERICAL_FAILURE;
    }

    x0 = (g11 * rhs0 - g01 * rhs1) / determinant;
    x1 = (g00 * rhs1 - g10 * rhs0) / determinant;

    if (!complex_is_finite(x0) || !complex_is_finite(x1)) {
        return ZF_NUMERICAL_FAILURE;
    }

    x_hat[0] = x0;
    x_hat[1] = x1;

    return ZF_OK;
}

/*
 * Process independent symbol pairs.
 *
 * The return value describes batch-level validity. Individual
 * detection outcomes are stored in statuses[i].
 */
zf_status zf_detect_batch(
    const double complex *H,
    const double complex *y,
    double complex *x_hat,
    zf_status *statuses,
    size_t count)
{
    if (count == 0) {
        return ZF_OK;
    }

    if (H == NULL || y == NULL || x_hat == NULL || statuses == NULL) {
        if (statuses != NULL) {
            for (size_t i = 0; i < count; ++i) {
                statuses[i] = ZF_INVALID_SHAPE;
            }
        }

        if (x_hat != NULL) {
            for (size_t i = 0; i < count; ++i) {
                x_hat[2 * i] = complex_nan();
                x_hat[2 * i + 1] = complex_nan();
            }
        }

        return ZF_INVALID_SHAPE;
    }

    for (size_t i = 0; i < count; ++i) {
        statuses[i] = zf_detect_single(
            &H[4 * i],
            &y[2 * i],
            &x_hat[2 * i]);
    }

    return ZF_OK;
}
