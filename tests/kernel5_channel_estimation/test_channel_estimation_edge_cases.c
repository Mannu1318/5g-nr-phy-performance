#include "channel_estimation.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static int tests_run = 0;
static int tests_failed = 0;

#define CHECK(condition, message)                                  \
    do {                                                           \
        ++tests_run;                                               \
        if (!(condition)) {                                        \
            ++tests_failed;                                        \
            fprintf(stderr, "FAIL: %s (line %d)\n",                \
                    message, __LINE__);                            \
        } else {                                                   \
            printf("PASS: %s\n", message);                         \
        }                                                          \
    } while (0)

static void test_non_finite_inputs(void)
{
    const channel_sample_t received[] = {{1.0, 0.0}};
    const size_t indices[] = {2};
    channel_sample_t output[1];

    const channel_sample_t nan_pilot[] = {{NAN, 0.0}};
    CHECK(
        estimate_channel(nan_pilot, received, indices, 1,
                         indices, 1, output) == -2,
        "NaN pilot rejected"
    );

    const channel_sample_t infinite_received[] = {{INFINITY, 0.0}};
    const channel_sample_t valid_pilot[] = {{1.0, 0.0}};
    CHECK(
        estimate_channel(valid_pilot, infinite_received, indices, 1,
                         indices, 1, output) == -2,
        "infinite received sample rejected"
    );
}

static void test_duplicate_pilot_indices(void)
{
    const channel_sample_t pilots[] = {
        {1.0, 0.0}, {1.0, 0.0}
    };
    const channel_sample_t received[] = {
        {1.0, 0.0}, {2.0, 0.0}
    };
    const size_t duplicate_indices[] = {4, 4};
    const size_t requested[] = {4};
    channel_sample_t output[1];

    CHECK(
        estimate_channel(pilots, received, duplicate_indices, 2,
                         requested, 1, output) == -1,
        "duplicate pilot indices rejected"
    );
}

static void test_single_pilot_restriction(void)
{
    const channel_sample_t pilots[] = {{1.0, 0.0}};
    const channel_sample_t received[] = {{2.0, -1.0}};
    const size_t pilot_indices[] = {3};
    const size_t other_index[] = {4};
    channel_sample_t output[1];

    CHECK(
        estimate_channel(pilots, received, pilot_indices, 1,
                         other_index, 1, output) == -1,
        "single pilot cannot estimate another subcarrier"
    );
}

static void test_missing_output_pointers(void)
{
    const channel_sample_t pilots[] = {{1.0, 0.0}};
    const channel_sample_t received[] = {{2.0, 0.0}};
    const size_t indices[] = {2};
    channel_sample_t output[1];

    CHECK(
        estimate_channel(pilots, received, indices, 1,
                         indices, 1, NULL) == -1,
        "missing output buffer rejected"
    );

    CHECK(
        estimate_channel(pilots, received, indices, 1,
                         NULL, 1, output)
            == -1,
        "missing requested-index pointer rejected"
    );
}


static void test_extreme_finite_values(void)
{
    const size_t indices[] = {2};
    channel_sample_t output[1];

    const channel_sample_t large_pilot[] = {{1e200, 0.0}};
    const channel_sample_t large_received[] = {{1e200, 0.0}};

    int status = estimate_channel(
        large_pilot, large_received, indices, 1,
        indices, 1, output
    );

    CHECK(status == 0, "large finite values accepted");
    CHECK(
        status == 0 && isfinite(output[0].real) &&
        isfinite(output[0].imag) &&
        fabs(output[0].real - 1.0) < 1e-12 &&
        fabs(output[0].imag) < 1e-12,
        "large finite values produce a finite unit estimate"
    );

    const channel_sample_t small_pilot[] = {{1e-200, 0.0}};
    const channel_sample_t small_received[] = {{1e-200, 0.0}};

    status = estimate_channel(
        small_pilot, small_received, indices, 1,
        indices, 1, output
    );

    CHECK(status == 0, "small finite values accepted");
    CHECK(
        status == 0 && isfinite(output[0].real) &&
        isfinite(output[0].imag) &&
        fabs(output[0].real - 1.0) < 1e-12 &&
        fabs(output[0].imag) < 1e-12,
        "small finite values produce a finite unit estimate"
    );
}

int main(void)
{
    test_non_finite_inputs();
    test_duplicate_pilot_indices();
    test_single_pilot_restriction();
    test_missing_output_pointers();
    test_extreme_finite_values();

    printf("\nEdge-case C tests: %d run, %d failed\n",
           tests_run, tests_failed);

    return tests_failed == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
