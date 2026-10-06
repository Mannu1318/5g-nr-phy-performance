#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

#define TEST_LENGTH 16
#define LONG_TEST_LENGTH 10000

void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

void generate_gold_sequence_packed(
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

void scramble_bits_packed(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);

static int compare_buffers(
    const uint8_t *a,
    const uint8_t *b,
    size_t length
)
{
    for (size_t i = 0; i < length; i++) {
        if (a[i] != b[i]) {
            printf(
                "Mismatch at index %zu: scalar=%u packed=%u\n",
                i,
                a[i],
                b[i]
            );
            return 0;
        }
    }

    return 1;
}

int main(void)
{
    uint8_t scalar_sequence[TEST_LENGTH];
    uint8_t packed_sequence[TEST_LENGTH];

    uint8_t input[TEST_LENGTH] = {
        1, 0, 1, 1, 0, 0, 1, 0,
        1, 1, 0, 0, 1, 0, 1, 1
    };

    uint8_t scalar_output[TEST_LENGTH];
    uint8_t packed_output[TEST_LENGTH];

    printf("Kernel 2 — Packed LFSR Cross-Validation\n\n");

    /*
     * Test 1: Gold sequence
     */
    generate_gold_sequence(
        scalar_sequence,
        TEST_LENGTH,
        0x091A0155
    );

    generate_gold_sequence_packed(
        packed_sequence,
        TEST_LENGTH,
        0x091A0155
    );

    printf("Gold sequence comparison: ");

    if (compare_buffers(
            scalar_sequence,
            packed_sequence,
            TEST_LENGTH)) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return 1;
    }

    /*
     * Test 2: Scrambling output
     */
    scramble_bits(
        input,
        scalar_output,
        TEST_LENGTH,
        0x1234,
        0x0155,
        0
    );

    scramble_bits_packed(
        input,
        packed_output,
        TEST_LENGTH,
        0x1234,
        0x0155,
        0
    );

    printf("Scrambling comparison: ");

    if (compare_buffers(
            scalar_output,
            packed_output,
            TEST_LENGTH)) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return 1;
    }

    /*
     * Test 3: Long Gold sequence
     */
    uint8_t scalar_long[LONG_TEST_LENGTH];
    uint8_t packed_long[LONG_TEST_LENGTH];

    generate_gold_sequence(
        scalar_long,
        LONG_TEST_LENGTH,
        0x091A0155
    );

    generate_gold_sequence_packed(
        packed_long,
        LONG_TEST_LENGTH,
        0x091A0155
    );

    printf("Long Gold sequence comparison: ");

    if (compare_buffers(
            scalar_long,
            packed_long,
            LONG_TEST_LENGTH)) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return 1;
    }

    /*
     * Test 4: q = 1
     */
    generate_gold_sequence(
        scalar_sequence,
        TEST_LENGTH,
        0x091A4155
    );

    generate_gold_sequence_packed(
        packed_sequence,
        TEST_LENGTH,
        0x091A4155
    );

    printf("q=1 Gold sequence comparison: ");

    if (compare_buffers(
            scalar_sequence,
            packed_sequence,
            TEST_LENGTH)) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return 1;
    }

    printf("\nAll packed LFSR cross-validation tests passed.\n");

    return 0;
}
