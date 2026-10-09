#include <stdio.h>
#include <math.h>

#include "qam.h"


int main(void)
{
    /*
     * 64-QAM decision boundaries:
     *
     *   -6  -4  -2   0   +2  +4  +6
     *
     * Test values immediately below and above
     * every boundary.
     */

    const float normalization = 1.0f / sqrtf(42.0f);
    const float epsilon = 1e-4f;

    float boundaries[] = {
        -6.0f,
        -4.0f,
        -2.0f,
         0.0f,
         2.0f,
         4.0f,
         6.0f
    };

    const size_t n_boundaries =
        sizeof(boundaries) / sizeof(boundaries[0]);

    const size_t n_symbols = n_boundaries * 2;

    qam_symbol_t symbols[14];
    unsigned char recovered_bits[14 * 6];


    /*
     * Create values immediately below and above
     * each decision boundary.
     *
     * Q component is fixed at +1.
     */
    for (size_t i = 0; i < n_boundaries; i++) {

        float boundary = boundaries[i];

        symbols[2 * i].real =
            (boundary - epsilon) * normalization;

        symbols[2 * i].imag =
            1.0f * normalization;

        symbols[2 * i + 1].real =
            (boundary + epsilon) * normalization;

        symbols[2 * i + 1].imag =
            1.0f * normalization;
    }


    /*
     * Demap all test symbols.
     */
    int result = qam64_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {

        printf(
            "64-QAM boundary demapping failed: %d\n",
            result
        );

        return 1;
    }


    /*
     * Expected bit mappings for the I component.
     *
     * Below -6  -> -7 -> 100
     * Above -6  -> -5 -> 101
     *
     * Below -4  -> -5 -> 101
     * Above -4  -> -3 -> 110
     *
     * Below -2  -> -3 -> 110
     * Above -2  -> -1 -> 111
     *
     * Below  0  -> -1 -> 111
     * Above  0  -> +1 -> 011
     *
     * Below +2  -> +1 -> 011
     * Above +2  -> +3 -> 010
     *
     * Below +4  -> +3 -> 010
     * Above +4  -> +5 -> 001
     *
     * Below +6  -> +5 -> 001
     * Above +6  -> +7 -> 000
     */
    unsigned char expected_i_bits[] = {
        1, 0, 0,
        1, 0, 1,

        1, 0, 1,
        1, 1, 0,

        1, 1, 0,
        1, 1, 1,

        1, 1, 1,
        0, 1, 1,

        0, 1, 1,
        0, 1, 0,

        0, 1, 0,
        0, 0, 1,

        0, 0, 1,
        0, 0, 0
    };


    /*
     * Q component is fixed at +1.
     *
     * +1 corresponds to:
     *
     *   011
     */
    unsigned char expected_q_bits[] = {
        0, 1, 1
    };


    int correct = 1;


    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char expected_b0 =
            expected_i_bits[3 * i];

        unsigned char expected_b2 =
            expected_i_bits[3 * i + 1];

        unsigned char expected_b4 =
            expected_i_bits[3 * i + 2];


        unsigned char expected_b1 =
            expected_q_bits[0];

        unsigned char expected_b3 =
            expected_q_bits[1];

        unsigned char expected_b5 =
            expected_q_bits[2];


        unsigned char actual_b0 =
            recovered_bits[6 * i];

        unsigned char actual_b1 =
            recovered_bits[6 * i + 1];

        unsigned char actual_b2 =
            recovered_bits[6 * i + 2];

        unsigned char actual_b3 =
            recovered_bits[6 * i + 3];

        unsigned char actual_b4 =
            recovered_bits[6 * i + 4];

        unsigned char actual_b5 =
            recovered_bits[6 * i + 5];


        size_t boundary_index = i / 2;

        const char *side =
            (i % 2 == 0) ? "below" : "above";


        printf(
            "Boundary %+.0f %s: "
            "expected [%u %u %u %u %u %u], "
            "got [%u %u %u %u %u %u]\n",
            boundaries[boundary_index],
            side,
            expected_b0,
            expected_b1,
            expected_b2,
            expected_b3,
            expected_b4,
            expected_b5,
            actual_b0,
            actual_b1,
            actual_b2,
            actual_b3,
            actual_b4,
            actual_b5
        );


        if (actual_b0 != expected_b0 ||
            actual_b1 != expected_b1 ||
            actual_b2 != expected_b2 ||
            actual_b3 != expected_b3 ||
            actual_b4 != expected_b4 ||
            actual_b5 != expected_b5) {

            correct = 0;
        }
    }


    if (correct) {

        printf(
            "\n64-QAM C boundary correctness: PASS\n"
        );

        return 0;
    }


    printf(
        "\n64-QAM C boundary correctness: FAIL\n"
    );

    return 1;
}
