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

static int sample_close(
    channel_sample_t actual,
    channel_sample_t expected,
    double tolerance
)
{
    return fabs(actual.real - expected.real) <= tolerance &&
           fabs(actual.imag - expected.imag) <= tolerance;
}

static void test_constant_channel(void)
{
    const channel_sample_t pilots[] = {
        {1.0, 0.0}, {1.0, 0.0}
    };
    const channel_sample_t received[] = {
        {2.0, 3.0}, {2.0, 3.0}
    };
    const size_t pilot_indices[] = {0, 4};
    const size_t requested[] = {0, 1, 2, 3, 4};
    channel_sample_t output[5];

    int status = estimate_channel(
        pilots, received, pilot_indices, 2,
        requested, 5, output
    );

    CHECK(status == 0, "constant channel: function returns success");

    for (size_t i = 0; i < 5; ++i) {
        CHECK(sample_close(output[i], (channel_sample_t){2.0, 3.0},
                           1e-12),
              "constant channel: expected complex estimate");
    }
}

static void test_linear_interpolation(void)
{
    const channel_sample_t pilots[] = {
        {1.0, 0.0}, {1.0, 0.0}
    };
    const channel_sample_t received[] = {
        {0.0, 0.0}, {4.0, 8.0}
    };
    const size_t pilot_indices[] = {2, 6};
    const size_t requested[] = {3, 4, 5};
    const channel_sample_t expected[] = {
        {1.0, 2.0}, {2.0, 4.0}, {3.0, 6.0}
    };
    channel_sample_t output[3];

    int status = estimate_channel(
        pilots, received, pilot_indices, 2,
        requested, 3, output
    );

    CHECK(status == 0, "linear interpolation: function returns success");

    for (size_t i = 0; i < 3; ++i) {
        CHECK(sample_close(output[i], expected[i], 1e-12),
              "linear interpolation: expected complex value");
    }
}

static void test_ls_at_pilots(void)
{
    const channel_sample_t pilots[] = {
        {1.0, 1.0}, {2.0, -1.0}
    };
    const channel_sample_t received[] = {
        {2.0, 0.0}, {3.0, 1.0}
    };
    const size_t pilot_indices[] = {1, 5};
    const size_t requested[] = {1, 5};
    const channel_sample_t expected[] = {
        {1.0, -1.0}, {1.0, 1.0}
    };
    channel_sample_t output[2];

    int status = estimate_channel(
        pilots, received, pilot_indices, 2,
        requested, 2, output
    );

    CHECK(status == 0, "LS pilot estimates: function returns success");

    for (size_t i = 0; i < 2; ++i) {
        CHECK(sample_close(output[i], expected[i], 1e-12),
              "LS pilot estimates: expected complex division");
    }
}

static void test_invalid_inputs(void)
{
    const channel_sample_t zero_pilot[] = {{0.0, 0.0}};
    const channel_sample_t received[] = {{1.0, 0.0}};
    const size_t pilot_indices[] = {2, 4};
    const size_t valid_request[] = {2};
    channel_sample_t output[1];

    CHECK(
        estimate_channel(
            zero_pilot, received, pilot_indices, 1,
            valid_request, 1, output
        ) == -2,
        "validation: zero pilot rejected"
    );

    const channel_sample_t pilots[] = {{1.0, 0.0}, {1.0, 0.0}};
    const channel_sample_t observations[] = {{1.0, 0.0}, {2.0, 0.0}};
    const size_t unsorted_indices[] = {4, 3};

    CHECK(
        estimate_channel(
            pilots, observations, unsorted_indices, 2,
            valid_request, 1, output
        ) == -1,
        "validation: unsorted pilot indices rejected"
    );

    const size_t out_of_range[] = {5};

    CHECK(
        estimate_channel(
            pilots, observations, pilot_indices, 2,
            out_of_range, 1, output
        ) == -1,
        "validation: out-of-range request rejected"
    );

    CHECK(
        estimate_channel(
            NULL, received, pilot_indices, 1,
            valid_request, 1, output
        ) == -1,
        "validation: null pilot pointer rejected"
    );
}

static void test_empty_requests(void)
{
    const channel_sample_t pilots[] = {{1.0, 0.0}};
    const channel_sample_t received[] = {{2.0, 1.0}};
    const size_t pilot_indices[] = {3};

    int status = estimate_channel(
        pilots, received, pilot_indices, 1,
        NULL, 0, NULL
    );

    CHECK(status == 0, "empty requests: valid pilots accepted");
}

int main(void)
{
    test_constant_channel();
    test_linear_interpolation();
    test_ls_at_pilots();
    test_invalid_inputs();
    test_empty_requests();

    printf("\nC tests: %d run, %d failed\n",
           tests_run, tests_failed);

    return tests_failed == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
