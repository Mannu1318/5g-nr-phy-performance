#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

void generate_gold_sequence(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

void generate_gold_sequence_packed_bits(
    uint8_t *output,
    size_t length,
    uint32_t c_init
);

static int compare_packed_with_scalar(
    const uint8_t *scalar,
    const uint8_t *packed,
    size_t length
)
{
    for (size_t i = 0; i < length; i++) {
        size_t byte_index = i / 8U;
        size_t bit_index = i % 8U;

        uint8_t packed_bit =
            (packed[byte_index] >> bit_index) & 1U;

        if (scalar[i] != packed_bit) {
            printf(
                "Mismatch at bit %zu: scalar=%u packed=%u\n",
                i,
                scalar[i],
                packed_bit
            );
            return 0;
        }
    }

    return 1;
}

static int run_test(size_t length)
{
    uint8_t scalar[64] = {0};
    uint8_t packed[8] = {0};

    generate_gold_sequence(
        scalar,
        length,
        0x091A0155
    );

    generate_gold_sequence_packed_bits(
        packed,
        length,
        0x091A0155
    );

    if (!compare_packed_with_scalar(
            scalar,
            packed,
            length)) {
        return 0;
    }

    printf(
        "Length %2zu bits: PASS\n",
        length
    );

    return 1;
}

int main(void)
{
    size_t test_lengths[] = {
        1,
        7,
        8,
        9,
        15,
        16,
        17,
        31,
        32,
        33,
        63,
        64
    };

    size_t num_tests =
        sizeof(test_lengths) /
        sizeof(test_lengths[0]);

    printf("Kernel 2 — Packed-Bit Cross-Validation\n\n");

    for (size_t i = 0; i < num_tests; i++) {
        if (!run_test(test_lengths[i])) {
            printf("\nPacked-bit validation FAILED.\n");
            return 1;
        }
    }

    printf("\nAll packed-bit cross-validation tests passed.\n");

    return 0;
}
