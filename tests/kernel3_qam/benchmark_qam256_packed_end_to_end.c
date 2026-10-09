#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
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
    const float normalization =
        1.0f / __builtin_sqrtf(170.0f);

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

static void fill_unpacked_bits(
    unsigned char *bits,
    size_t n_bits)
{
    for (size_t i = 0; i < n_bits; i++) {
        bits[i] =
            (unsigned char)((i * 7 + 3) & 1);
    }
}

static void pack_bits(
    const unsigned char *bits,
    unsigned char *packed,
    size_t n_symbols)
{
    for (size_t i = 0; i < n_symbols; i++) {
        unsigned char value = 0;

        for (size_t b = 0; b < 8; b++) {
            value |= (unsigned char)(bits[8 * i + b] << (7 - b));
        }

        packed[i] = value;
    }
}  

static void pack_bits_optimized(
    const unsigned char *bits,
    unsigned char *packed,
    size_t n_symbols)
{
    for (size_t i = 0; i < n_symbols; i++) {

        const unsigned char *src = &bits[8 * i];

        unsigned int value =
            ((unsigned int)src[0] << 7) |
            ((unsigned int)src[1] << 6) |
            ((unsigned int)src[2] << 5) |
            ((unsigned int)src[3] << 4) |
            ((unsigned int)src[4] << 3) |
            ((unsigned int)src[5] << 2) |
            ((unsigned int)src[6] << 1) |
            ((unsigned int)src[7]);

        packed[i] = (unsigned char)value;
    }
}

static void pack_bits_swar(
    const unsigned char *bits,
    unsigned char *packed,
    size_t n_symbols)
{
    for (size_t i = 0; i < n_symbols; i++) {

        uint64_t x;

        memcpy(&x, &bits[8 * i], sizeof(uint64_t));

        x &= 0x0101010101010101ULL;

        x *= 0x8040201008040201ULL;

        packed[i] = (unsigned char)(x >> 56);
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
    const size_t n_bits =
        N_SYMBOLS * 8;

    unsigned char *bits =
        malloc(n_bits);

    unsigned char *packed_bits =
        malloc(N_SYMBOLS);

    unsigned char *packed_bits_optimized =
        malloc(N_SYMBOLS);
unsigned char *packed_bits_swar =
    malloc(N_SYMBOLS);
    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !packed_bits ||!packed_bits_optimized ||!packed_bits_swar || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");

        free(bits);
        free(packed_bits);
        free(symbols);
        free(packed_bits_optimized);
        free(packed_bits_swar);
        return 1;
    }

    qam256_packed_table_init();

    fill_unpacked_bits(bits, n_bits);

    /*
     * Prepare packed input before timing.
     * This is only for the mapper-only comparison.
     */
    pack_bits(
        bits,
        packed_bits,
        N_SYMBOLS
    );
    pack_bits_optimized(
        bits,
        packed_bits_optimized,
        N_SYMBOLS
);
pack_bits_swar(
    bits,
    packed_bits_swar,
    N_SYMBOLS
);
/*
 * Verify that the optimized packing produces
 * exactly the same bytes as the original packing.
 */
for (size_t i = 0; i < N_SYMBOLS; i++) {
    if (packed_bits[i] != packed_bits_optimized[i]) {
        fprintf(stderr,
                "Packing correctness FAILED at symbol %zu: "
                "original=%u optimized=%u\n",
                i,
                packed_bits[i],
                packed_bits_optimized[i]);

        free(bits);
        free(packed_bits);
        free(packed_bits_optimized);
        free(symbols);

        return 1;
    }
}

printf("Packing correctness: PASS\n");
for (size_t i = 0; i < N_SYMBOLS; i++) {
    if (packed_bits[i] != packed_bits_swar[i]) {
        fprintf(stderr,
                "SWAR packing correctness FAILED at symbol %zu: "
                "original=%u swar=%u\n",
                i,
                packed_bits[i],
                packed_bits_swar[i]);

        free(bits);
        free(packed_bits);
        free(packed_bits_optimized);
        free(packed_bits_swar);
        free(symbols);

        return 1;
    }
}

printf("SWAR packing correctness: PASS\n");

    /*
     * Warm-up.
     */
    qam256_map(
        bits,
        n_bits,
        symbols
    );

    pack_bits(
        bits,
        packed_bits,
        N_SYMBOLS
    );

    qam256_map_packed(
        packed_bits,
        N_SYMBOLS,
        symbols
    );

    volatile float benchmark_sink = 0.0f;

    struct timespec start;
    struct timespec end;

    /*
     * ---------------------------------------------------------
     * 1. Original mapper
     * ---------------------------------------------------------
     */
    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        qam256_map(
            bits,
            n_bits,
            symbols
        );

        benchmark_sink +=
            symbols[N_SYMBOLS - 1].real;
    }

    clock_gettime(
        CLOCK_MONOTONIC,
        &end
    );

    double original_time =
        elapsed_seconds(start, end);

    /*
     * ---------------------------------------------------------
     * 2. Packing only
     * ---------------------------------------------------------
     */
    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        pack_bits(
            bits,
            packed_bits,
            N_SYMBOLS
        );

        benchmark_sink +=
            (float)packed_bits[N_SYMBOLS - 1];
    }

    clock_gettime(
        CLOCK_MONOTONIC,
        &end
    );

    double packing_time =
        elapsed_seconds(start, end);

    /*
     * ---------------------------------------------------------
     * 3. Packed mapper only
     * ---------------------------------------------------------
     */
    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        qam256_map_packed(
            packed_bits,
            N_SYMBOLS,
            symbols
        );

        benchmark_sink +=
            symbols[N_SYMBOLS - 1].real;
    }

    clock_gettime(
        CLOCK_MONOTONIC,
        &end
    );

    double packed_mapper_time =
        elapsed_seconds(start, end);

    /*
     * ---------------------------------------------------------
     * 4. Complete packed path
     *
     *     unpacked bits
     *          ↓
     *       packing
     *          ↓
     *    packed mapper
     * ---------------------------------------------------------
     */
    clock_gettime(
        CLOCK_MONOTONIC,
        &start
    );

    for (int iteration = 0;
         iteration < ITERATIONS;
         iteration++) {

        pack_bits(
            bits,
            packed_bits,
            N_SYMBOLS
        );

        qam256_map_packed(
            packed_bits,
            N_SYMBOLS,
            symbols
        );

        benchmark_sink +=
            symbols[N_SYMBOLS - 1].real;
    }

    clock_gettime(
        CLOCK_MONOTONIC,
        &end
    );

    double end_to_end_time =
        elapsed_seconds(start, end);

    /*
     * Throughput.
     */
    double original_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        original_time / 1e6;

    double packing_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        packing_time / 1e6;

    double packed_mapper_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        packed_mapper_time / 1e6;

    double end_to_end_rate =
        ((double)N_SYMBOLS * ITERATIONS) /
        end_to_end_time / 1e6;

    /*
     * Speedups.
     */
    double mapper_speedup =
        original_time /
        packed_mapper_time;

    double end_to_end_speedup =
        original_time /
        end_to_end_time;

    printf("\n");
    printf(
        "256-QAM Packed End-to-End Benchmark\n"
    );
    printf(
        "------------------------------------\n"
    );

    printf(
        "Symbols/iteration: %d\n",
        N_SYMBOLS
    );

    printf(
        "Iterations:        %d\n",
        ITERATIONS
    );

    printf("\n");

    printf(
        "Original mapper:       %.6f s  "
        "%.3f Msymbol/s\n",
        original_time,
        original_rate
    );

    printf(
        "Packing only:           %.6f s  "
        "%.3f Msymbol/s\n",
        packing_time,
        packing_rate
    );

    printf(
        "Packed mapper:          %.6f s  "
        "%.3f Msymbol/s\n",
        packed_mapper_time,
        packed_mapper_rate
    );

    printf(
        "Packed end-to-end:      %.6f s  "
        "%.3f Msymbol/s\n",
        end_to_end_time,
        end_to_end_rate
    );

    printf("\n");

    printf(
        "Mapper-only speedup:    %.3fx\n",
        mapper_speedup
    );

    printf(
        "End-to-end speedup:     %.3fx\n",
        end_to_end_speedup
    );

    printf(
        "Benchmark sink:         %.3f\n",
        benchmark_sink
    );

    free(bits);
    free(packed_bits);
    free(symbols);

    return 0;
}
