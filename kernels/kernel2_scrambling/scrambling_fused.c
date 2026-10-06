#include <stdint.h>
#include <stddef.h>

#define NR_SCRAMBLING_NC 1600U

static uint32_t advance_x1_8(uint32_t state)
{
    uint32_t high = 0U;

    high |= (uint32_t)__builtin_parity(state & 0x009U) << 23;
    high |= (uint32_t)__builtin_parity(state & 0x012U) << 24;
    high |= (uint32_t)__builtin_parity(state & 0x024U) << 25;
    high |= (uint32_t)__builtin_parity(state & 0x048U) << 26;
    high |= (uint32_t)__builtin_parity(state & 0x090U) << 27;
    high |= (uint32_t)__builtin_parity(state & 0x120U) << 28;
    high |= (uint32_t)__builtin_parity(state & 0x240U) << 29;
    high |= (uint32_t)__builtin_parity(state & 0x480U) << 30;

    return (state >> 8) | high;
}

static uint32_t advance_x2_8(uint32_t state)
{
    uint32_t high = 0U;

    high |= (uint32_t)__builtin_parity(state & 0x00FU) << 23;
    high |= (uint32_t)__builtin_parity(state & 0x01EU) << 24;
    high |= (uint32_t)__builtin_parity(state & 0x03CU) << 25;
    high |= (uint32_t)__builtin_parity(state & 0x078U) << 26;
    high |= (uint32_t)__builtin_parity(state & 0x0F0U) << 27;
    high |= (uint32_t)__builtin_parity(state & 0x1E0U) << 28;
    high |= (uint32_t)__builtin_parity(state & 0x3C0U) << 29;
    high |= (uint32_t)__builtin_parity(state & 0x780U) << 30;

    return (state >> 8) | high;
}

static uint32_t calculate_c_init(
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    return ((uint32_t)n_rnti << 15)
         + ((uint32_t)q << 14)
         + (uint32_t)n_id;
}

void scramble_bits_fused(
    const uint8_t *input,
    uint8_t *output,
    size_t length,
    uint16_t n_rnti,
    uint16_t n_id,
    uint8_t q
)
{
    uint32_t c_init =
        calculate_c_init(
            n_rnti,
            n_id,
            q
        );

    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /*
     * 1600-bit Gold sequence warm-up.
     */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {

        uint32_t next_x1 =
            ((x1 >> 3) ^ x1) & 1U;

        uint32_t next_x2 =
            ((x2 >> 3) ^
             (x2 >> 2) ^
             (x2 >> 1) ^
             x2) & 1U;

        x1 =
            (x1 >> 1) |
            (next_x1 << 30);

        x2 =
            (x2 >> 1) |
            (next_x2 << 30);
    }

    size_t n = 0;

    /*
     * Generate eight Gold bits and immediately
     * XOR them with the input.
     */
    for (; n + 8U <= length; n += 8U) {

        uint32_t gold =
            x1 ^ x2;

        for (size_t j = 0; j < 8U; j++) {

            uint8_t scrambling_bit =
                (uint8_t)((gold >> j) & 1U);

            output[n + j] =
                input[n + j] ^ scrambling_bit;
        }

        x1 = advance_x1_8(x1);
        x2 = advance_x2_8(x2);
    }

    /*
     * Remaining bits.
     */
    while (n < length) {

        uint8_t scrambling_bit =
            (uint8_t)((x1 & 1U) ^
                      (x2 & 1U));

        output[n] =
            input[n] ^ scrambling_bit;

        uint32_t next_x1 =
            ((x1 >> 3) ^ x1) & 1U;

        uint32_t next_x2 =
            ((x2 >> 3) ^
             (x2 >> 2) ^
             (x2 >> 1) ^
             x2) & 1U;

        x1 =
            (x1 >> 1) |
            (next_x1 << 30);

        x2 =
            (x2 >> 1) |
            (next_x2 << 30);

        n++;
    }
}
