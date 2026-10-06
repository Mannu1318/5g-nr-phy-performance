#define _POSIX_C_SOURCE 200809L

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define BENCHMARK_LENGTH 1000000U
#define BENCHMARK_ITERATIONS 100

void generate_gold_sequence_packed(
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
    uint8_t *sequence =
        malloc(BENCHMARK_LENGTH * sizeof(uint8_t));

    if (sequence == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    uint32_t c_init = 0x091A0155;

    /* Warm-up */
    generate_gold_sequence_packed(
        sequence,
        BENCHMARK_LENGTH,
        c_init
    );

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < BENCHMARK_ITERATIONS; i++) {
        generate_gold_sequence_packed(
            sequence,
            BENCHMARK_LENGTH,
            c_init
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed =
        elapsed_seconds(&start, &end);

    double total_bits =
        (double)BENCHMARK_LENGTH *
        BENCHMARK_ITERATIONS;

    double throughput =
        total_bits / elapsed / 1e6;

    printf("Kernel 2 — Packed LFSR Gold Sequence Benchmark\n");
    printf("Sequence length   : %u bits\n",
           BENCHMARK_LENGTH);
    printf("Iterations        : %d\n",
           BENCHMARK_ITERATIONS);
    printf("Total bits        : %.0f\n",
           total_bits);
    printf("Elapsed time      : %.6f s\n",
           elapsed);
    printf("Throughput        : %.2f Mbit/s\n",
           throughput);
    printf("Sequence sample   : %u %u %u %u\n",
           sequence[0],
           sequence[1],
           sequence[2],
           sequence[3]);

    free(sequence);

    return 0;
}
