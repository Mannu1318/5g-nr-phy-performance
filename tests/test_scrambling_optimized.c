#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void scramble_bits(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);

void scramble_bits_optimized(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
);

static int compare_outputs(
    const uint8_t *reference,
    const uint8_t *optimized,
    size_t length
)
{
    for (size_t i = 0; i < length; i++) {

        if (reference[i] != optimized[i]) {

            printf(
                "Mismatch at bit %zu: "
                "reference=%u optimized=%u\n",
                i,
                reference[i],
                optimized[i]
            );

            return 0;
        }
    }

    return 1;
}

static int run_test(
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    uint8_t *input =
        malloc(length);

    uint8_t *reference =
        malloc(length);

    uint8_t *optimized =
        malloc(length);

    if (input == NULL ||
        reference == NULL ||
        optimized == NULL) {

        free(input);
        free(reference);
        free(optimized);

        return 0;
    }

    for (size_t i = 0; i < length; i++) {
        input[i] =
            (uint8_t)((i * 7U + 3U) & 1U);
    }

    scramble_bits(
        input,
        reference,
        length,
        n_rnti,
        n_id,
        q
    );

    scramble_bits_optimized(
        input,
        optimized,
        length,
        n_rnti,
        n_id,
        q
    );

    int pass =
        compare_outputs(
            reference,
            optimized,
            length
        );

    free(input);
    free(reference);
    free(optimized);

    return pass;
}

int main(void)
{
    printf(
        "Kernel 2 — Optimized Scrambling Cross-Validation\n\n"
    );

    printf("Test 1: 16 bits, q=0\n");

    if (!run_test(
            16,
            0x1234,
            0x0155,
            0)) {

        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 2: 10000 bits, q=0\n");

    if (!run_test(
            10000,
            0x1234,
            0x0155,
            0)) {

        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 3: 10000 bits, q=1\n");

    if (!run_test(
            10000,
            0x1234,
            0x0155,
            1)) {

        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 4: 100000 bits\n");

    if (!run_test(
            100000,
            0xFFFF,
            0x03FF,
            0)) {

        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 5: 1000000 bits\n");

    if (!run_test(
            1000000,
            0x1234,
            0x0155,
            0)) {

        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf(
        "All optimized scrambling cross-validation tests passed.\n"
    );

    return 0;
}

