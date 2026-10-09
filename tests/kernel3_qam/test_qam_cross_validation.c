#include "qam.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BITS 2048
#define MAX_SYMBOLS 256

static void print_symbols(
    const qam_symbol_t *symbols,
    size_t n_symbols
)
{
    for (size_t i = 0; i < n_symbols; i++) {
        printf("%.9f %.9f\n",
               symbols[i].real,
               symbols[i].imag);
    }
}

static void print_bits(
    const unsigned char *bits,
    size_t n_bits
)
{
    for (size_t i = 0; i < n_bits; i++) {
        printf("%u", bits[i]);
    }

    printf("\n");
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr,
                "Usage: %s <qpsk|qam16|qam64|qam256>\n",
                argv[0]);
        return 1;
    }

    const char *mode = argv[1];

    size_t bits_per_symbol;

    if (strcmp(mode, "qpsk") == 0) {
        bits_per_symbol = 2;
    } else if (strcmp(mode, "qam16") == 0) {
        bits_per_symbol = 4;
    } else if (strcmp(mode, "qam64") == 0) {
        bits_per_symbol = 6;
    } else if (strcmp(mode, "qam256") == 0) {
        bits_per_symbol = 8;
    } else {
        fprintf(stderr, "Unknown modulation: %s\n", mode);
        return 1;
    }

    /*
     * Use a deterministic test pattern.
     *
     * The Python side will generate the same pattern.
     */
    const size_t n_symbols = 16;
    const size_t n_bits = n_symbols * bits_per_symbol;

    unsigned char bits[MAX_BITS];
    unsigned char recovered_bits[MAX_BITS];
    qam_symbol_t symbols[MAX_SYMBOLS];

    for (size_t i = 0; i < n_bits; i++) {
        bits[i] = (unsigned char)((i * 7 + 3) % 2);
    }

    int status;

    if (strcmp(mode, "qpsk") == 0) {

        status = qpsk_map(
            bits,
            n_bits,
            symbols
        );

    } else if (strcmp(mode, "qam16") == 0) {

        status = qam16_map(
            bits,
            n_bits,
            symbols
        );

    } else if (strcmp(mode, "qam64") == 0) {

        status = qam64_map(
            bits,
            n_bits,
            symbols
        );

    } else {

        status = qam256_map(
            bits,
            n_bits,
            symbols
        );
    }

    if (status != 0) {
        fprintf(stderr,
                "C mapper failed with status %d\n",
                status);
        return 1;
    }

    printf("SYMBOLS\n");

    print_symbols(
        symbols,
        n_symbols
    );

    if (strcmp(mode, "qpsk") == 0) {

        status = qpsk_demap(
            symbols,
            n_symbols,
            recovered_bits
        );

    } else if (strcmp(mode, "qam16") == 0) {

        status = qam16_demap(
            symbols,
            n_symbols,
            recovered_bits
        );

    } else if (strcmp(mode, "qam64") == 0) {

        status = qam64_demap(
            symbols,
            n_symbols,
            recovered_bits
        );

    } else {

        status = qam256_demap(
            symbols,
            n_symbols,
            recovered_bits
        );
    }

    if (status != 0) {
        fprintf(stderr,
                "C demapper failed with status %d\n",
                status);
        return 1;
    }

    printf("BITS\n");

    print_bits(
        recovered_bits,
        n_bits
    );

    return 0;
}
