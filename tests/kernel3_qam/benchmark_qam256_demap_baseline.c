#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N_SYMBOLS 1000000
#define ITERATIONS 100

typedef struct {
    float real;
    float imag;
} qam_symbol_t;


/*
 * Reference 256-QAM level-to-bits decision.
 *
 * This is intentionally kept identical to the
 * current production/reference threshold approach.
 */
static void qam256_level_to_bits_reference(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3
)
{
    if (value >= 14.0f) {
        *b0 = 0; *b1 = 0; *b2 = 0; *b3 = 0;
    } else if (value >= 12.0f) {
        *b0 = 0; *b1 = 0; *b2 = 0; *b3 = 1;
    } else if (value >= 10.0f) {
        *b0 = 0; *b1 = 0; *b2 = 1; *b3 = 0;
    } else if (value >= 8.0f) {
        *b0 = 0; *b1 = 0; *b2 = 1; *b3 = 1;
    } else if (value >= 6.0f) {
        *b0 = 0; *b1 = 1; *b2 = 0; *b3 = 0;
    } else if (value >= 4.0f) {
        *b0 = 0; *b1 = 1; *b2 = 0; *b3 = 1;
    } else if (value >= 2.0f) {
        *b0 = 0; *b1 = 1; *b2 = 1; *b3 = 0;
    } else if (value >= 0.0f) {
        *b0 = 0; *b1 = 1; *b2 = 1; *b3 = 1;
    } else if (value >= -2.0f) {
        *b0 = 1; *b1 = 1; *b2 = 1; *b3 = 1;
    } else if (value >= -4.0f) {
        *b0 = 1; *b1 = 1; *b2 = 1; *b3 = 0;
    } else if (value >= -6.0f) {
        *b0 = 1; *b1 = 1; *b2 = 0; *b3 = 1;
    } else if (value >= -8.0f) {
        *b0 = 1; *b1 = 1; *b2 = 0; *b3 = 0;
    } else if (value >= -10.0f) {
        *b0 = 1; *b1 = 0; *b2 = 1; *b3 = 1;
    } else if (value >= -12.0f) {
        *b0 = 1; *b1 = 0; *b2 = 1; *b3 = 0;
    } else if (value >= -14.0f) {
        *b0 = 1; *b1 = 0; *b2 = 0; *b3 = 1;
    } else {
        *b0 = 1; *b1 = 0; *b2 = 0; *b3 = 0;
    }
}


static void qam256_demap_reference(
    const qam_symbol_t *symbols,
    unsigned char *bits,
    size_t n_symbols
)
{
    const float normalization = 1.0f / 13.0384048f;

    for (size_t i = 0; i < n_symbols; i++) {

        float i_value = symbols[i].real / normalization;
        float q_value = symbols[i].imag / normalization;

        unsigned char i_b0, i_b1, i_b2, i_b3;
        unsigned char q_b0, q_b1, q_b2, q_b3;

        qam256_level_to_bits_reference(
            i_value,
            &i_b0, &i_b1, &i_b2, &i_b3
        );

        qam256_level_to_bits_reference(
            q_value,
            &q_b0, &q_b1, &q_b2, &q_b3
        );

        bits[8 * i]     = i_b0;
        bits[8 * i + 1] = q_b0;
        bits[8 * i + 2] = i_b1;
        bits[8 * i + 3] = q_b1;
        bits[8 * i + 4] = i_b2;
        bits[8 * i + 5] = q_b2;
        bits[8 * i + 6] = i_b3;
        bits[8 * i + 7] = q_b3;
    }
}


static double elapsed_seconds(
    struct timespec start,
    struct timespec end
)
{
    return (double)(end.tv_sec - start.tv_sec)
         + (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}


int main(void)
{
    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    unsigned char *bits =
        malloc(N_SYMBOLS * 8);

    if (symbols == NULL || bits == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        free(symbols);
        free(bits);
        return 1;
    }

    /*
     * Generate deterministic 256-QAM constellation points.
     *
     * All 16 amplitude levels are exercised.
     */
    const float levels[16] = {
        -15.0f, -13.0f, -11.0f, -9.0f,
        -7.0f,  -5.0f,  -3.0f,  -1.0f,
         1.0f,   3.0f,   5.0f,   7.0f,
         9.0f,  11.0f,  13.0f,  15.0f
    };

    const float normalization = 1.0f / 13.0384048f;

    for (size_t i = 0; i < N_SYMBOLS; i++) {
        symbols[i].real =
            levels[i % 16] * normalization;

        symbols[i].imag =
            levels[(i + 7) % 16] * normalization;
    }

    /*
     * Warm-up.
     */
    qam256_demap_reference(
        symbols,
        bits,
        N_SYMBOLS
    );

    /*
     * Benchmark.
     */
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        qam256_demap_reference(
            symbols,
            bits,
            N_SYMBOLS
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed =
        elapsed_seconds(start, end);

    /*
     * Prevent the compiler from eliminating the work.
     */
    volatile unsigned int sink = 0;

    for (size_t i = 0; i < N_SYMBOLS * 8; i++) {
        sink += bits[i];
    }

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double symbols_per_second =
        total_symbols / elapsed;

    printf("256-QAM baseline demapper benchmark\n");
    printf("------------------------------------\n");
    printf("Time:       %.6f s\n", elapsed);
    printf("Throughput: %.3f Msymbol/s\n",
           symbols_per_second / 1e6);
    printf("Sink:       %u\n", sink);

    free(symbols);
    free(bits);

    return 0;
}
