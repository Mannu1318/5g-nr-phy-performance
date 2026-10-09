#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "qam.h"

#define N_SYMBOLS 1000000
#define ITERATIONS 100

typedef struct {
    float real;
    float imag;
} packed_qam256_entry_t;

static packed_qam256_entry_t qam256_packed_table[256];

static float qam256_level_from_index(unsigned int index)
{
    static const float levels[16] = {
         15.0f,  13.0f,  11.0f,   9.0f,
          7.0f,   5.0f,   3.0f,   1.0f,
        -15.0f, -13.0f, -11.0f,  -9.0f,
         -7.0f,  -5.0f,  -3.0f,  -1.0f
    };

    return levels[index];
}

static void qam256_packed_table_init(void)
{
    const float normalization = 1.0f / __builtin_sqrtf(170.0f);

    for (unsigned int value = 0; value < 256; value++) {

        unsigned int i_index =
            (((value >> 7) & 1) << 3) |
            (((value >> 5) & 1) << 2) |
            (((value >> 3) & 1) << 1) |
            ((value >> 1) & 1);

        unsigned int q_index =
            (((value >> 6) & 1) << 3) |
            (((value >> 4) & 1) << 2) |
            (((value >> 2) & 1) << 1) |
            (value & 1);

        qam256_packed_table[value].real =
            qam256_level_from_index(i_index) * normalization;

        qam256_packed_table[value].imag =
            qam256_level_from_index(q_index) * normalization;
    }
}

static void qam256_map_packed(
    const unsigned char *packed_bits,
    size_t n_symbols,
    qam_symbol_t *symbols)
{
    for (size_t i = 0; i < n_symbols; i++) {
        symbols[i].real =
            qam256_packed_table[packed_bits[i]].real;

        symbols[i].imag =
            qam256_packed_table[packed_bits[i]].imag;
    }
}

static void fill_unpacked_bits(unsigned char *bits, size_t n_bits)
{
    for (size_t i = 0; i < n_bits; i++) {
        bits[i] = (unsigned char)((i * 7 + 3) & 1);
    }
}

static void pack_bits(
    const unsigned char *bits,
    unsigned char *packed,
    size_t n_symbols)
{
    for (size_t i = 0; i < n_symbols; i++) {

        packed[i] =
            (unsigned char)(
                (bits[8 * i + 0] << 7) |
                (bits[8 * i + 1] << 6) |
                (bits[8 * i + 2] << 5) |
                (bits[8 * i + 3] << 4) |
                (bits[8 * i + 4] << 3) |
                (bits[8 * i + 5] << 2) |
                (bits[8 * i + 6] << 1) |
                (bits[8 * i + 7])
            );
    }
}

static double elapsed_seconds(
    struct timespec start,
    struct timespec end)
{
    return (double)(end.tv_sec - start.tv_sec) +
           (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}

int main(void)
{
    const size_t n_bits = N_SYMBOLS * 8;

    unsigned char *bits =
        malloc(n_bits * sizeof(unsigned char));

    unsigned char *packed_bits =
        malloc(N_SYMBOLS * sizeof(unsigned char));

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !packed_bits || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        free(bits);
        free(packed_bits);
        free(symbols);
        return 1;
    }

    qam256_packed_table_init();

    fill_unpacked_bits(bits, n_bits);
    pack_bits(bits, packed_bits, N_SYMBOLS);

    /*
     * Warm-up
     */
    qam256_map(bits, n_bits, symbols);
    qam256_map_packed(packed_bits, N_SYMBOLS, symbols);

    volatile float benchmark_sink = 0.0f;

    struct timespec start;
    struct timespec end;

    /*
     * ---------------------------------------------------------
     * Original unpacked mapper
     * ---------------------------------------------------------
     */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iteration = 0; iteration < ITERATIONS; iteration++) {
        qam256_map(bits, n_bits, symbols);
        benchmark_sink += symbols[N_SYMBOLS - 1].real;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double original_time =
        elapsed_seconds(start, end);

    /*
     * ---------------------------------------------------------
     * Packed-byte mapper
     * ---------------------------------------------------------
     */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iteration = 0; iteration < ITERATIONS; iteration++) {
        qam256_map_packed(
            packed_bits,
            N_SYMBOLS,
            symbols
        );

        benchmark_sink += symbols[N_SYMBOLS - 1].real;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double packed_time =
        elapsed_seconds(start, end);

    double original_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        original_time / 1e6;

    double packed_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        packed_time / 1e6;

    double speedup =
        original_time / packed_time;

    printf("\n");
    printf("256-QAM Packed-Byte Mapping Benchmark\n");
    printf("--------------------------------------\n");
    printf("Symbols/iteration: %d\n", N_SYMBOLS);
    printf("Iterations:        %d\n", ITERATIONS);
    printf("\n");

    printf(
        "Original unpacked:  %.6f s  %.3f Msymbol/s\n",
        original_time,
        original_rate
    );

    printf(
        "Packed-byte:        %.6f s  %.3f Msymbol/s\n",
        packed_time,
        packed_rate
    );

    printf("\n");

    printf(
        "Speedup:            %.3fx\n",
        speedup
    );

    printf(
        "Benchmark sink:     %.3f\n",
        benchmark_sink
    );

    free(bits);
    free(packed_bits);
    free(symbols);

    return 0;
}
