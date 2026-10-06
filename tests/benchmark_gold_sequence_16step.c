#define _POSIX_C_SOURCE 200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void generate_gold_sequence_16step(
    uint8_t *output,
    size_t length,
    uint32_t c_init
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

    uint8_t *output =
        malloc(length);

    if (output == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    struct timespec start;
    struct timespec end;

    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (size_t i = 0; i < iterations; i++) {

        generate_gold_sequence_16step(
            output,
            length,
            0x091A0155U
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
        "Kernel 2 — 16-step Gold Sequence Benchmark\n"
    );

    printf(
        "Sequence length   : %zu bits\n",
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
        "Sequence sample   : %u %u %u %u\n",
        output[0],
        output[1],
        output[2],
        output[3]
    );

    free(output);

    return 0;
}
