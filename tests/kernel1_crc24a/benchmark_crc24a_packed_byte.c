#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stddef.h>

uint32_t crc24a_packed_byte(const uint8_t *data, size_t nbits);

#define INPUT_BITS (1024u * 1024u)
#define INPUT_BYTES (INPUT_BITS / 8u)
#define ITERATIONS 100u
#define SAMPLES 10u

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end)
{
    return (double)(end->tv_sec - start->tv_sec)
         + (double)(end->tv_nsec - start->tv_nsec) / 1e9;
}

int main(void)
{
    uint8_t *data = malloc(INPUT_BYTES);

    if (data == NULL)
    {
        fprintf(stderr, "Failed to allocate input buffer.\n");
        return 1;
    }

    for (size_t i = 0; i < INPUT_BYTES; i++)
    {
        data[i] = (uint8_t)(i & 0xFFu);
    }

    double min_seconds = 1e100;
    double max_seconds = 0.0;
    double total_seconds = 0.0;

    uint32_t result = 0u;

    for (unsigned int sample = 0; sample < SAMPLES; sample++)
    {
        struct timespec start;
        struct timespec end;

        clock_gettime(CLOCK_MONOTONIC, &start);

        for (unsigned int i = 0; i < ITERATIONS; i++)
        {
            result ^= crc24a_packed_byte(data, INPUT_BITS);
        }

        clock_gettime(CLOCK_MONOTONIC, &end);

        double seconds = elapsed_seconds(&start, &end);

        if (seconds < min_seconds)
        {
            min_seconds = seconds;
        }

        if (seconds > max_seconds)
        {
            max_seconds = seconds;
        }

        total_seconds += seconds;
    }

    double average_seconds =
        total_seconds / (double)SAMPLES;

    double total_bits =
        (double)INPUT_BITS * (double)ITERATIONS;

    double min_throughput =
        total_bits / max_seconds / 1e9;

    double average_throughput =
        total_bits / average_seconds / 1e9;

    double max_throughput =
        total_bits / min_seconds / 1e9;

    printf("CRC24A packed-byte benchmark\n");
    printf("Input size:          %u bits\n", INPUT_BITS);
    printf("Input storage:       %u bytes\n", INPUT_BYTES);
    printf("Iterations/sample:   %u\n", ITERATIONS);
    printf("Samples:              %u\n", SAMPLES);
    printf("Minimum time:         %.6f s\n", min_seconds);
    printf("Average time:         %.6f s\n", average_seconds);
    printf("Maximum time:         %.6f s\n", max_seconds);
    printf("Minimum throughput:   %.3f Gbit/s\n", min_throughput);
    printf("Average throughput:   %.3f Gbit/s\n", average_throughput);
    printf("Maximum throughput:   %.3f Gbit/s\n", max_throughput);
    printf("Checksum:             0x%06X\n", result);

    free(data);

    return 0;
}
