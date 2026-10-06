#include <stdint.h>
#include <stdio.h>

static uint32_t advance_x1(uint32_t state)
{
    uint32_t feedback =
        ((state >> 3) ^ state) & 1U;

    return (state >> 1) | (feedback << 30);
}

static uint32_t advance_x1_16_reference(uint32_t state)
{
    for (int i = 0; i < 16; i++) {
        state = advance_x1(state);
    }

    return state;
}

/*
 * Derive the dependency mask for each of the
 * eight newly generated high bits.
 *
 * Each input bit is tested independently.
 */
static void derive_masks_x1(uint32_t masks[16])
{
    for (int output_bit = 0; output_bit < 16; output_bit++) {

        uint32_t mask = 0U;

        for (int input_bit = 0; input_bit < 31; input_bit++) {

            uint32_t state =
                1U << input_bit;

            uint32_t result =
                advance_x1_16_reference(state);

            if ((result >> (15 + output_bit)) & 1U) {
                mask |= 1U << input_bit;
            }
        }

        masks[output_bit] = mask;
    }
}

static uint32_t advance_x1_16(
    uint32_t state,
    const uint32_t masks[16]
)
{
    uint32_t high = 0U;

    for (int i = 0; i < 16; i++) {

        unsigned parity =
            __builtin_parity(state & masks[i]);

        high |=
            (uint32_t)parity << (15 + i);
    }

    return (state >> 16) | high;
}

int main(void)
{
    uint32_t masks[16];

    derive_masks_x1(masks);

    printf("x1 16-step dependency masks:\n");

    for (int i = 0; i < 16; i++) {
        printf(
            "mask[%d] = 0x%08X\n",
            i,
            masks[i]
        );
    }

    printf("\nValidation:\n");

    uint32_t test_states[] = {
        0x00000001U,
        0x00000002U,
        0x12345678U,
        0x40000001U,
        0x7FFFFFFFU
    };

    size_t count =
        sizeof(test_states) /
        sizeof(test_states[0]);

    int all_pass = 1;

    for (size_t i = 0; i < count; i++) {

        uint32_t reference =
            advance_x1_16_reference(
                test_states[i]
            );

        uint32_t transformed =
            advance_x1_16(
                test_states[i],
                masks
            );

        printf(
            "0x%08X -> reference 0x%08X, "
            "transformed 0x%08X : %s\n",
            test_states[i],
            reference,
            transformed,
            reference == transformed
                ? "PASS"
                : "FAIL"
        );

        if (reference != transformed) {
            all_pass = 0;
        }
    }

    printf(
        "\n16-step x1 transformation %s.\n",
        all_pass ? "validated" : "FAILED"
    );

    return all_pass ? 0 : 1;
}
