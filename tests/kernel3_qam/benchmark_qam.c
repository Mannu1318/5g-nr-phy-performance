#include "qam.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#define N_SYMBOLS 1000000
#define ITERATIONS 100

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

static volatile float benchmark_sink;

static void benchmark_qpsk(void)
{
    const size_t bits_per_symbol = 2;
    const size_t n_bits = N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits * sizeof(unsigned char));

    unsigned char *recovered =
        malloc(n_bits * sizeof(unsigned char));

    qam_symbol_t *symbols =
        malloc(N_SYMBOLS * sizeof(qam_symbol_t));

    if (!bits || !recovered || !symbols) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    fill_bits(bits, n_bits);

    /* Warm-up */
    qpsk_map(bits, n_bits, symbols);
    qpsk_demap(symbols, N_SYMBOLS, recovered);

    struct timespec start, end;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iter = 0; iter < ITERATIONS; iter++) {

        qpsk_map(
            bits,
            n_bits,
            symbols
        );

        qpsk_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real +
        symbols[N_SYMBOLS - 1].imag +
        recovered[0];

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double total_bits =
        (double)n_bits * ITERATIONS;

    printf(
        "QPSK      %.6f s  %.3f Msymbol/s  %.3f Mbit/s\n",
        seconds,
        total_symbols / seconds / 1e6,
        total_bits / seconds / 1e6
    );

    free(bits);
    free(recovered);
    free(symbols);
}


static void benchmark_qam16(void)
{
    const size_t bits_per_symbol = 4;
    const size_t n_bits = N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits * sizeof(unsigned char));

    unsigned char *recovered =
        malloc(n_bits * sizeof(unsigned char));

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

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iter = 0; iter < ITERATIONS; iter++) {

        qam16_map(
            bits,
            n_bits,
            symbols
        );

        qam16_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real +
        symbols[N_SYMBOLS - 1].imag +
        recovered[0];

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double total_bits =
        (double)n_bits * ITERATIONS;

    printf(
        "16-QAM    %.6f s  %.3f Msymbol/s  %.3f Mbit/s\n",
        seconds,
        total_symbols / seconds / 1e6,
        total_bits / seconds / 1e6
    );

    free(bits);
    free(recovered);
    free(symbols);
}


static void benchmark_qam64(void)
{
    const size_t bits_per_symbol = 6;
    const size_t n_bits = N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits * sizeof(unsigned char));

    unsigned char *recovered =
        malloc(n_bits * sizeof(unsigned char));

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

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iter = 0; iter < ITERATIONS; iter++) {

        qam64_map(
            bits,
            n_bits,
            symbols
        );

        qam64_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real +
        symbols[N_SYMBOLS - 1].imag +
        recovered[0];

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double total_bits =
        (double)n_bits * ITERATIONS;

    printf(
        "64-QAM    %.6f s  %.3f Msymbol/s  %.3f Mbit/s\n",
        seconds,
        total_symbols / seconds / 1e6,
        total_bits / seconds / 1e6
    );

    free(bits);
    free(recovered);
    free(symbols);
}


static void benchmark_qam256(void)
{
    const size_t bits_per_symbol = 8;
    const size_t n_bits = N_SYMBOLS * bits_per_symbol;

    unsigned char *bits =
        malloc(n_bits * sizeof(unsigned char));

    unsigned char *recovered =
        malloc(n_bits * sizeof(unsigned char));

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

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int iter = 0; iter < ITERATIONS; iter++) {

        qam256_map(
            bits,
            n_bits,
            symbols
        );

        qam256_demap(
            symbols,
            N_SYMBOLS,
            recovered
        );
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double seconds =
        elapsed_seconds(start, end);

    benchmark_sink =
        symbols[0].real +
        symbols[N_SYMBOLS - 1].imag +
        recovered[0];

    double total_symbols =
        (double)N_SYMBOLS * ITERATIONS;

    double total_bits =
        (double)n_bits * ITERATIONS;

    printf(
        "256-QAM   %.6f s  %.3f Msymbol/s  %.3f Mbit/s\n",
        seconds,
        total_symbols / seconds / 1e6,
        total_bits / seconds / 1e6
    );

    free(bits);
    free(recovered);
    free(symbols);
}


int main(void)
{
    printf(
        "Kernel 3 QAM Mapping/Demapping Benchmark\n"
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
