#include <stdint.h>
#include <stdio.h>

#define LFSR_BITS 31
#define STEP_COUNT 8

static uint32_t advance_x2(uint32_t state)
{
    uint32_t feedback =
        ((state >> 3) ^
         (state >> 2) ^
         (state >> 1) ^
         state) & 1U;

    return (state >> 1) | (feedback << 30);
}

static void initialize_masks(uint32_t masks[LFSR_BITS])
{
    for (int i = 0; i < LFSR_BITS; i++) {
        masks[i] = 1U << i;
    }
}

static void advance_masks_x2(uint32_t masks[LFSR_BITS])
{
    uint32_t next[LFSR_BITS];

    for (int i = 0; i < LFSR_BITS - 1; i++) {
        next[i] = masks[i + 1];
    }

    next[30] =
        masks[3] ^
        masks[2] ^
        masks[1] ^
        masks[0];

    for (int i = 0; i < LFSR_BITS; i++) {
        masks[i] = next[i];
    }
}

static uint32_t apply_masks(
    const uint32_t masks[LFSR_BITS],
    uint32_t state
)
{
    uint32_t result = 0U;

    for (int i = 0; i < LFSR_BITS; i++) {
        uint32_t dependency =
            masks[i] & state;

        dependency ^= dependency >> 16;
        dependency ^= dependency >> 8;
        dependency ^= dependency >> 4;
        dependency ^= dependency >> 2;
        dependency ^= dependency >> 1;

        uint32_t bit =
            dependency & 1U;

        result |= bit << i;
    }

    return result;
}

int main(void)
{
    uint32_t masks[LFSR_BITS];

    initialize_masks(masks);

    for (int step = 0; step < STEP_COUNT; step++) {
        advance_masks_x2(masks);
    }

    uint32_t test_states[] = {
        0x00000001U,
        0x00000002U,
        0x12345678U,
        0x40000001U,
        0x7FFFFFFFU
    };

    size_t count =
        sizeof(test_states) / sizeof(test_states[0]);

    for (size_t t = 0; t < count; t++) {

        uint32_t original =
            test_states[t] & 0x7FFFFFFFU;

        uint32_t ordinary = original;

        for (int step = 0; step < STEP_COUNT; step++) {
            ordinary = advance_x2(ordinary);
        }

        uint32_t transformed =
            apply_masks(masks, original);

        printf(
            "state=0x%08X  ordinary=0x%08X  "
            "8-step=0x%08X  %s\n",
            original,
            ordinary,
            transformed,
            ordinary == transformed ? "PASS" : "FAIL"
        );

        if (ordinary != transformed) {
            return 1;
        }
    }

    printf("\n8-step x2 transformation validated.\n");

    return 0;
}
