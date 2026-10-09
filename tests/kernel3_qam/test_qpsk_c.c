#include <stdio.h>

#include "qam.h"


int main(void)
{
    unsigned char input_bits[] = {
        0, 0,
        0, 1,
        1, 0,
        1, 1
    };

    const size_t n_bits = sizeof(input_bits) / sizeof(input_bits[0]);
    const size_t n_symbols = n_bits / 2;

    qam_symbol_t symbols[4];
    unsigned char recovered_bits[8];


    /* Map bits to QPSK symbols. */
    int result = qpsk_map(
        input_bits,
        n_bits,
        symbols
    );

    if (result != 0) {
        printf("QPSK mapping failed: %d\n", result);
        return 1;
    }


    /* Print mapped symbols. */
    printf("QPSK symbols:\n");

    for (size_t i = 0; i < n_symbols; i++) {
        printf(
            "  (%f, %f)\n",
            symbols[i].real,
            symbols[i].imag
        );
    }


    /* Demap symbols back to bits. */
    result = qpsk_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {
        printf("QPSK demapping failed: %d\n", result);
        return 1;
    }


    /* Compare original and recovered bits. */
    int correct = 1;

    for (size_t i = 0; i < n_bits; i++) {

        if (input_bits[i] != recovered_bits[i]) {
            correct = 0;
            break;
        }
    }


    printf("\nInput bits:     ");

    for (size_t i = 0; i < n_bits; i++) {
        printf("%u ", input_bits[i]);
    }

    printf("\nRecovered bits: ");

    for (size_t i = 0; i < n_bits; i++) {
        printf("%u ", recovered_bits[i]);
    }

    printf("\n");


    if (correct) {
        printf("\nQPSK C correctness: PASS\n");
        return 0;
    }

    printf("\nQPSK C correctness: FAIL\n");
    return 1;
}
