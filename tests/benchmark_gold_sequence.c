#define _POSIX_C_SOURCE 200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define BENCHMARK_LENGTH 1000000U
#define BENCHMARK_ITERATIONS 100

void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end
)
{
    return (double)(end->tv_sec - start->tv_sec)
         + (double)(end->tv_nsec - start->tv_nsec) / 1e9;
}

int main(void)
{
    uint8_t *sequence;

    struct timespec start;
    struct timespec end;

    double elapsed;
    double total_bits;
    double throughput_mbps;

    sequence = malloc(BENCHMARK_LENGTH * sizeof(uint8_t));

    if (sequence == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    /*
     * Warm-up run.
     */
    generate_gold_sequence(
        sequence,
        BENCHMARK_LENGTH,
        0x091A0155
    );

    if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
        perror("clock_gettime");
        free(sequence);
        return 1;
    }

    for (size_t iteration = 0;
         iteration < BENCHMARK_ITERATIONS;
         iteration++) {

        generate_gold_sequence(
            sequence,
            BENCHMARK_LENGTH,
            0x091A0155
        );
    }

    if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
        perror("clock_gettime");
        free(sequence);
        return 1;
    }

    elapsed = elapsed_seconds(&start, &end);

    total_bits =
        (double)BENCHMARK_LENGTH *
        (double)BENCHMARK_ITERATIONS;

    throughput_mbps =
        total_bits / elapsed / 1000000.0;

    printf("Kernel 2 — Gold Sequence Benchmark\n");
    printf("Sequence length   : %u bits\n", BENCHMARK_LENGTH);
    printf("Iterations        : %u\n", BENCHMARK_ITERATIONS);
    printf("Total bits        : %.0f\n", total_bits);
    printf("Elapsed time      : %.6f s\n", elapsed);
    printf("Throughput        : %.2f Mbit/s\n", throughput_mbps);

    printf("Sequence sample   : %u %u %u %u\n",
           sequence[0],
           sequence[1],
           sequence[2],
           sequence[3]);

    free(sequence);

    return 0;
}
