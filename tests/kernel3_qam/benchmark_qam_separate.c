#include "qam.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N_SYMBOLS 1000000
#define ITERATIONS 100

static volatile float benchmark_sink;

static double elapsed_seconds(
    struct timespec start,
    struct timespec end
)
{
    return (double)(end.tv_sec - start.tv_sec)
         + (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}

static void fill_bits(
    unsigned char *bits,
    size_t n_bits
)
{
    for (size_t i = 0; i < n_bits; i++) {
        bits[i] = (unsigned char)((i * 7 + 3) & 1);
    }
}

static void print_results(
    const char *name,
    const char *operation,
    double seconds,
    double total_symbols,
    double total_bits
)
{
    printf(
        "%-8s %-7s %.6f s  %.3f Msymbol/s  %.3f Mbit/s\n",
        name,
        operation,
        seconds,
        total_symbols / seconds / 1e6,
        total_bits / seconds / 1e6
    );
}


/* --------------------------------------------------------- */
/* QPSK                                                       */
/* --------------------------------------------------------- */

static void benchmark_qpsk(void)
{
    const size_t bits_per_symbol = 2;
    const size_t n_bits =
        N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits);

    unsigned char *recovered =
        malloc(n_bits);

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !recovered || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    fill_bits(bits, n_bits);

    qpsk_map(bits, n_bits, symbols);
    qpsk_demap(symbols, N_SYMBOLS, recovered);

    struct timespec start, end;

    /* Mapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qpsk_map(
            bits,
            n_bits,
            symbols
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double map_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real;

    print_results(
        "QPSK",
        "map",
        map_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    /* Demapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qpsk_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double demap_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        recovered[0];

    print_results(
        "QPSK",
        "demap",
        demap_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    free(bits);
    free(recovered);
    free(symbols);
}


/* --------------------------------------------------------- */
/* 16-QAM                                                     */
/* --------------------------------------------------------- */

static void benchmark_qam16(void)
{
    const size_t bits_per_symbol = 4;
    const size_t n_bits =
        N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits);

    unsigned char *recovered =
        malloc(n_bits);

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !recovered || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    fill_bits(bits, n_bits);

    qam16_map(bits, n_bits, symbols);
    qam16_demap(symbols, N_SYMBOLS, recovered);

    struct timespec start, end;

    /* Mapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam16_map(
            bits,
            n_bits,
            symbols
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double map_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real;

    print_results(
        "16-QAM",
        "map",
        map_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    /* Demapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam16_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double demap_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        recovered[0];

    print_results(
        "16-QAM",
        "demap",
        demap_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    free(bits);
    free(recovered);
    free(symbols);
}


/* --------------------------------------------------------- */
/* 64-QAM                                                     */
/* --------------------------------------------------------- */

static void benchmark_qam64(void)
{
    const size_t bits_per_symbol = 6;
    const size_t n_bits =
        N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits);

    unsigned char *recovered =
        malloc(n_bits);

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !recovered || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    fill_bits(bits, n_bits);

    qam64_map(bits, n_bits, symbols);
    qam64_demap(symbols, N_SYMBOLS, recovered);

    struct timespec start, end;

    /* Mapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam64_map(
            bits,
            n_bits,
            symbols
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double map_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real;

    print_results(
        "64-QAM",
        "map",
        map_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    /* Demapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam64_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double demap_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        recovered[0];

    print_results(
        "64-QAM",
        "demap",
        demap_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    free(bits);
    free(recovered);
    free(symbols);
}


/* --------------------------------------------------------- */
/* 256-QAM                                                    */
/* --------------------------------------------------------- */

static void benchmark_qam256(void)
{
    const size_t bits_per_symbol = 8;
    const size_t n_bits =
        N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits);

    unsigned char *recovered =
        malloc(n_bits);

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !recovered || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    fill_bits(bits, n_bits);

    qam256_map(bits, n_bits, symbols);
    qam256_demap(symbols, N_SYMBOLS, recovered);

    struct timespec start, end;

    /* Mapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam256_map(
            bits,
            n_bits,
            symbols
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double map_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real;

    print_results(
        "256-QAM",
        "map",
        map_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    /* Demapping */
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        qam256_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double demap_seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        recovered[0];

    print_results(
        "256-QAM",
        "demap",
        demap_seconds,
        (double)N_SYMBOLS * ITERATIONS,
        (double)n_bits * ITERATIONS
    );

    free(bits);
    free(recovered);
    free(symbols);
}


int main(void)
{
    printf(
        "Kernel 3 Separate Mapping/Demapping Benchmark\n"
    );

    printf(
        "Symbols/iteration: %d\n"
        "Iterations:        %d\n\n",
        N_SYMBOLS,
        ITERATIONS
    );

    benchmark_qpsk();
    benchmark_qam16();
    benchmark_qam64();
    benchmark_qam256();

    return 0;
}
