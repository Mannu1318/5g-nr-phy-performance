#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

void generate_gold_sequence_16step(
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
                "Mismatch at bit %zu: "
                "reference=%u optimized=%u\n",
                i,
                a[i],
                b[i]
            );
            return 0;
        }
    }

    return 1;
}

static int run_test(
    size_t length,
    uint32_t c_init
)
{
    uint8_t *reference =
        malloc(length);

    uint8_t *optimized =
        malloc(length);

    if (reference == NULL ||
        optimized == NULL) {

        free(reference);
        free(optimized);

        return 0;
    }

    generate_gold_sequence(
        reference,
        length,
        c_init
    );

    generate_gold_sequence_16step(
        optimized,
        length,
        c_init
    );

    int pass =
        compare_sequences(
            reference,
            optimized,
            length
        );

    free(reference);
    free(optimized);

    return pass;
}

int main(void)
{
    printf("Kernel 2 — 16-step cross-validation\n\n");

    printf("Test 1: 16 bits\n");

    if (!run_test(16, 0x091A0155U)) {
        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 2: 10000 bits\n");

    if (!run_test(10000, 0x091A0155U)) {
        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 3: q=1 configuration\n");

    if (!run_test(10000, 0x091A4155U)) {
        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("Test 4: 100000 bits\n");

    if (!run_test(100000, 0x091A0155U)) {
        printf("FAIL\n");
        return 1;
    }

    printf("PASS\n\n");

    printf("All 16-step cross-validation tests passed.\n");

    return 0;
}
