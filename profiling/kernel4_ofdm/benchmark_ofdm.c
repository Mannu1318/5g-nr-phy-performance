#define _POSIX_C_SOURCE 200809L

#include "ofdm.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define NUM_SIZES 6
#define WARMUP_ITERATIONS 100
#define BENCHMARK_ITERATIONS 2000
#define NUM_SAMPLES 7

static const size_t fft_sizes[NUM_SIZES] = {
    64, 128, 256, 512, 1024, 2048
};

static volatile double result_sink = 0.0;

static double elapsed_seconds(
    const struct timespec *start,
    const struct timespec *end
) {
    return (double)(end->tv_sec - start->tv_sec)
         + (double)(end->tv_nsec - start->tv_nsec) / 1.0e9;
}

static void sort_samples(double values[NUM_SAMPLES]) {
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

static int benchmark_transform(
    size_t n,
    int use_ifft,
    double *median_ns,
    double *minimum_ns
) {
    ofdm_sample_t *input = calloc(n, sizeof(*input));
    ofdm_sample_t *output = calloc(n, sizeof(*output));

    if (input == NULL || output == NULL) {
        free(input);
        free(output);
        return -1;
    }

    for (size_t i = 0; i < n; ++i) {
        input[i].real = sin(0.013 * (double)i)
                      + 0.25 * cos(0.031 * (double)i);
        input[i].imag = cos(0.017 * (double)i)
                      - 0.15 * sin(0.023 * (double)i);
    }

    for (size_t i = 0; i < WARMUP_ITERATIONS; ++i) {
        int status = use_ifft
            ? ofdm_ifft(input, output, n)
            : ofdm_fft(input, output, n);

        if (status != 0) {
            free(input);
            free(output);
            return -1;
        }
    }

    double samples[NUM_SAMPLES];

    for (size_t sample = 0; sample < NUM_SAMPLES; ++sample) {
        struct timespec start;
        struct timespec end;

        if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
            free(input);
            free(output);
            return -1;
        }

        for (size_t i = 0; i < BENCHMARK_ITERATIONS; ++i) {
            int status = use_ifft
                ? ofdm_ifft(input, output, n)
                : ofdm_fft(input, output, n);

            if (status != 0) {
                free(input);
                free(output);
                return -1;
            }

            result_sink += output[i % n].real * 1.0e-30;
        }

        if (clock_gettime(CLOCK_MONOTONIC, &end) != 0) {
            free(input);
            free(output);
            return -1;
        }

        samples[sample] =
            elapsed_seconds(&start, &end) * 1.0e9
            / (double)BENCHMARK_ITERATIONS;
    }

    sort_samples(samples);
    *minimum_ns = samples[0];
    *median_ns = samples[NUM_SAMPLES / 2];

    free(input);
    free(output);
    return 0;
}

int main(void) {
    printf("Kernel 4: OFDM FFT/IFFT repeated-sample benchmark\n");
    printf("Warm-up iterations per transform: %d\n", WARMUP_ITERATIONS);
    printf("Iterations per sample: %d\n", BENCHMARK_ITERATIONS);
    printf("Independent samples per transform: %d\n\n", NUM_SAMPLES);

    printf("%-10s %-8s %16s %16s\n",
           "FFT size", "Type", "Median (ns)", "Minimum (ns)");
    printf("--------------------------------------------------------\n");

    for (size_t i = 0; i < NUM_SIZES; ++i) {
        size_t n = fft_sizes[i];

        for (int use_ifft = 0; use_ifft <= 1; ++use_ifft) {
            double median_ns;
            double minimum_ns;

            if (benchmark_transform(
                    n, use_ifft, &median_ns, &minimum_ns) != 0) {
                fprintf(stderr, "Benchmark failed for N=%zu\n", n);
                return EXIT_FAILURE;
            }

            printf("%-10zu %-8s %16.2f %16.2f\n",
                   n,
                   use_ifft ? "IFFT" : "FFT",
                   median_ns,
                   minimum_ns);
        }
    }

    printf("\nResult sink: %.12e\n", result_sink);
    printf("Benchmark completed successfully.\n");
    return EXIT_SUCCESS;
}
