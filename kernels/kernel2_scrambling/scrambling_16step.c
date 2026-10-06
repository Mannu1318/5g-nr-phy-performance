#include <stdint.h>
#include <stddef.h>

#define NR_SCRAMBLING_NC 1600U

static uint32_t advance_x1_16(uint32_t state)
{
    uint32_t high = 0U;

    high |= (uint32_t)__builtin_parity(state & 0x00000009U) << 15;
    high |= (uint32_t)__builtin_parity(state & 0x00000012U) << 16;
    high |= (uint32_t)__builtin_parity(state & 0x00000024U) << 17;
    high |= (uint32_t)__builtin_parity(state & 0x00000048U) << 18;
    high |= (uint32_t)__builtin_parity(state & 0x00000090U) << 19;
    high |= (uint32_t)__builtin_parity(state & 0x00000120U) << 20;
    high |= (uint32_t)__builtin_parity(state & 0x00000240U) << 21;
    high |= (uint32_t)__builtin_parity(state & 0x00000480U) << 22;
    high |= (uint32_t)__builtin_parity(state & 0x00000900U) << 23;
    high |= (uint32_t)__builtin_parity(state & 0x00001200U) << 24;
    high |= (uint32_t)__builtin_parity(state & 0x00002400U) << 25;
    high |= (uint32_t)__builtin_parity(state & 0x00004800U) << 26;
    high |= (uint32_t)__builtin_parity(state & 0x00009000U) << 27;
    high |= (uint32_t)__builtin_parity(state & 0x00012000U) << 28;
    high |= (uint32_t)__builtin_parity(state & 0x00024000U) << 29;
    high |= (uint32_t)__builtin_parity(state & 0x00048000U) << 30;

    return (state >> 16) | high;
}

static uint32_t advance_x2_16(uint32_t state)
{
    uint32_t high = 0U;

    high |= (uint32_t)__builtin_parity(state & 0x0000000FU) << 15;
    high |= (uint32_t)__builtin_parity(state & 0x0000001EU) << 16;
    high |= (uint32_t)__builtin_parity(state & 0x0000003CU) << 17;
    high |= (uint32_t)__builtin_parity(state & 0x00000078U) << 18;
    high |= (uint32_t)__builtin_parity(state & 0x000000F0U) << 19;
    high |= (uint32_t)__builtin_parity(state & 0x000001E0U) << 20;
    high |= (uint32_t)__builtin_parity(state & 0x000003C0U) << 21;
    high |= (uint32_t)__builtin_parity(state & 0x00000780U) << 22;
    high |= (uint32_t)__builtin_parity(state & 0x00000F00U) << 23;
    high |= (uint32_t)__builtin_parity(state & 0x00001E00U) << 24;
    high |= (uint32_t)__builtin_parity(state & 0x00003C00U) << 25;
    high |= (uint32_t)__builtin_parity(state & 0x00007800U) << 26;
    high |= (uint32_t)__builtin_parity(state & 0x0000F000U) << 27;
    high |= (uint32_t)__builtin_parity(state & 0x0001E000U) << 28;
    high |= (uint32_t)__builtin_parity(state & 0x0003C000U) << 29;
    high |= (uint32_t)__builtin_parity(state & 0x00078000U) << 30;

    return (state >> 16) | high;
}

void generate_gold_sequence_16step(
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

        x1 =
            (x1 >> 1) |
            (next_x1 << 30);

        x2 =
            (x2 >> 1) |
            (next_x2 << 30);
    }

    size_t n = 0;

    /* Generate sixteen scrambling bits at a time. */
    for (; n + 16U <= length; n += 16U) {

        uint32_t gold =
            x1 ^ x2;

        for (size_t j = 0; j < 16U; j++) {

            output[n + j] =
                (uint8_t)((gold >> j) & 1U);
        }

        x1 = advance_x1_16(x1);
        x2 = advance_x2_16(x2);
    }

    /* Remaining bits. */
    while (n < length) {

        output[n] =
            (uint8_t)((x1 & 1U) ^
                      (x2 & 1U));

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
