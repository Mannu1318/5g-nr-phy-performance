#include <stdio.h>

#include "qam.h"

int main(void)
{
    /*
     * 256-QAM has 256 possible 8-bit input patterns.
     */
    unsigned char input_bits[256 * 8];
    unsigned char recovered_bits[256 * 8];

    qam_symbol_t symbols[256];

    /*
     * Generate all possible 8-bit patterns.
     *
     * Pattern 0   -> 00000000
     * Pattern 1   -> 00000001
     * ...
     * Pattern 255 -> 11111111
     */
    for (int pattern = 0; pattern < 256; pattern++) {

        for (int bit = 0; bit < 8; bit++) {

            input_bits[pattern * 8 + bit] =
                (pattern >> (7 - bit)) & 1;
        }
    }

    const size_t n_bits = sizeof(input_bits)
                        / sizeof(input_bits[0]);

    const size_t n_symbols = n_bits / 8;

    /*
     * Test mapping.
     */
    int result = qam256_map(
        input_bits,
        n_bits,
        symbols
    );

    if (result != 0) {
        printf(
            "256-QAM mapping failed: %d\n",
            result
        );

        return 1;
    }

    /*
     * Print all 256 constellation points.
     */
    printf("256-QAM symbols:\n");

    for (size_t i = 0; i < n_symbols; i++) {

        printf(
            "%3zu: (%f, %f)\n",
            i,
            symbols[i].real,
            symbols[i].imag
        );
    }

    /*
     * Test demapping.
     */
    result = qam256_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {
        printf(
            "256-QAM demapping failed: %d\n",
            result
        );

        return 1;
    }

    /*
     * Compare every input bit with the recovered bit.
     */
    int correct = 1;

    for (size_t i = 0; i < n_bits; i++) {

        if (input_bits[i] != recovered_bits[i]) {

            printf(
                "\nMismatch at bit %zu: "
                "input=%u recovered=%u\n",
                i,
                input_bits[i],
                recovered_bits[i]
            );

            correct = 0;
            break;
        }
    }

    /*
     * Print a compact comparison of the complete bitstream.
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
            "\n256-QAM C exhaustive correctness: PASS\n"
        );

        return 0;
    }

    printf(
        "\n256-QAM C exhaustive correctness: FAIL\n"
    );

    return 1;
}
