#define _POSIX_C_SOURCE 200809L

#include "channel_estimation.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define NUM_CASES 6
#define WARMUP_ITERATIONS 50
#define BENCHMARK_ITERATIONS 500
#define NUM_SAMPLES 7

typedef struct {
    size_t subcarriers;
    size_t pilots;
} benchmark_case_t;

static const benchmark_case_t cases[NUM_CASES] = {
    {64, 4},
    {256, 4},
    {256, 16},
    {1024, 16},
    {1024, 64},
    {2048, 64}
};

static volatile double result_sink = 0.0;

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end
)
{
    return (double)(end->tv_sec - start->tv_sec)
         + (double)(end->tv_nsec - start->tv_nsec) / 1.0e9;
}

static void sort_samples(double values[NUM_SAMPLES])
{
    for (size_t i = 1; i < NUM_SAMPLES; ++i) {
        double current = values[i];
        size_t j = i;

        while (j > 0 && values[j - 1] > current) {
            values[j] = values[j - 1];
            --j;
        }

        values[j] = current;
    }
}

static int benchmark_case(
    size_t n_subcarriers,
    size_t n_pilots,
    double *median_ns,
    double *minimum_ns
)
{
    channel_sample_t *pilot_symbols =
        calloc(n_pilots, sizeof(*pilot_symbols));
    channel_sample_t *received_pilots =
        calloc(n_pilots, sizeof(*received_pilots));
    size_t *pilot_indices = calloc(n_pilots, sizeof(*pilot_indices));
    size_t *estimate_indices =
        calloc(n_subcarriers, sizeof(*estimate_indices));
    channel_sample_t *estimates =
        calloc(n_subcarriers, sizeof(*estimates));

    if (pilot_symbols == NULL || received_pilots == NULL ||
        pilot_indices == NULL || estimate_indices == NULL ||
        estimates == NULL) {
        free(pilot_symbols);
        free(received_pilots);
        free(pilot_indices);
        free(estimate_indices);
        free(estimates);
        return -1;
    }

    /* Prepare all inputs before timing the estimator. */
    for (size_t i = 0; i < n_pilots; ++i) {
        pilot_symbols[i].real = 1.0;
        pilot_symbols[i].imag = 0.0;

        received_pilots[i].real =
            0.75 + 0.001 * (double)i;
        received_pilots[i].imag =
            -0.25 + 0.0005 * (double)i;

        pilot_indices[i] =
            i * (n_subcarriers - 1) / (n_pilots - 1);
    }

    for (size_t i = 0; i < n_subcarriers; ++i) {
        estimate_indices[i] = i;
    }

    for (size_t i = 0; i < WARMUP_ITERATIONS; ++i) {
        if (estimate_channel(
                pilot_symbols, received_pilots, pilot_indices,
                n_pilots, estimate_indices, n_subcarriers,
                estimates) != 0) {
            goto failure;
        }
    }

    double samples[NUM_SAMPLES];

    for (size_t sample = 0; sample < NUM_SAMPLES; ++sample) {
        struct timespec start;
        struct timespec end;

        if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
            goto failure;
        }

        for (size_t iteration = 0;
             iteration < BENCHMARK_ITERATIONS;
             ++iteration) {
            if (estimate_channel(
                    pilot_symbols, received_pilots, pilot_indices,
                    n_pilots, estimate_indices, n_subcarriers,
                    estimates) != 0) {
                goto failure;
            }
        }

        if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
            goto failure;
        }

        samples[sample] =
            elapsed_seconds(&start, &end) * 1.0e9
            / (double)BENCHMARK_ITERATIONS;

        /*
         * Consume every output outside the timed region.
         * The volatile sink prevents the checksum from being discarded.
         */
        double checksum = 0.0;
        for (size_t i = 0; i < n_subcarriers; ++i) {
            checksum += estimates[i].real;
            checksum += estimates[i].imag;
        }
        result_sink += checksum;
    }

    sort_samples(samples);
    *minimum_ns = samples[0];
    *median_ns = samples[NUM_SAMPLES / 2];

    free(pilot_symbols);
    free(received_pilots);
    free(pilot_indices);
    free(estimate_indices);
    free(estimates);
    return 0;

failure:
    free(pilot_symbols);
    free(received_pilots);
    free(pilot_indices);
    free(estimate_indices);
    free(estimates);
    return -1;
}

int main(void)
{
    printf("Kernel 5: Channel estimation benchmark\n");
    printf("Compiler optimization: -O2\n");
    printf("Warm-up calls per case: %d\n", WARMUP_ITERATIONS);
    printf("Calls per sample: %d\n", BENCHMARK_ITERATIONS);
    printf("Independent samples per case: %d\n\n", NUM_SAMPLES);

    printf("%-14s %-10s %16s %16s\n",
           "Subcarriers", "Pilots", "Median (ns)", "Minimum (ns)");
    printf("------------------------------------------------------------\n");

    for (size_t i = 0; i < NUM_CASES; ++i) {
        double median_ns;
        double minimum_ns;

        if (benchmark_case(
                cases[i].subcarriers, cases[i].pilots,
                &median_ns, &minimum_ns) != 0) {
            fprintf(stderr,
                    "Benchmark failed for N=%zu, pilots=%zu\n",
                    cases[i].subcarriers, cases[i].pilots);
            return EXIT_FAILURE;
        }

        printf("%-14zu %-10zu %16.2f %16.2f\n",
               cases[i].subcarriers,
               cases[i].pilots,
               median_ns,
               minimum_ns);
    }

    printf("\nResult sink: %.12e\n", result_sink);
    printf("Benchmark completed successfully.\n");
    return EXIT_SUCCESS;
}
