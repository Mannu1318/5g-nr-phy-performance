#define _POSIX_C_SOURCE 200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void scramble_bits_optimized(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end
)
{
    return
        (double)(end->tv_sec - start->tv_sec) +
        (double)(end->tv_nsec - start->tv_nsec) /
        1e9;
}

int main(void)
{
    const size_t length = 1000000;
    const size_t iterations = 100;

    uint8_t *input =
        malloc(length);

    uint8_t *output =
        malloc(length);

    if (input == NULL ||
        output == NULL) {

        fprintf(
            stderr,
            "Memory allocation failed\n"
        );

        free(input);
        free(output);

        return 1;
    }

    for (size_t i = 0; i < length; i++) {
        input[i] =
            (uint8_t)((i * 7U + 3U) & 1U);
    }

    struct timespec start;
    struct timespec end;

    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (size_t i = 0; i < iterations; i++) {

        scramble_bits_optimized(
            input,
            output,
            length,
            0x1234,
            0x0155,
            0
        );
    }

    clock_gettime(
        CLOCK_MONOTONIC,
        &end
    );

    double elapsed =
        elapsed_seconds(
            &start,
            &end
        );

    size_t total_bits =
        length * iterations;

    double throughput =
        (double)total_bits /
        elapsed /
        1e6;

    printf(
        "Kernel 2 — Optimized Scrambling Benchmark\n"
    );

    printf(
        "Input length      : %zu bits\n",
        length
    );

    printf(
        "Iterations        : %zu\n",
        iterations
    );

    printf(
        "Total bits        : %zu\n",
        total_bits
    );

    printf(
        "Elapsed time      : %.6f s\n",
        elapsed
    );

    printf(
        "Throughput        : %.2f Mbit/s\n",
        throughput
    );

    printf(
        "Output sample     : %u %u %u %u\n",
        output[0],
        output[1],
        output[2],
        output[3]
    );

    free(input);
    free(output);

    return 0;
}
