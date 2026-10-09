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
 * 16-entry lookup table.
 *
 * Index:
 *
 *   0 -> 0000
 *   1 -> 0001
 *   2 -> 0010
 *   ...
 *   15 -> 1111
 *
 * The table entries correspond to the Gray-coded
 * 256-QAM amplitude mapping.
 */
static const unsigned char level_bits[16][4] = {
    {0, 0, 0, 0},
    {0, 0, 0, 1},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 1, 0, 0},
    {0, 1, 0, 1},
    {0, 1, 1, 0},
    {0, 1, 1, 1},
    {1, 1, 1, 1},
    {1, 1, 1, 0},
    {1, 1, 0, 1},
    {1, 1, 0, 0},
    {1, 0, 1, 1},
    {1, 0, 1, 0},
    {1, 0, 0, 1},
    {1, 0, 0, 0
    }
};


/*
 * Optimized 256-QAM level quantizer.
 *
 * Instead of walking through 15 threshold comparisons,
 * calculate the constellation-region index directly.
 */
static unsigned int qam256_level_index(float value)
{
    unsigned int index;

    if (value >= 0.0f) {
        index = 7U - (unsigned int)(value * 0.5f);
    } else {
        index = 7U +
                (unsigned int)((-value) * 0.5f + 0.999999f);
    }

    /*
     * Protect against values outside the normal
     * 256-QAM constellation range.
     */
    if (index > 15U) {
        index = 15U;
    }

    return index;
}


static void qam256_level_to_bits_optimized(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3
)
{
    unsigned int index =
        qam256_level_index(value);

    *b0 = level_bits[index][0];
    *b1 = level_bits[index][1];
    *b2 = level_bits[index][2];
    *b3 = level_bits[index][3];
}


static void qam256_demap_optimized(
    const qam_symbol_t *symbols,
    unsigned char *bits,
    size_t n_symbols
)
{
    const float normalization = 1.0f / 13.0384048f;

    for (size_t i = 0; i < n_symbols; i++) {

        float i_value =
            symbols[i].real / normalization;

        float q_value =
            symbols[i].imag / normalization;

        unsigned char i_b0, i_b1, i_b2, i_b3;
        unsigned char q_b0, q_b1, q_b2, q_b3;

        qam256_level_to_bits_optimized(
            i_value,
            &i_b0,
            &i_b1,
            &i_b2,
            &i_b3
        );

        qam256_level_to_bits_optimized(
            q_value,
            &q_b0,
            &q_b1,
            &q_b2,
            &q_b3
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
     * Same deterministic constellation data
     * used by the baseline benchmark.
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
    qam256_demap_optimized(
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

        qam256_demap_optimized(
            symbols,
            bits,
            N_SYMBOLS
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed =
        elapsed_seconds(start, end);

    /*
     * Prevent compiler elimination.
     */
    volatile unsigned int sink = 0;

    for (size_t i = 0; i < N_SYMBOLS * 8; i++) {
        sink += bits[i];
    }

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double symbols_per_second =
        total_symbols / elapsed;

    printf("256-QAM optimized demapper benchmark\n");
    printf("-------------------------------------\n");
    printf("Time:       %.6f s\n", elapsed);
    printf("Throughput: %.3f Msymbol/s\n",
           symbols_per_second / 1e6);
    printf("Sink:       %u\n", sink);

    free(symbols);
    free(bits);

    return 0;
}
