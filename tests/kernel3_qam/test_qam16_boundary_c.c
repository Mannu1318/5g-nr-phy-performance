#include <stdio.h>
#include <math.h>

#include "qam.h"


int main(void)
{
    /*
     * 16-QAM decision boundaries:
     *
     *     -2       0       +2
     *
     * We test values immediately below and above
     * each boundary.
     */

    const float normalization = 1.0f / sqrtf(10.0f);
    const float epsilon = 1e-4f;

    float test_values[] = {
        -2.0f - epsilon,
        -2.0f + epsilon,

        -epsilon,
        epsilon,

        2.0f - epsilon,
        2.0f + epsilon
    };

    const size_t n_symbols =
        sizeof(test_values) / sizeof(test_values[0]);

    qam_symbol_t symbols[6];
    unsigned char recovered_bits[24];


    /*
     * Put the test value on the I component.
     *
     * Q component is fixed at +1.
     */
    for (size_t i = 0; i < n_symbols; i++) {

        symbols[i].real =
            test_values[i] * normalization;

        symbols[i].imag =
            1.0f * normalization;
    }


    /*
     * Demap the symbols.
     */
    int result = qam16_demap(
        symbols,
        n_symbols,
        recovered_bits
    );

    if (result != 0) {
        printf(
            "16-QAM boundary demapping failed: %d\n",
            result
        );

        return 1;
    }


    /*
     * Expected I-component bits.
     *
     * Below -2  -> -3 -> 10
     * Above -2  -> -1 -> 11
     *
     * Below  0  -> -1 -> 11
     * Above  0  -> +1 -> 01
     *
     * Below +2  -> +1 -> 01
     * Above +2  -> +3 -> 00
     */
    unsigned char expected_i_bits[] = {
        1, 0,
        1, 1,

        1, 1,
        0, 1,

        0, 1,
        0, 0
    };


    /*
     * Q component is fixed at +1,
     * which corresponds to bits 01.
     */
    unsigned char expected_q_bits[] = {
        0, 1
    };


    int correct = 1;

    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char expected_b0 =
            expected_i_bits[2 * i];

        unsigned char expected_b2 =
            expected_i_bits[2 * i + 1];

        unsigned char expected_b1 =
            expected_q_bits[0];

        unsigned char expected_b3 =
            expected_q_bits[1];


        unsigned char actual_b0 =
            recovered_bits[4 * i];

        unsigned char actual_b1 =
            recovered_bits[4 * i + 1];

        unsigned char actual_b2 =
            recovered_bits[4 * i + 2];

        unsigned char actual_b3 =
            recovered_bits[4 * i + 3];


        printf(
            "Test %zu: I=%+.6f -> "
            "expected [%u %u %u %u], "
            "got [%u %u %u %u]\n",
            i + 1,
            test_values[i],
            expected_b0,
            expected_b1,
            expected_b2,
            expected_b3,
            actual_b0,
            actual_b1,
            actual_b2,
            actual_b3
        );


        if (actual_b0 != expected_b0 ||
            actual_b1 != expected_b1 ||
            actual_b2 != expected_b2 ||
            actual_b3 != expected_b3) {

            correct = 0;
        }
    }


    if (correct) {

        printf(
            "\n16-QAM C boundary correctness: PASS\n"
        );

        return 0;
    }


    printf(
        "\n16-QAM C boundary correctness: FAIL\n"
    );

    return 1;
}
