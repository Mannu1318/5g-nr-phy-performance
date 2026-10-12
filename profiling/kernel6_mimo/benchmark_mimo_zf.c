#define _POSIX_C_SOURCE 200809L

#include "mimo_zf_scalar.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define NUM_BATCH_SIZES 5
#define TARGET_PAIRS 1000000U
#define MIN_ITERATIONS 10U

static const size_t batch_sizes[NUM_BATCH_SIZES] = {
    1U, 16U, 256U, 4096U, 65536U
};

static double elapsed_seconds(struct timespec start,
                              struct timespec end)
{
    return (double)(end.tv_sec - start.tv_sec)
         + (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}

static int allocate_buffers(
    size_t count,
    double complex **H,
    double complex **y,
    double complex **x_hat,
    zf_status **statuses)
{
    *H = malloc(count * 4U * sizeof(**H));
    *y = malloc(count * 2U * sizeof(**y));
    *x_hat = malloc(count * 2U * sizeof(**x_hat));
    *statuses = malloc(count * sizeof(**statuses));

    if (*H == NULL || *y == NULL ||
        *x_hat == NULL || *statuses == NULL) {
        free(*H);
        free(*y);
        free(*x_hat);
        free(*statuses);
        return 0;
    }

    return 1;
}

static void initialize_inputs(size_t count,
                              double complex *H,
                              double complex *y)
{
    for (size_t i = 0; i < count; ++i) {
        /* A fixed, well-conditioned complex 2x2 channel. */
        H[4U * i]      = 1.0 + 0.1 * I;
        H[4U * i + 1U] = 0.2 - 0.1 * I;
        H[4U * i + 2U] = 0.1 + 0.05 * I;
        H[4U * i + 3U] = 0.9 - 0.1 * I;

        y[2U * i]      = 0.75 + 0.5 * I;
        y[2U * i + 1U] = -1.0 + 0.25 * I;
    }
}

int main(void)
{
    puts("Kernel 6: 2x2 MIMO Zero-Forcing C benchmark");
    puts("Compiler optimization: build with -O2");
    puts("Clock: CLOCK_MONOTONIC");
    puts("");
    puts("Batch size,Iterations,Total pairs,Elapsed (s),"
         "ns/pair,pairs/s");

    for (size_t b = 0; b < NUM_BATCH_SIZES; ++b) {
        const size_t count = batch_sizes[b];
        size_t iterations = TARGET_PAIRS / count;

        if (iterations < MIN_ITERATIONS) {
            iterations = MIN_ITERATIONS;
        }

        double complex *H = NULL;
        double complex *y = NULL;
        double complex *x_hat = NULL;
        zf_status *statuses = NULL;

        if (!allocate_buffers(count, &H, &y, &x_hat, &statuses)) {
            fprintf(stderr, "Allocation failed for batch size %zu\n",
                    count);
            return EXIT_FAILURE;
        }

        initialize_inputs(count, H, y);

        /* Warm-up call; correctness is checked after timing. */
        if (zf_detect_batch(H, y, x_hat, statuses, count) != ZF_OK) {
            fprintf(stderr, "Warm-up failed for batch size %zu\n",
                    count);
            free(H);
            free(y);
            free(x_hat);
            free(statuses);
            return EXIT_FAILURE;
        }

        struct timespec start;
        struct timespec end;

        if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
            perror("clock_gettime");
            free(H);
            free(y);
            free(x_hat);
            free(statuses);
            return EXIT_FAILURE;
        }

        for (size_t iteration = 0; iteration < iterations; ++iteration) {
            zf_status batch_status =
                zf_detect_batch(H, y, x_hat, statuses, count);

            if (batch_status != ZF_OK) {
                fprintf(stderr, "Batch call failed during benchmark\n");
                free(H);
                free(y);
                free(x_hat);
                free(statuses);
                return EXIT_FAILURE;
            }
        }

        if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
            perror("clock_gettime");
            free(H);
            free(y);
            free(x_hat);
            free(statuses);
            return EXIT_FAILURE;
        }

        /* Validate the results outside the timed region. */
        int valid = 1;
        for (size_t i = 0; i < count; ++i) {
            if (statuses[i] != ZF_OK ||
                !isfinite(creal(x_hat[2U * i])) ||
                !isfinite(cimag(x_hat[2U * i])) ||
                !isfinite(creal(x_hat[2U * i + 1U])) ||
                !isfinite(cimag(x_hat[2U * i + 1U]))) {
                valid = 0;
                break;
            }
        }

        const double seconds = elapsed_seconds(start, end);
        const double total_pairs = (double)count * (double)iterations;
        const double ns_per_pair = seconds * 1e9 / total_pairs;
        const double pairs_per_second = total_pairs / seconds;

        if (!valid || seconds <= 0.0) {
            fprintf(stderr,
                    "Validation or timing failed for batch size %zu\n",
                    count);
            free(H);
            free(y);
            free(x_hat);
            free(statuses);
            return EXIT_FAILURE;
        }

        printf("%zu,%zu,%.0f,%.6f,%.2f,%.2f\n",
               count, iterations, total_pairs, seconds,
               ns_per_pair, pairs_per_second);

        free(H);
        free(y);
        free(x_hat);
        free(statuses);
    }

    return EXIT_SUCCESS;
}
