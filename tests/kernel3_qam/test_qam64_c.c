#include <stdio.h>

#include "qam.h"


int main(void)
{
    /*
     * Generate all 64 possible 6-bit patterns.
     *
     * 2^6 = 64
     *
     * Each pattern represents one 64-QAM constellation point.
     */
    unsigned char input_bits[64 * 6];

    for (size_t pattern = 0; pattern < 64; pattern++) {

        for (size_t bit = 0; bit < 6; bit++) {

            /*
             * Store bits MSB first.
             */
            input_bits[pattern * 6 + bit] =
                (pattern >> (5 - bit)) & 1;
        }
    }


    const size_t n_bits =
        sizeof(input_bits) / sizeof(input_bits[0]);

    const size_t n_symbols = n_bits / 6;


    qam_symbol_t symbols[64];

    unsigned char recovered_bits[64 * 6];


    /*
     * Map all 64 patterns to 64-QAM symbols.
     */
    int result = qam64_map(
        input_bits,
        n_bits,
        symbols
    );

    if (result != 0) {

        printf(
            "64-QAM mapping failed: %d\n",
            result
        );

        return 1;
    }


    /*
     * Print all 64 constellation points.
     */
    printf("64-QAM symbols:\n");

    for (size_t i = 0; i < n_symbols; i++) {

        printf(
            "  %2zu: (%f, %f)\n",
            i,
            symbols[i].real,
            symbols[i].imag
        );
    }


    /*
     * Demap all symbols back to bits.
     */
    result = qam64_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {

        printf(
            "64-QAM demapping failed: %d\n",
            result
        );

        return 1;
    }


    /*
     * Compare every input bit with every
     * recovered bit.
     */
    int correct = 1;

    for (size_t i = 0; i < n_bits; i++) {

        if (input_bits[i] != recovered_bits[i]) {

            printf(
                "Mismatch at bit %zu: "
                "expected %u, got %u\n",
                i,
                input_bits[i],
                recovered_bits[i]
            );

            correct = 0;

            break;
        }
    }


    /*
     * Print complete input and recovered sequences.
     */
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

        printf(
            "\n64-QAM C correctness: PASS\n"
        );

        return 0;
    }


    printf(
        "\n64-QAM C correctness: FAIL\n"
    );

    return 1;
}
