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

void generate_gold_sequence_multistep(
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
                "Mismatch at bit %zu: scalar=%u multistep=%u\n",
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
    uint8_t multistep[TEST_LENGTH];

    uint32_t c_init = 0x091A0155U;

    generate_gold_sequence(
        scalar,
        TEST_LENGTH,
        c_init
    );

    generate_gold_sequence_multistep(
        multistep,
        TEST_LENGTH,
        c_init
    );

    printf("16-bit Gold sequence comparison: ");

    if (compare_sequences(
            scalar,
            multistep,
            TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");
        return EXIT_FAILURE;
    }

    uint8_t *scalar_long =
        malloc(LONG_TEST_LENGTH);

    uint8_t *multistep_long =
        malloc(LONG_TEST_LENGTH);

    if (scalar_long == NULL || multistep_long == NULL) {
        free(scalar_long);
        free(multistep_long);
        return EXIT_FAILURE;
    }

    generate_gold_sequence(
        scalar_long,
        LONG_TEST_LENGTH,
        c_init
    );

    generate_gold_sequence_multistep(
        multistep_long,
        LONG_TEST_LENGTH,
        c_init
    );

    printf("10,000-bit Gold sequence comparison: ");

    if (compare_sequences(
            scalar_long,
            multistep_long,
            LONG_TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL\n");

        free(scalar_long);
        free(multistep_long);

        return EXIT_FAILURE;
    }

    uint8_t q1_scalar[TEST_LENGTH];
    uint8_t q1_multistep[TEST_LENGTH];

    generate_gold_sequence(
        q1_scalar,
        TEST_LENGTH,
        0x091A4155U
    );

    generate_gold_sequence_multistep(
        q1_multistep,
        TEST_LENGTH,
        0x091A4155U
    );

    printf("q=1 Gold sequence comparison: ");

    if (compare_sequences(
            q1_scalar,
            q1_multistep,
            TEST_LENGTH
        )) {
        printf("PASS\n");
    } else {
        printf("FAIL");

        free(scalar_long);
        free(multistep_long);

        return EXIT_FAILURE;
    }

    free(scalar_long);
    free(multistep_long);

    printf("\nAll multi-step cross-validation tests passed.\n");

    return EXIT_SUCCESS;
}
