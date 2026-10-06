/*
 * 5G NR PDSCH bit scrambling - scalar C implementation.
 *
 * Reference:
 *     3GPP TS 38.211
 *     Section 5.2.1  - Pseudo-random sequence generation
 *     Section 7.3.1.1 - PDSCH scrambling
 *
 * This implementation prioritizes correctness and readability.
 * It intentionally uses one byte per bit and no SIMD/optimization.
 */

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>

#define NR_SCRAMBLING_NC 1600U


/*
 * Calculate the PDSCH scrambling initialization value.
 *
 * c_init = n_RNTI * 2^15 + q * 2^14 + n_ID
 */
uint32_t calculate_c_init(
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    return ((uint32_t)n_rnti << 15)
         + ((uint32_t)q << 14)
         + (uint32_t)n_id;
}


/*
 * Generate the 5G NR Gold scrambling sequence.
 *
 * output must point to an array containing at least 'length' bytes.
 *
 * Each output byte contains one bit:
 *
 *     output[i] = 0 or 1
 */
void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
)
{
    size_t total_length = NR_SCRAMBLING_NC + length;

    uint8_t *x1;
    uint8_t *x2;


    /*
     * x1 and x2 are dynamically allocated because the total sequence
     * length depends on the requested input size.
     */
     x1 = (uint8_t *)malloc(total_length * sizeof(uint8_t));
     x2 = (uint8_t *)malloc(total_length * sizeof(uint8_t));

     if (x1 == NULL || x2 == NULL) {
     free(x1);
     free(x2);
     return;
     }


    /*
     * Initialize x1.
     *
     * x1(0) = 1
     * x1(1)...x1(30) = 0
     */
    for (size_t i = 0; i < total_length; i++) {
    x1[i] = 0;
    }

    x1[0] = 1;


    /*
     * Initialize x2 using c_init.
     */
    for (size_t i = 0; i < 31; i++) {
        x2[i] = (uint8_t)((c_init >> i) & 1U);
    }


    /*
     * Generate x1 and x2.
     */
    for (size_t n = 0; n < total_length - 31; n++) {

        x1[n + 31] =
            x1[n + 3] ^
            x1[n];

        x2[n + 31] =
            x2[n + 3] ^
            x2[n + 2] ^
            x2[n + 1] ^
            x2[n];
    }


    /*
     * Generate Gold sequence after the N_C offset.
     */
    for (size_t n = 0; n < length; n++) {

        output[n] =
            x1[n + NR_SCRAMBLING_NC] ^
            x2[n + NR_SCRAMBLING_NC];
    }


    free(x1);
    free(x2);
}


/*
 * Scramble bits using the generated Gold sequence.
 *
 * input and output may point to different arrays.
 *
 * Each byte represents one bit and must contain 0 or 1.
 */
void scramble_bits(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    uint32_t c_init =
        calculate_c_init(
            n_rnti,
            n_id,
            q
        );


    uint8_t *sequence =
        (uint8_t *)malloc(length * sizeof(uint8_t));

    if (sequence == NULL) {
        return;
    }


    generate_gold_sequence(
        sequence,
        length,
        c_init
    );


    for (size_t i = 0; i < length; i++) {
        output[i] = input[i] ^ sequence[i];
    }


    free(sequence);
}
