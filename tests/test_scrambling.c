/*
 * Correctness tests for the 5G NR PDSCH scrambling C implementation.
 *
 * The expected values in this file were generated from the
 * Python reference implementation.
 */

#include <stdint.h>
#include <stdio.h>
#include <stddef.h>


#define TEST_LENGTH 16
#define NUM_TEST_CASES 4
#define LONG_TEST_LENGTH 10000


uint32_t calculate_c_init(
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);


void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);


void scramble_bits(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);


/*
 * Compare two bit arrays.
 *
 * Returns:
 *     1 if the arrays match
 *     0 if they differ
 */
static int compare_bits(
    const uint8_t *actual,
    const uint8_t *expected,
    size_t length
)
{
    for (size_t i = 0; i < length; i++) {

        if (actual[i] != expected[i]) {

            printf(
                "Mismatch at index %zu: "
                "actual=%u expected=%u\n",
                i,
                actual[i],
                expected[i]
            );

            return 0;
        }
    }

    return 1;
}


int main(void)
{
    /*
     * Test Case 1
     *
     * Baseline configuration:
     *
     * n_RNTI = 0x1234
     * n_ID   = 0x0155
     * q      = 0
     */
    {
        const uint16_t n_rnti = 0x1234;
        const uint16_t n_id = 0x0155;
        const uint8_t q = 0;

        const uint8_t input[8] = {
            1, 0, 1, 1, 0, 0, 1, 0
        };

        const uint8_t expected_sequence[8] = {
            0, 1, 1, 1, 0, 0, 0, 1
        };

        const uint8_t expected_scrambled[8] = {
            1, 1, 0, 0, 0, 0, 1, 1
        };

        uint8_t sequence[8];
        uint8_t scrambled[8];
        uint8_t recovered[8];

        uint32_t c_init = calculate_c_init(
            n_rnti,
            n_id,
            q
        );

        printf("Test Case 1\n");

        if (c_init != 0x091A0155U) {
            printf("FAIL: c_init\n");
            printf(
                "Expected: 0x091A0155\n"
                "Actual  : 0x%08X\n",
                c_init
            );

            return 1;
        }

        generate_gold_sequence(
            sequence,
            8,
            c_init
        );

        if (!compare_bits(
            sequence,
            expected_sequence,
            8
        )) {
            printf("FAIL: Gold sequence\n");
            return 1;
        }

        scramble_bits(
            input,
            scrambled,
            8,
            n_rnti,
            n_id,
            q
        );

        if (!compare_bits(
            scrambled,
            expected_scrambled,
            8
        )) {
            printf("FAIL: scrambled output\n");
            return 1;
        }

        /*
         * Descrambling:
         * applying the same XOR operation again
         * must recover the original input.
         */
        scramble_bits(
            scrambled,
            recovered,
            8,
            n_rnti,
            n_id,
            q
        );

        if (!compare_bits(
            recovered,
            input,
            8
        )) {
            printf("FAIL: descrambling\n");
            return 1;
        }

        printf("PASS: descrambling\n");
        printf("PASS\n\n");
    }


    /*
     * Test Case 2
     *
     * Same RNTI and n_ID, but q = 1.
     */
    {
        const uint16_t n_rnti = 0x1234;
        const uint16_t n_id = 0x0155;
        const uint8_t q = 1;

        const uint8_t input[8] = {
            1, 0, 1, 1, 0, 0, 1, 0
        };

        const uint8_t expected_sequence[8] = {
            0, 1, 0, 1, 0, 0, 1, 1
        };

        const uint8_t expected_scrambled[8] = {
            1, 1, 1, 0, 0, 0, 0, 1
        };

        uint8_t sequence[8];
        uint8_t scrambled[8];

        uint32_t c_init = calculate_c_init(
            n_rnti,
            n_id,
            q
        );

        printf("Test Case 2\n");

        if (c_init != 0x091A4155U) {
            printf("FAIL: c_init\n");
            printf(
                "Expected: 0x091A4155\n"
                "Actual  : 0x%08X\n",
                c_init
            );

            return 1;
        }

        generate_gold_sequence(
            sequence,
            8,
            c_init
        );

        if (!compare_bits(
            sequence,
            expected_sequence,
            8
        )) {
            printf("FAIL: Gold sequence\n");
            return 1;
        }

        scramble_bits(
            input,
            scrambled,
            8,
            n_rnti,
            n_id,
            q
        );

        if (!compare_bits(
            scrambled,
            expected_scrambled,
            8
        )) {
            printf("FAIL: scrambled output\n");
            return 1;
        }

        printf("PASS\n\n");
    }


    /*
     * Test Case 3
     *
     * Small RNTI/n_ID values and all-zero input.
     */
    {
        const uint16_t n_rnti = 0x0001;
        const uint16_t n_id = 0x0000;
        const uint8_t q = 0;

        const uint8_t input[8] = {
            0, 0, 0, 0, 0, 0, 0, 0
        };

        const uint8_t expected_sequence[8] = {
            0, 0, 0, 1, 0, 0, 1, 1
        };

        const uint8_t expected_scrambled[8] = {
            0, 0, 0, 1, 0, 0, 1, 1
        };

        uint8_t sequence[8];
        uint8_t scrambled[8];

        uint32_t c_init = calculate_c_init(
            n_rnti,
            n_id,
            q
        );

        printf("Test Case 3\n");

        if (c_init != 0x00008000U) {
            printf("FAIL: c_init\n");
            printf(
                "Expected: 0x00008000\n"
                "Actual  : 0x%08X\n",
                c_init
            );

            return 1;
        }

        generate_gold_sequence(
            sequence,
            8,
            c_init
        );

        if (!compare_bits(
            sequence,
            expected_sequence,
            8
        )) {
            printf("FAIL: Gold sequence\n");
            return 1;
        }

        scramble_bits(
            input,
            scrambled,
            8,
            n_rnti,
            n_id,
            q
        );

        if (!compare_bits(
            scrambled,
            expected_scrambled,
            8
        )) {
            printf("FAIL: scrambled output\n");
            return 1;
        }

        printf("PASS\n\n");
    }


    /*
     * Test Case 4
     *
     * Maximum allowed RNTI/n_ID values
     * and all-one input.
     */
    {
        const uint16_t n_rnti = 0xFFFF;
        const uint16_t n_id = 0x03FF;
        const uint8_t q = 0;

        const uint8_t input[8] = {
            1, 1, 1, 1, 1, 1, 1, 1
        };

        const uint8_t expected_sequence[8] = {
            0, 0, 1, 0, 0, 0, 1, 0
        };

        const uint8_t expected_scrambled[8] = {
            1, 1, 0, 1, 1, 1, 0, 1
        };

        uint8_t sequence[8];
        uint8_t scrambled[8];

        uint32_t c_init = calculate_c_init(
            n_rnti,
            n_id,
            q
        );

        printf("Test Case 4\n");

        if (c_init != 0x7FFF83FFU) {
            printf("FAIL: c_init\n");
            printf(
                "Expected: 0x7FFF83FF\n"
                "Actual  : 0x%08X\n",
                c_init
            );

            return 1;
        }

        generate_gold_sequence(
            sequence,
            8,
            c_init
        );

        if (!compare_bits(
            sequence,
            expected_sequence,
            8
        )) {
            printf("FAIL: Gold sequence\n");
            return 1;
        }

        scramble_bits(
            input,
            scrambled,
            8,
            n_rnti,
            n_id,
            q
        );

        if (!compare_bits(
            scrambled,
            expected_scrambled,
            8
        )) {
            printf("FAIL: scrambled output\n");
            return 1;
        }

        printf("PASS\n\n");
    }


    /*
     * Long-sequence test.
     *
     * Verify Gold-sequence generation, scrambling,
     * and descrambling for 10,000 bits.
     */
    {
        const size_t length = LONG_TEST_LENGTH;

        const uint16_t n_rnti = 0x1234;
        const uint16_t n_id = 0x0155;
        const uint8_t q = 0;

        uint8_t input[LONG_TEST_LENGTH];
        uint8_t scrambled[LONG_TEST_LENGTH];
        uint8_t recovered[LONG_TEST_LENGTH];

        /*
         * Generate deterministic input:
         *
         * 0, 1, 0, 1, ...
         */
        for (size_t i = 0; i < length; i++) {
            input[i] = (uint8_t)(i & 1U);
        }

        printf(
            "Long-sequence test (%zu bits)\n",
            length
        );

        /*
         * Scramble.
         */
        scramble_bits(
            input,
            scrambled,
            length,
            n_rnti,
            n_id,
            q
        );

        /*
         * Descramble.
         */
        scramble_bits(
            scrambled,
            recovered,
            length,
            n_rnti,
            n_id,
            q
        );

        /*
         * Verify exact recovery.
         */
        if (!compare_bits(
            recovered,
            input,
            length
        )) {
            printf(
                "FAIL: long-sequence descrambling\n"
            );

            return 1;
        }

        printf("PASS\n\n");
    }


    /*
     * Final result.
     */
    printf(
        "All %d C reference test cases passed.\n",
        NUM_TEST_CASES
    );

    printf(
        "Long-sequence test passed for %d bits.\n",
        LONG_TEST_LENGTH
    );

    return 0;
}
