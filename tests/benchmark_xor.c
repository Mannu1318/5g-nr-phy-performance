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
    uint8_t *input;
    uint8_t *sequence;
    uint8_t *output;

    struct timespec start;
    struct timespec end;

    double elapsed;
    double total_bits;
    double throughput_mbps;

    input = malloc(BENCHMARK_LENGTH * sizeof(uint8_t));
    sequence = malloc(BENCHMARK_LENGTH * sizeof(uint8_t));
    output = malloc(BENCHMARK_LENGTH * sizeof(uint8_t));

    if (input == NULL || sequence == NULL || output == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        free(input);
        free(sequence);
        free(output);
        return 1;
    }

    for (size_t i = 0; i < BENCHMARK_LENGTH; i++) {
        input[i] = (uint8_t)(i & 1U);
    }

    /*
     * Generate the Gold sequence outside the timed region.
     */
    generate_gold_sequence(
        sequence,
        BENCHMARK_LENGTH,
        0x091A0155
    );

    /*
     * Warm-up XOR.
     */
    for (size_t i = 0; i < BENCHMARK_LENGTH; i++) {
        output[i] = input[i] ^ sequence[i];
    }

    if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
        perror("clock_gettime");
        free(input);
        free(sequence);
        free(output);
        return 1;
    }

    for (size_t iteration = 0;
         iteration < BENCHMARK_ITERATIONS;
         iteration++) {

        for (size_t i = 0; i < BENCHMARK_LENGTH; i++) {
            output[i] = input[i] ^ sequence[i];
        }
    }

    if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
        perror("clock_gettime");
        free(input);
        free(sequence);
        free(output);
        return 1;
    }

    elapsed = elapsed_seconds(&start, &end);

    total_bits =
        (double)BENCHMARK_LENGTH *
        (double)BENCHMARK_ITERATIONS;

    throughput_mbps =
        total_bits / elapsed / 1000000.0;

    printf("Kernel 2 — XOR-only Benchmark\n");
    printf("Input length      : %u bits\n", BENCHMARK_LENGTH);
    printf("Iterations        : %u\n", BENCHMARK_ITERATIONS);
    printf("Total bits        : %.0f\n", total_bits);
    printf("Elapsed time      : %.6f s\n", elapsed);
    printf("Throughput        : %.2f Mbit/s\n", throughput_mbps);

    printf("Output sample     : %u %u %u %u\n",
           output[0],
           output[1],
           output[2],
           output[3]);

    free(input);
    free(sequence);
    free(output);

    return 0;
}
