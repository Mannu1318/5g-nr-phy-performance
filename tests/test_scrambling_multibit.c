#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define TEST_LENGTH 16
#define LONG_TEST_LENGTH 10000

void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

void generate_gold_sequence_multibit(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

static int compare_sequences(
    const uint8_t *a,
    const uint8_t *b,
    size_t length
)
{
    for (size_t i = 0; i < length; i++) {
        if (a[i] != b[i]) {
            printf(
                "Mismatch at bit %zu: scalar=%u multibit=%u\n",
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
    uint8_t scalar[TEST_LENGTH];
    uint8_t multibit[TEST_LENGTH];

    uint32_t c_init = 0x091A0155U;

    /*
     * Test 1: 16-bit sequence
     */
    generate_gold_sequence(
        scalar,
        TEST_LENGTH,
        c_init
    );

    generate_gold_sequence_multibit(
        multibit,
        TEST_LENGTH,
        c_init
    );

    printf("16-bit Gold sequence comparison: ");

    if (compare_sequences(
            scalar,
            multibit,
            TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return EXIT_FAILURE;
    }

    /*
     * Test 2: 10,000-bit sequence
     */
    uint8_t *scalar_long =
        malloc(LONG_TEST_LENGTH);

    uint8_t *multibit_long =
        malloc(LONG_TEST_LENGTH);

    if (scalar_long == NULL || multibit_long == NULL) {
        free(scalar_long);
        free(multibit_long);
        return EXIT_FAILURE;
    }

    generate_gold_sequence(
        scalar_long,
        LONG_TEST_LENGTH,
        c_init
    );

    generate_gold_sequence_multibit(
        multibit_long,
        LONG_TEST_LENGTH,
        c_init
    );

    printf("10,000-bit Gold sequence comparison: ");

    if (compare_sequences(
            scalar_long,
            multibit_long,
            LONG_TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");

        free(scalar_long);
        free(multibit_long);

        return EXIT_FAILURE;
    }

    /*
     * Test 3: q = 1
     *
     * c_init = 0x091A4155
     */
    uint8_t q1_scalar[TEST_LENGTH];
    uint8_t q1_multibit[TEST_LENGTH];

    generate_gold_sequence(
        q1_scalar,
        TEST_LENGTH,
        0x091A4155U
    );

    generate_gold_sequence_multibit(
        q1_multibit,
        TEST_LENGTH,
        0x091A4155U
    );

    printf("q=1 Gold sequence comparison: ");

    if (compare_sequences(
            q1_scalar,
            q1_multibit,
            TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");

        free(scalar_long);
        free(multibit_long);

        return EXIT_FAILURE;
    }

    free(scalar_long);
    free(multibit_long);

    printf("\nAll multi-bit cross-validation tests passed.\n");

    return EXIT_SUCCESS;
}
