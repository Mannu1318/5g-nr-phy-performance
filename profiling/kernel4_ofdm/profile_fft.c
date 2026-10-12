#include "ofdm.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define FFT_SIZE 2048
#define ITERATIONS 200000

static volatile double result_sink = 0.0;

int main(void)
{
    ofdm_sample_t *input = calloc(FFT_SIZE, sizeof(*input));
    ofdm_sample_t *output = calloc(FFT_SIZE, sizeof(*output));

    if (input == NULL || output == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        free(input);
        free(output);
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < FFT_SIZE; ++i) {
        input[i].real = sin(0.013 * (double)i)
                      + 0.25 * cos(0.031 * (double)i);
        input[i].imag = cos(0.017 * (double)i)
                      - 0.15 * sin(0.023 * (double)i);
    }

    /* Warm up the FFT before the measured workload. */
    for (size_t i = 0; i < 100; ++i) {
        if (ofdm_fft(input, output, FFT_SIZE) != 0) {
            fprintf(stderr, "FFT warm-up failed\n");
            free(input);
            free(output);
            return EXIT_FAILURE;
        }
    }

    for (size_t i = 0; i < ITERATIONS; ++i) {
        if (ofdm_fft(input, output, FFT_SIZE) != 0) {
            fprintf(stderr, "FFT failed at iteration %zu\n", i);
            free(input);
            free(output);
            return EXIT_FAILURE;
        }

        result_sink += output[i % FFT_SIZE].real * 1.0e-30;
    }

    printf("Focused FFT profiling workload\n");
    printf("FFT size: %d\n", FFT_SIZE);
    printf("Measured iterations: %d\n", ITERATIONS);
    printf("Result sink: %.12e\n", result_sink);

    free(input);
    free(output);
    return EXIT_SUCCESS;
}
