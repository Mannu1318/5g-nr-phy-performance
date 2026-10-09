#include <stdio.h>

#include "qam.h"


int main(void)
{
    /*
     * All 16 possible 16-QAM input patterns.
     */
    unsigned char input_bits[] = {
        0, 0, 0, 0,
        0, 0, 0, 1,
        0, 0, 1, 0,
        0, 0, 1, 1,

        0, 1, 0, 0,
        0, 1, 0, 1,
        0, 1, 1, 0,
        0, 1, 1, 1,

        1, 0, 0, 0,
        1, 0, 0, 1,
        1, 0, 1, 0,
        1, 0, 1, 1,

        1, 1, 0, 0,
        1, 1, 0, 1,
        1, 1, 1, 0,
        1, 1, 1, 1
    };

    const size_t n_bits =
        sizeof(input_bits) / sizeof(input_bits[0]);

    const size_t n_symbols = n_bits / 4;

    qam_symbol_t symbols[16];

    unsigned char recovered_bits[64];


    /*
     * Map bits to 16-QAM symbols.
     */
    int result = qam16_map(
        input_bits,
        n_bits,
        symbols
    );

    if (result != 0) {
        printf("16-QAM mapping failed: %d\n", result);
        return 1;
    }


    /*
     * Print constellation points.
     */
    printf("16-QAM symbols:\n");

    for (size_t i = 0; i < n_symbols; i++) {

        printf(
            "  (%f, %f)\n",
            symbols[i].real,
            symbols[i].imag
        );
    }


    /*
     * Demap symbols back to bits.
     */
    result = qam16_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {
        printf("16-QAM demapping failed: %d\n", result);
        return 1;
    }


    /*
     * Compare original and recovered bits.
     */
    int correct = 1;

    for (size_t i = 0; i < n_bits; i++) {

        if (input_bits[i] != recovered_bits[i]) {

            correct = 0;

            printf(
                "Mismatch at bit %zu: "
                "expected %u, got %u\n",
                i,
                input_bits[i],
                recovered_bits[i]
            );

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

        printf("\n16-QAM C correctness: PASS\n");
        return 0;
    }

    printf("\n16-QAM C correctness: FAIL\n");
    return 1;
}
