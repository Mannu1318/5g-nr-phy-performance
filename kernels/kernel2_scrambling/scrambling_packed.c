#include <stdint.h>
#include <stddef.h>

#define NR_SCRAMBLING_NC 1600U

static uint32_t advance_x1(uint32_t state)
{
    uint32_t feedback =
        ((state >> 3) ^ state) & 1U;

    return (state >> 1) | (feedback << 30);
}

static uint32_t advance_x2(uint32_t state)
{
    uint32_t feedback =
        ((state >> 3) ^
         (state >> 2) ^
         (state >> 1) ^
         state) & 1U;

    return (state >> 1) | (feedback << 30);
}

void generate_gold_sequence_packed(
    uint8_t *output,
    size_t length,
    uint32_t c_init
)
{
    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /* Skip the first Nc = 1600 sequence positions. */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {
        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }

    /* Generate the scrambling sequence. */
    for (size_t n = 0; n < length; n++) {
        output[n] =
            (uint8_t)((x1 & 1U) ^ (x2 & 1U));

        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }
}

void scramble_bits_packed(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    uint32_t c_init =
        ((uint32_t)n_rnti << 15)
        + ((uint32_t)q << 14)
        + (uint32_t)n_id;

    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /* Skip Nc = 1600 positions. */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {
        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }

    /* Generate and apply scrambling directly. */
    for (size_t n = 0; n < length; n++) {
        uint8_t scrambling_bit =
            (uint8_t)((x1 & 1U) ^ (x2 & 1U));

        output[n] = input[n] ^ scrambling_bit;

        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }
}
