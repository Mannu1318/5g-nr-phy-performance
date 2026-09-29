#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stddef.h>

uint32_t crc24a(const uint8_t *bits, size_t nbits);

#define INPUT_BITS (1024u * 1024u)
#define ITERATIONS 100u

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end)
{
    return (double)(end->tv_sec - start->tv_sec)
         + (double)(end->tv_nsec - start->tv_nsec) / 1e9;
}

int main(void)
{
    uint8_t *bits = malloc(INPUT_BITS * sizeof(uint8_t));

    if (bits == NULL)
    {
        fprintf(stderr, "Failed to allocate input buffer.\n");
        return 1;
    }

    for (size_t i = 0; i < INPUT_BITS; i++)
    {
        bits[i] = (uint8_t)(i & 1u);
    }

    uint32_t result = 0u;

    struct timespec start;
    struct timespec end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (unsigned int i = 0; i < ITERATIONS; i++)
    {
        result ^= crc24a(bits, INPUT_BITS);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double total_seconds = elapsed_seconds(&start, &end);

    double total_bits =
        (double)INPUT_BITS * (double)ITERATIONS;

    double throughput_gbps =
        total_bits / total_seconds / 1e9;

    printf("CRC24A scalar benchmark\n");
    printf("Input size:       %u bits\n", INPUT_BITS);
    printf("Iterations:       %u\n", ITERATIONS);
    printf("Total time:       %.6f s\n", total_seconds);
    printf("Throughput:       %.3f Gbit/s\n", throughput_gbps);
    printf("Checksum:         0x%06X\n", result);

    free(bits);

    return 0;
}
