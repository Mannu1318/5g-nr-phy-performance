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

void generate_gold_sequence_multibit(
    uint8_t *output,
    size_t length,
    uint32_t c_init
)
{
    uint32_t x1 = 1U;
    uint32_t x2 = c_init;

    /* Gold sequence warm-up: Nc = 1600 */
    for (size_t n = 0; n < NR_SCRAMBLING_NC; n++) {
        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }

    /* Process eight output bits per outer iteration. */
    size_t n = 0;

    for (; n + 8U <= length; n += 8U) {

        for (size_t j = 0; j < 8U; j++) {

            output[n + j] =
                (uint8_t)((x1 & 1U) ^ (x2 & 1U));

            x1 = advance_x1(x1);
            x2 = advance_x2(x2);
        }
    }

    /* Handle any remaining bits. */
    for (; n < length; n++) {

        output[n] =
            (uint8_t)((x1 & 1U) ^ (x2 & 1U));

        x1 = advance_x1(x1);
        x2 = advance_x2(x2);
    }
}
