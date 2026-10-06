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

void generate_gold_sequence_packed_bits(
    uint8_t *output,
    size_t length,
    uint32_t c_init
)
{
    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /* Skip Nc = 1600 positions. */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {
        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }

    /*
     * Generate one output byte for every 8 scrambling bits.
     *
     * Bit n is stored at position:
     *
     *     n % 8
     *
     * inside the current output byte.
     */
    for (size_t byte = 0; byte < (length + 7U) / 8U; byte++) {
        uint8_t packed = 0U;

        for (size_t bit = 0; bit < 8U; bit++) {
            size_t n = byte * 8U + bit;

            if (n >= length) {
                break;
            }

            uint8_t scrambling_bit =
                (uint8_t)((x1 & 1U) ^ (x2 & 1U));

            packed |=
                (uint8_t)(scrambling_bit << bit);

            x1 = advance_x1(x1);
            x2 = advance_x2(x2);
        }

        output[byte] = packed;
    }
}
