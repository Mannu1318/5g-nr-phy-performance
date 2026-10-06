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

void generate_gold_sequence_multistep(
    uint8_t *output,
    size_t length,
    uint32_t c_init
)
{
    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /* 1600-bit Gold sequence warm-up */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {
        uint32_t next_x1 =
            ((x1 >> 3) ^ x1) & 1U;

        uint32_t next_x2 =
            ((x2 >> 3) ^
             (x2 >> 2) ^
             (x2 >> 1) ^
             x2) & 1U;

        x1 = (x1 >> 1) | (next_x1 << 30);
        x2 = (x2 >> 1) | (next_x2 << 30);
    }

    size_t n = 0;

    /* Generate eight scrambling bits at a time. */
    for (; n + 8U <= length; n += 8U) {

        uint32_t gold =
            x1 ^ x2;

        for (size_t j = 0; j < 8U; j++) {
            output[n + j] =
                (uint8_t)((gold >> j) & 1U);
        }

        x1 = advance_x1_8(x1);
        x2 = advance_x2_8(x2);
    }

    /* Remaining bits. */
    while (n < length) {

        output[n] =
            (uint8_t)((x1 & 1U) ^ (x2 & 1U));

        uint32_t next_x1 =
            ((x1 >> 3) ^ x1) & 1U;

        uint32_t next_x2 =
            ((x2 >> 3) ^
             (x2 >> 2) ^
             (x2 >> 1) ^
             x2) & 1U;

        x1 = (x1 >> 1) | (next_x1 << 30);
        x2 = (x2 >> 1) | (next_x2 << 30);

        n++;
    }
}
