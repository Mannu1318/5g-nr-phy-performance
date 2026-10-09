#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <math.h>

#define N_SYMBOLS 1000000
#define ITERATIONS 100

typedef struct {
    float real;
    float imag;
} qam_symbol_t;


/*
 * Reference 256-QAM demapper.
 *
 * This is the same threshold-based logic
 * used by the current implementation.
 */
static void qam256_level_to_bits_reference(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3)
{
    if (value >= 14.0f) {
        *b0=0; *b1=0; *b2=0; *b3=0;
    } else if (value >= 12.0f) {
        *b0=0; *b1=0; *b2=0; *b3=1;
    } else if (value >= 10.0f) {
        *b0=0; *b1=0; *b2=1; *b3=0;
    } else if (value >= 8.0f) {
        *b0=0; *b1=0; *b2=1; *b3=1;
    } else if (value >= 6.0f) {
        *b0=0; *b1=1; *b2=0; *b3=0;
    } else if (value >= 4.0f) {
        *b0=0; *b1=1; *b2=0; *b3=1;
    } else if (value >= 2.0f) {
        *b0=0; *b1=1; *b2=1; *b3=0;
    } else if (value >= 0.0f) {
        *b0=0; *b1=1; *b2=1; *b3=1;
    } else if (value >= -2.0f) {
        *b0=1; *b1=1; *b2=1; *b3=1;
    } else if (value >= -4.0f) {
        *b0=1; *b1=1; *b2=1; *b3=0;
    } else if (value >= -6.0f) {
        *b0=1; *b1=1; *b2=0; *b3=1;
    } else if (value >= -8.0f) {
        *b0=1; *b1=1; *b2=0; *b3=0;
    } else if (value >= -10.0f) {
        *b0=1; *b1=0; *b2=1; *b3=1;
    } else if (value >= -12.0f) {
        *b0=1; *b1=0; *b2=1; *b3=0;
    } else if (value >= -14.0f) {
        *b0=1; *b1=0; *b2=0; *b3=1;
    } else {
        *b0=1; *b1=0; *b2=0; *b3=0;
    }
}


/*
 * Optimized experimental 256-QAM demapper.
 *
 * Arithmetic index calculation + lookup table.
 */
static void qam256_level_to_bits_optimized(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3)
{
    static const unsigned char table[16][4] = {
        {0,0,0,0},
        {0,0,0,1},
        {0,0,1,0},
        {0,0,1,1},
        {0,1,0,0},
        {0,1,0,1},
        {0,1,1,0},
        {0,1,1,1},
        {1,1,1,1},
        {1,1,1,0},
        {1,1,0,1},
        {1,1,0,0},
        {1,0,1,1},
        {1,0,1,0},
        {1,0,0,1},
        {1,0,0,0}
    };

    int index;

    if (value >= 0.0f) {
        index = 7 - (int)(value * 0.5f);
    } else {
        index = 7 + (int)ceilf((-value) * 0.5f);
    }

    if (index < 0)
        index = 0;

    if (index > 15)
        index = 15;

    *b0 = table[index][0];
    *b1 = table[index][1];
    *b2 = table[index][2];
    *b3 = table[index][3];
}


/*
 * Full reference demapper.
 */
static void qam256_demap_reference(
    const qam_symbol_t *symbols,
    unsigned char *bits,
    size_t n_symbols)
{
    const float normalization = 1.0f / sqrtf(170.0f);

    for (size_t i = 0; i < n_symbols; i++) {

        float real = symbols[i].real / normalization;
        float imag = symbols[i].imag / normalization;

        unsigned char i_b0, i_b1, i_b2, i_b3;
        unsigned char q_b0, q_b1, q_b2, q_b3;

        qam256_level_to_bits_reference(
            real,
            &i_b0, &i_b1, &i_b2, &i_b3
        );

        qam256_level_to_bits_reference(
            imag,
            &q_b0, &q_b1, &q_b2, &q_b3
        );

        bits[8*i]   = i_b0;
        bits[8*i+1] = q_b0;
        bits[8*i+2] = i_b1;
        bits[8*i+3] = q_b1;
        bits[8*i+4] = i_b2;
        bits[8*i+5] = q_b2;
        bits[8*i+6] = i_b3;
        bits[8*i+7] = q_b3;
    }
}


/*
 * Full optimized demapper.
 */
static void qam256_demap_optimized(
    const qam_symbol_t *symbols,
    unsigned char *bits,
    size_t n_symbols)
{
    const float normalization = 1.0f / sqrtf(170.0f);

    for (size_t i = 0; i < n_symbols; i++) {

        float real = symbols[i].real / normalization;
        float imag = symbols[i].imag / normalization;

        unsigned char i_b0, i_b1, i_b2, i_b3;
        unsigned char q_b0, q_b1, q_b2, q_b3;

        qam256_level_to_bits_optimized(
            real,
            &i_b0, &i_b1, &i_b2, &i_b3
        );

        qam256_level_to_bits_optimized(
            imag,
            &q_b0, &q_b1, &q_b2, &q_b3
        );

        bits[8*i]   = i_b0;
        bits[8*i+1] = q_b0;
        bits[8*i+2] = i_b1;
        bits[8*i+3] = q_b1;
        bits[8*i+4] = i_b2;
        bits[8*i+5] = q_b2;
        bits[8*i+6] = i_b3;
        bits[8*i+7] = q_b3;
    }
}


static double elapsed_seconds(
    struct timespec start,
    struct timespec end)
{
    return (double)(end.tv_sec - start.tv_sec)
         + (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}


int main(void)
{
    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    unsigned char *bits_reference =
        malloc(N_SYMBOLS * 8);

    unsigned char *bits_optimized =
        malloc(N_SYMBOLS * 8);

    if (!symbols || !bits_reference || !bits_optimized) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }


    /*
     * Deterministic constellation data.
     *
     * We use all 16 possible I/Q levels repeatedly.
     */
    const float levels[16] = {
         15.0f, 13.0f, 11.0f,  9.0f,
          7.0f,  5.0f,  3.0f,  1.0f,
         -1.0f,-3.0f,-5.0f,-7.0f,
         -9.0f,-11.0f,-13.0f,-15.0f
    };

    const float normalization =
        1.0f / sqrtf(170.0f);

    for (size_t i = 0; i < N_SYMBOLS; i++) {

        symbols[i].real =
            levels[i % 16] * normalization;

        symbols[i].imag =
            levels[(i * 7) % 16] * normalization;
    }


    /*
     * Warm-up.
     */
    qam256_demap_reference(
        symbols,
        bits_reference,
        N_SYMBOLS
    );

    qam256_demap_optimized(
        symbols,
        bits_optimized,
        N_SYMBOLS
    );


    /*
     * Verify both implementations produce
     * exactly the same output.
     */
    for (size_t i = 0; i < N_SYMBOLS * 8; i++) {

        if (bits_reference[i] != bits_optimized[i]) {

            printf(
                "Benchmark correctness: FAIL at bit %zu\n",
                i
            );

            free(symbols);
            free(bits_reference);
            free(bits_optimized);

            return 1;
        }
    }

    printf("Benchmark correctness: PASS\n");


    /*
     * Prevent the compiler from eliminating
     * the benchmarked work.
     */
    volatile unsigned int sink = 0;


    /*
     * Benchmark reference implementation.
     */
    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        qam256_demap_reference(
            symbols,
            bits_reference,
            N_SYMBOLS
        );

        sink += bits_reference[
            iteration % (N_SYMBOLS * 8)
        ];
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double reference_time =
        elapsed_seconds(start, end);


    /*
     * Benchmark optimized implementation.
     */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        qam256_demap_optimized(
            symbols,
            bits_optimized,
            N_SYMBOLS
        );

        sink += bits_optimized[
            iteration % (N_SYMBOLS * 8)
        ];
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double optimized_time =
        elapsed_seconds(start, end);


    double reference_speed =
        ((double)N_SYMBOLS * ITERATIONS)
        / reference_time
        / 1e6;

    double optimized_speed =
        ((double)N_SYMBOLS * ITERATIONS)
        / optimized_time
        / 1e6;

    double speedup =
        reference_time / optimized_time;


    printf("\n");
    printf("256-QAM demapper benchmark\n");
    printf("--------------------------\n");

    printf(
        "Reference:  %.6f s  %.3f Msymbol/s\n",
        reference_time,
        reference_speed
    );

    printf(
        "Optimized:  %.6f s  %.3f Msymbol/s\n",
        optimized_time,
        optimized_speed
    );

    printf(
        "Speedup:    %.3fx\n",
        speedup
    );

    printf(
        "Benchmark sink: %u\n",
        sink
    );


    free(symbols);
    free(bits_reference);
    free(bits_optimized);

    return 0;
}
