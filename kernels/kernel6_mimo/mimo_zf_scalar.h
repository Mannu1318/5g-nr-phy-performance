#ifndef MIMO_ZF_SCALAR_H
#define MIMO_ZF_SCALAR_H

#include <complex.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ZF_NEAR_SINGULAR_THRESHOLD 1e-12

typedef enum {
    ZF_OK = 0,
    ZF_INVALID_SHAPE,
    ZF_NONFINITE_INPUT,
    ZF_SINGULAR_CHANNEL,
    ZF_NEAR_SINGULAR_CHANNEL,
    ZF_NUMERICAL_FAILURE
} zf_status;

/*
 * Detect one pair of transmitted complex symbols using a 2x2
 * Zero-Forcing detector.
 *
 * H: row-major channel matrix [h00, h01, h10, h11]
 * y: received vector [y0, y1]
 * x_hat: output estimate [x0, x1]
 *
 * Returns a status code. On failure, x_hat contains complex NaNs
 * whenever its pointer is valid.
 */
zf_status zf_detect_single(
    const double complex H[4],
    const double complex y[2],
    double complex x_hat[2]
);

/*
 * Detect multiple independent symbol pairs.
 *
 * H: N contiguous row-major 2x2 channel matrices (4*N values)
 * y: N received vectors (2*N values)
 * x_hat: N output estimates (2*N values)
 * statuses: N output status codes
 *
 * Returns a batch-level status. Per-pair failures are reported in
 * statuses[i], while valid pairs can still succeed.
 */
zf_status zf_detect_batch(
    const double complex *H,
    const double complex *y,
    double complex *x_hat,
    zf_status *statuses,
    size_t count
);

#ifdef __cplusplus
}
#endif

#endif
