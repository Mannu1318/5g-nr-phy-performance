#include "mimo_zf_scalar.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define TOL 1e-10

static int close_complex(double complex actual, double complex expected)
{
    return cabs(actual - expected) <= TOL;
}

static int check_estimate(
    const double complex actual[2],
    const double complex expected[2])
{
    return close_complex(actual[0], expected[0]) &&
           close_complex(actual[1], expected[1]);
}

static int check_nan_estimate(const double complex estimate[2])
{
    return isnan(creal(estimate[0])) &&
           isnan(cimag(estimate[0])) &&
           isnan(creal(estimate[1])) &&
           isnan(cimag(estimate[1]));
}

static int test_identity_channel(void)
{
    const double complex H[4] = {
        1.0, 0.0,
        0.0, 1.0
    };
    const double complex y[2] = {
        1.5 + 0.5 * I,
        -0.25 + 2.0 * I
    };
    const double complex expected[2] = {
        1.5 + 0.5 * I,
        -0.25 + 2.0 * I
    };
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_OK || !check_estimate(estimate, expected)) {
        fprintf(stderr, "FAIL: identity channel\n");
        return 0;
    }

    printf("PASS: identity channel\n");
    return 1;
}

static int test_diagonal_channel(void)
{
    const double complex H[4] = {
        2.0, 0.0,
        0.0, 0.5
    };
    const double complex expected[2] = {
        1.0 + 0.5 * I,
        -2.0 + 1.0 * I
    };
    const double complex y[2] = {
        2.0 + 1.0 * I,
        -1.0 + 0.5 * I
    };
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_OK || !check_estimate(estimate, expected)) {
        fprintf(stderr, "FAIL: diagonal channel\n");
        return 0;
    }

    printf("PASS: diagonal channel\n");
    return 1;
}

static int test_complex_nondiagonal_channel(void)
{
    const double complex H[4] = {
        1.0 + I,  0.5 - 0.25 * I,
        0.25 + 0.5 * I, 1.5 - I
    };
    const double complex expected[2] = {
        0.75 - 0.5 * I,
        -1.0 + 0.25 * I
    };
    const double complex y[2] = {
        H[0] * expected[0] + H[1] * expected[1],
        H[2] * expected[0] + H[3] * expected[1]
    };
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_OK || !check_estimate(estimate, expected)) {
        fprintf(stderr, "FAIL: complex non-diagonal channel\n");
        return 0;
    }

    printf("PASS: complex non-diagonal channel\n");
    return 1;
}

static int test_zero_channel(void)
{
    const double complex H[4] = {0.0, 0.0, 0.0, 0.0};
    const double complex y[2] = {1.0, 2.0};
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_SINGULAR_CHANNEL || !check_nan_estimate(estimate)) {
        fprintf(stderr, "FAIL: zero channel handling\n");
        return 0;
    }

    printf("PASS: zero channel handling\n");
    return 1;
}

static int test_near_singular_channel(void)
{
    const double complex H[4] = {
        1.0, 1.0,
        1.0, 1.0 + 1e-14
    };
    const double complex y[2] = {1.0, 2.0};
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_NEAR_SINGULAR_CHANNEL ||
        !check_nan_estimate(estimate)) {
        fprintf(stderr, "FAIL: near-singular channel handling\n");
        return 0;
    }

    printf("PASS: near-singular channel handling\n");
    return 1;
}

static int test_nonfinite_input(void)
{
    const double complex H[4] = {
        1.0, 0.0,
        0.0, 1.0
    };
    const double complex y[2] = {NAN, 1.0};
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_NONFINITE_INPUT || !check_nan_estimate(estimate)) {
        fprintf(stderr, "FAIL: non-finite input handling\n");
        return 0;
    }

    printf("PASS: non-finite input handling\n");
    return 1;
}

static int test_batch_processing(void)
{
    const double complex H[8] = {
        1.0, 0.0,
        0.0, 1.0,

        1.0, 1.0,
        1.0, 1.0
    };
    const double complex y[4] = {
        0.5 + I, -1.0 + 0.25 * I,
        1.0, 2.0
    };
    const double complex expected_first[2] = {
        0.5 + I, -1.0 + 0.25 * I
    };
    double complex estimates[4];
    zf_status statuses[2];

    zf_status batch_status = zf_detect_batch(
        H, y, estimates, statuses, 2);

    if (batch_status != ZF_OK ||
        statuses[0] != ZF_OK ||
        statuses[1] != ZF_NEAR_SINGULAR_CHANNEL ||
        !check_estimate(&estimates[0], expected_first) ||
        !check_nan_estimate(&estimates[2])) {
        fprintf(stderr, "FAIL: batch processing\n");
        return 0;
    }

    printf("PASS: batch processing\n");
    return 1;
}

static int test_small_channel_scaling(void)
{
    const double complex H[4] = {
        1e-100, 0.0,
        0.0, 1e-100
    };
    const double complex expected[2] = {
        0.75 + 0.5 * I,
        -1.0 + 0.25 * I
    };
    const double complex y[2] = {
        1e-100 * expected[0],
        1e-100 * expected[1]
    };
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_OK || !check_estimate(estimate, expected)) {
        fprintf(stderr, "FAIL: small channel scaling\n");
        return 0;
    }

    printf("PASS: small channel scaling\n");
    return 1;
}

static int test_large_channel_scaling(void)
{
    const double complex H[4] = {
        1e100, 0.0,
        0.0, 1e100
    };
    const double complex expected[2] = {
        0.75 + 0.5 * I,
        -1.0 + 0.25 * I
    };
    const double complex y[2] = {
        1e100 * expected[0],
        1e100 * expected[1]
    };
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_OK || !check_estimate(estimate, expected)) {
        fprintf(stderr, "FAIL: large channel scaling\n");
        return 0;
    }

    printf("PASS: large channel scaling\n");
    return 1;
}

static int test_null_pointer_handling(void)
{
    const double complex H[4] = {1.0, 0.0, 0.0, 1.0};
    const double complex y[2] = {1.0, 2.0};
    double complex estimate[2];

    if (zf_detect_single(NULL, y, estimate) != ZF_INVALID_SHAPE) {
        fprintf(stderr, "FAIL: null channel pointer handling\n");
        return 0;
    }

    if (zf_detect_single(H, NULL, estimate) != ZF_INVALID_SHAPE) {
        fprintf(stderr, "FAIL: null received-vector pointer handling\n");
        return 0;
    }

    if (zf_detect_single(H, y, NULL) != ZF_INVALID_SHAPE) {
        fprintf(stderr, "FAIL: null output pointer handling\n");
        return 0;
    }

    printf("PASS: null pointer handling\n");
    return 1;
}


static int test_unrepresentable_complex_magnitude(void)
{
    const double complex H[4] = {
        1.7e308 + 1.7e308 * I, 0.0,
        0.0, 1.0
    };
    const double complex y[2] = {1.0, 2.0};
    double complex estimate[2];

    zf_status status = zf_detect_single(H, y, estimate);

    if (status != ZF_NUMERICAL_FAILURE ||
        !check_nan_estimate(estimate)) {
        fprintf(stderr, "FAIL: unrepresentable complex magnitude\n");
        return 0;
    }

    printf("PASS: unrepresentable complex magnitude\n");
    return 1;
}

static int test_batch_null_pointer_handling(void)
{
    const double complex y[2] = {1.0, 2.0};
    double complex estimate[2];
    zf_status status;

    status = zf_detect_batch(NULL, y, estimate, &status, 1);

    if (status != ZF_INVALID_SHAPE ||
        !check_nan_estimate(estimate)) {
        fprintf(stderr, "FAIL: batch null pointer handling\n");
        return 0;
    }

    printf("PASS: batch null pointer handling\n");
    return 1;
}

static int test_empty_batch(void)
{
    zf_status status = zf_detect_batch(NULL, NULL, NULL, NULL, 0);

    if (status != ZF_OK) {
        fprintf(stderr, "FAIL: empty batch handling\n");
        return 0;
    }

    printf("PASS: empty batch handling\n");
    return 1;
}

int main(void)
{
    int passed = 0;
    int total = 13;

    passed += test_identity_channel();
    passed += test_diagonal_channel();
    passed += test_complex_nondiagonal_channel();
    passed += test_zero_channel();
    passed += test_near_singular_channel();
    passed += test_nonfinite_input();
    passed += test_batch_processing();
    passed += test_small_channel_scaling();
    passed += test_large_channel_scaling();
    passed += test_null_pointer_handling();
    passed += test_unrepresentable_complex_magnitude();
    passed += test_batch_null_pointer_handling();
    passed += test_empty_batch();

    printf("\nC ZF tests: %d/%d passed\n", passed, total);

    return (passed == total) ? EXIT_SUCCESS : EXIT_FAILURE;
}
