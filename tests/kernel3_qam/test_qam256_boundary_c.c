#include <math.h>
#include <stdio.h>

#include "qam.h"

int main(void)
{
    /*
     * 256-QAM decision boundaries:
     *
     * -14, -12, -10, -8, -6, -4, -2,
     *   0,
     * +2, +4, +6, +8, +10, +12, +14
     */
    const float boundaries[] = {
        -14.0f,
        -12.0f,
        -10.0f,
        -8.0f,
        -6.0f,
        -4.0f,
        -2.0f,
         0.0f,
         2.0f,
         4.0f,
         6.0f,
         8.0f,
        10.0f,
        12.0f,
        14.0f
    };

    const size_t n_boundaries =
        sizeof(boundaries) / sizeof(boundaries[0]);

    const float normalization =
        1.0f / sqrtf(170.0f);

    const float epsilon = 0.0001f;

    int all_correct = 1;

    /*
     * Test values immediately below and above
     * every decision boundary.
     */
    for (size_t i = 0; i < n_boundaries; i++) {

        float below = boundaries[i] - epsilon;
        float above = boundaries[i] + epsilon;

        qam_symbol_t below_symbol;
        qam_symbol_t above_symbol;

        unsigned char below_bits[8];
        unsigned char above_bits[8];

        /*
         * Put the test value on the I axis.
         * Keep Q at the +1 constellation level.
         */
        below_symbol.real =
            below * normalization;

        below_symbol.imag =
            1.0f * normalization;

        above_symbol.real =
            above * normalization;

        above_symbol.imag =
            1.0f * normalization;

        qam256_demap(
            &below_symbol,
            1,
            below_bits
        );

        qam256_demap(
            &above_symbol,
            1,
            above_bits
        );

        printf(
            "Boundary %+5.0f below: "
            "I=%+9.4f -> [%u %u %u %u %u %u %u %u]\n",
            boundaries[i],
            below,
            below_bits[0],
            below_bits[1],
            below_bits[2],
            below_bits[3],
            below_bits[4],
            below_bits[5],
            below_bits[6],
            below_bits[7]
        );

        printf(
            "Boundary %+5.0f above: "
            "I=%+9.4f -> [%u %u %u %u %u %u %u %u]\n",
            boundaries[i],
            above,
            above_bits[0],
            above_bits[1],
            above_bits[2],
            above_bits[3],
            above_bits[4],
            above_bits[5],
            above_bits[6],
            above_bits[7]
        );

        /*
         * The important property is that crossing
         * a decision boundary changes the I-axis
         * decision to the adjacent constellation level.
         *
         * Therefore the four I bits must change
         * between below and above.
         *
         * Q bits should remain:
         *
         *   0111
         *
         * because Q = +1.
         */

        if (below_bits[1] != 0 ||
            below_bits[3] != 1 ||
            below_bits[5] != 1 ||
            below_bits[7] != 1) {

            printf(
                "ERROR: Q-axis decision changed below boundary\n"
            );

            all_correct = 0;
        }

        if (above_bits[1] != 0 ||
            above_bits[3] != 1 ||
            above_bits[5] != 1 ||
            above_bits[7] != 1) {

            printf(
                "ERROR: Q-axis decision changed above boundary\n"
            );

            all_correct = 0;
        }

        /*
         * At a boundary, the adjacent constellation
         * levels must produce different I decisions.
         */
        if (below_bits[0] == above_bits[0] &&
            below_bits[2] == above_bits[2] &&
            below_bits[4] == above_bits[4] &&
            below_bits[6] == above_bits[6]) {

            printf(
                "ERROR: I-axis decision did not change "
                "across boundary %+5.0f\n",
                boundaries[i]
            );

            all_correct = 0;
        }
    }

    if (all_correct) {

        printf(
            "\n256-QAM C boundary correctness: PASS\n"
        );

        return 0;
    }

    printf(
        "\n256-QAM C boundary correctness: FAIL\n"
    );

    return 1;
}
