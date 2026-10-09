#include "qam.h"

#include <math.h>


/*
 * QPSK
 *
 * Mapping:
 *
 *   00 -> (+1 + j)/sqrt(2)
 *   01 -> (+1 - j)/sqrt(2)
 *   10 -> (-1 + j)/sqrt(2)
 *   11 -> (-1 - j)/sqrt(2)
 */

int qpsk_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
)
{
    if (n_bits % 2 != 0) {
        return -1;
    }

    for (size_t i = 0; i < n_bits; i++) {
        if (bits[i] > 1) {
            return -2;
        }
    }

    const float normalization = 1.0f / sqrtf(2.0f);

    size_t n_symbols = n_bits / 2;

    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char b0 = bits[2 * i];
        unsigned char b1 = bits[2 * i + 1];

        float i_component = 1.0f - 2.0f * (float)b0;
        float q_component = 1.0f - 2.0f * (float)b1;

        symbols[i].real = i_component * normalization;
        symbols[i].imag = q_component * normalization;
    }

    return 0;
}


/*
 * QPSK hard-decision demapper.
 */

int qpsk_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
)
{
    for (size_t i = 0; i < n_symbols; i++) {

        if (symbols[i].real >= 0.0f) {
            bits[2 * i] = 0;
        } else {
            bits[2 * i] = 1;
        }

        if (symbols[i].imag >= 0.0f) {
            bits[2 * i + 1] = 0;
        } else {
            bits[2 * i + 1] = 1;
        }
    }

    return 0;
}

/*
 * 16-QAM
 *
 * Bit mapping:
 *
 *   00 -> +3
 *   01 -> +1
 *   10 -> -3
 *   11 -> -1
 *
 * I component uses bits b0, b2.
 * Q component uses bits b1, b3.
 *
 * Normalization:
 *
 *   1 / sqrt(10)
 */

static float qam16_level(
    unsigned char b0,
    unsigned char b1
)
{
    if (b0 == 0 && b1 == 0) {
        return 3.0f;
    }

    if (b0 == 0 && b1 == 1) {
        return 1.0f;
    }

    if (b0 == 1 && b1 == 0) {
        return -3.0f;
    }

    return -1.0f;
}


int qam16_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
)
{
    if (n_bits % 4 != 0) {
        return -1;
    }

    for (size_t i = 0; i < n_bits; i++) {
        if (bits[i] > 1) {
            return -2;
        }
    }

    const float normalization = 1.0f / sqrtf(10.0f);

    size_t n_symbols = n_bits / 4;

    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char b0 = bits[4 * i];
        unsigned char b1 = bits[4 * i + 1];
        unsigned char b2 = bits[4 * i + 2];
        unsigned char b3 = bits[4 * i + 3];

        float i_component = qam16_level(b0, b2);
        float q_component = qam16_level(b1, b3);

        symbols[i].real = i_component * normalization;
        symbols[i].imag = q_component * normalization;
    }

    return 0;
}


/*
 * 16-QAM hard-decision demapper.
 *
 * Decision boundaries:
 *
 *   x >= +2  -> +3
 *   x >=  0  -> +1
 *   x >= -2  -> -1
 *   else     -> -3
 */

static void qam16_level_to_bits(
    float value,
    unsigned char *b0,
    unsigned char *b1
)
{
    if (value >= 2.0f) {

        *b0 = 0;
        *b1 = 0;

    } else if (value >= 0.0f) {

        *b0 = 0;
        *b1 = 1;

    } else if (value >= -2.0f) {

        *b0 = 1;
        *b1 = 1;

    } else {

        *b0 = 1;
        *b1 = 0;
    }
}


int qam16_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
)
{
    const float normalization = 1.0f / sqrtf(10.0f);

    for (size_t i = 0; i < n_symbols; i++) {

        /*
         * Convert normalized symbol coordinates
         * back to the original constellation levels.
         */
        float i_value = symbols[i].real / normalization;
        float q_value = symbols[i].imag / normalization;

        unsigned char i_b0;
        unsigned char i_b1;
        unsigned char q_b0;
        unsigned char q_b1;

        qam16_level_to_bits(
            i_value,
            &i_b0,
            &i_b1
        );

        qam16_level_to_bits(
            q_value,
            &q_b0,
            &q_b1
        );

        bits[4 * i]     = i_b0;
        bits[4 * i + 1] = q_b0;
        bits[4 * i + 2] = i_b1;
        bits[4 * i + 3] = q_b1;
    }

    return 0;
}


/*
 * 64-QAM
 *
 * Bit mapping:
 *
 *   000 -> +7
 *   001 -> +5
 *   010 -> +3
 *   011 -> +1
 *   100 -> -7
 *   101 -> -5
 *   110 -> -3
 *   111 -> -1
 *
 * I component uses bits b0, b2, b4.
 * Q component uses bits b1, b3, b5.
 *
 * Normalization:
 *
 *   1 / sqrt(42)
 */

static float qam64_level(
    unsigned char b0,
    unsigned char b1,
    unsigned char b2
)
{
    if (b0 == 0 && b1 == 0 && b2 == 0) {
        return 7.0f;
    }

    if (b0 == 0 && b1 == 0 && b2 == 1) {
        return 5.0f;
    }

    if (b0 == 0 && b1 == 1 && b2 == 0) {
        return 3.0f;
    }

    if (b0 == 0 && b1 == 1 && b2 == 1) {
        return 1.0f;
    }

    if (b0 == 1 && b1 == 0 && b2 == 0) {
        return -7.0f;
    }

    if (b0 == 1 && b1 == 0 && b2 == 1) {
        return -5.0f;
    }

    if (b0 == 1 && b1 == 1 && b2 == 0) {
        return -3.0f;
    }

    return -1.0f;
}


int qam64_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
)
{
    if (n_bits % 6 != 0) {
        return -1;
    }

    for (size_t i = 0; i < n_bits; i++) {
        if (bits[i] > 1) {
            return -2;
        }
    }

    const float normalization = 1.0f / sqrtf(42.0f);

    size_t n_symbols = n_bits / 6;

    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char b0 = bits[6 * i];
        unsigned char b1 = bits[6 * i + 1];
        unsigned char b2 = bits[6 * i + 2];
        unsigned char b3 = bits[6 * i + 3];
        unsigned char b4 = bits[6 * i + 4];
        unsigned char b5 = bits[6 * i + 5];

        float i_component =
            qam64_level(b0, b2, b4);

        float q_component =
            qam64_level(b1, b3, b5);

        symbols[i].real =
            i_component * normalization;

        symbols[i].imag =
            q_component * normalization;
    }

    return 0;
}


/*
 * 64-QAM hard-decision demapper.
 *
 * Decision boundaries:
 *
 *   +6
 *   +4
 *   +2
 *    0
 *   -2
 *   -4
 *   -6
 */

static void qam64_level_to_bits(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2
)
{
    if (value >= 6.0f) {

        *b0 = 0;
        *b1 = 0;
        *b2 = 0;

    } else if (value >= 4.0f) {

        *b0 = 0;
        *b1 = 0;
        *b2 = 1;

    } else if (value >= 2.0f) {

        *b0 = 0;
        *b1 = 1;
        *b2 = 0;

    } else if (value >= 0.0f) {

        *b0 = 0;
        *b1 = 1;
        *b2 = 1;

    } else if (value >= -2.0f) {

        *b0 = 1;
        *b1 = 1;
        *b2 = 1;

    } else if (value >= -4.0f) {

        *b0 = 1;
        *b1 = 1;
        *b2 = 0;

    } else if (value >= -6.0f) {

        *b0 = 1;
        *b1 = 0;
        *b2 = 1;

    } else {

        *b0 = 1;
        *b1 = 0;
        *b2 = 0;
    }
}


int qam64_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
)
{
    const float normalization = 1.0f / sqrtf(42.0f);

    for (size_t i = 0; i < n_symbols; i++) {

        /*
         * Convert normalized coordinates back
         * to the original constellation levels.
         */
        float i_value =
            symbols[i].real / normalization;

        float q_value =
            symbols[i].imag / normalization;

        unsigned char i_b0;
        unsigned char i_b1;
        unsigned char i_b2;

        unsigned char q_b0;
        unsigned char q_b1;
        unsigned char q_b2;

        qam64_level_to_bits(
            i_value,
            &i_b0,
            &i_b1,
            &i_b2
        );

        qam64_level_to_bits(
            q_value,
            &q_b0,
            &q_b1,
            &q_b2
        );

        bits[6 * i]     = i_b0;
        bits[6 * i + 1] = q_b0;
        bits[6 * i + 2] = i_b1;
        bits[6 * i + 3] = q_b1;
        bits[6 * i + 4] = i_b2;
        bits[6 * i + 5] = q_b2;
    }

    return 0;
}


/*
 * 256-QAM
 *
 * Bit mapping:
 *
 *   0000 -> +15
 *   0001 -> +13
 *   0010 -> +11
 *   0011 -> +9
 *   0100 -> +7
 *   0101 -> +5
 *   0110 -> +3
 *   0111 -> +1
 *   1000 -> -15
 *   1001 -> -13
 *   1010 -> -11
 *   1011 -> -9
 *   1100 -> -7
 *   1101 -> -5
 *   1110 -> -3
 *   1111 -> -1
 *
 * I component uses bits b0, b2, b4, b6.
 * Q component uses bits b1, b3, b5, b7.
 *
 * Normalization:
 *
 *   1 / sqrt(170)
 */

static const float qam256_levels[16] = {
     15.0f,
     13.0f,
     11.0f,
      9.0f,
      7.0f,
      5.0f,
      3.0f,
      1.0f,
    -15.0f,
    -13.0f,
    -11.0f,
     -9.0f,
     -7.0f,
     -5.0f,
     -3.0f,
     -1.0f
};


static float qam256_level(
    unsigned char b0,
    unsigned char b1,
    unsigned char b2,
    unsigned char b3
)
{
    unsigned int index =
        ((unsigned int)b0 << 3) |
        ((unsigned int)b1 << 2) |
        ((unsigned int)b2 << 1) |
        (unsigned int)b3;

    return qam256_levels[index];
}

int qam256_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
)
{
    if (n_bits % 8 != 0) {
        return -1;
    }

    for (size_t i = 0; i < n_bits; i++) {
        if (bits[i] > 1) {
            return -2;
        }
    }

    const float normalization =
        1.0f / sqrtf(170.0f);

    size_t n_symbols = n_bits / 8;

    for (size_t i = 0; i < n_symbols; i++) {

        unsigned char b0 = bits[8 * i];
        unsigned char b1 = bits[8 * i + 1];
        unsigned char b2 = bits[8 * i + 2];
        unsigned char b3 = bits[8 * i + 3];
        unsigned char b4 = bits[8 * i + 4];
        unsigned char b5 = bits[8 * i + 5];
        unsigned char b6 = bits[8 * i + 6];
        unsigned char b7 = bits[8 * i + 7];

        float i_component =
            qam256_level(
                b0,
                b2,
                b4,
                b6
            );

        float q_component =
            qam256_level(
                b1,
                b3,
                b5,
                b7
            );

        symbols[i].real =
            i_component * normalization;

        symbols[i].imag =
            q_component * normalization;
    }

    return 0;
}


/*
 * 256-QAM hard-decision demapper.
 *
 * Decision boundaries:
 *
 *   -14 -12 -10 -8 -6 -4 -2
 *     0  +2  +4 +6 +8 +10 +12 +14
 */

static const unsigned char qam256_level_bits[16][4] = {
    {0, 0, 0, 0},
    {0, 0, 0, 1},
    {0, 0, 1, 0},
    {0, 0, 1, 1},
    {0, 1, 0, 0},
    {0, 1, 0, 1},
    {0, 1, 1, 0},
    {0, 1, 1, 1},
    {1, 1, 1, 1},
    {1, 1, 1, 0},
    {1, 1, 0, 1},
    {1, 1, 0, 0},
    {1, 0, 1, 1},
    {1, 0, 1, 0},
    {1, 0, 0, 1},
    {1, 0, 0, 0}
};


static unsigned int qam256_level_index(float value)
{
    unsigned int index;

    if (value >= 0.0f) {
        index = 7U - (unsigned int)(value * 0.5f);
    } else {
        index = 7U +
                (unsigned int)((-value) * 0.5f + 0.999999f);
    }

    if (index > 15U) {
        index = 15U;
    }

    return index;
}


static void qam256_level_to_bits(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3
)
{
    unsigned int index =
        qam256_level_index(value);

    *b0 = qam256_level_bits[index][0];
    *b1 = qam256_level_bits[index][1];
    *b2 = qam256_level_bits[index][2];
    *b3 = qam256_level_bits[index][3];
}

int qam256_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
)
{
    const float normalization =
        1.0f / sqrtf(170.0f);

    for (size_t i = 0; i < n_symbols; i++) {

        /*
         * Convert normalized coordinates back
         * to the original constellation levels.
         */
        float i_value =
            symbols[i].real / normalization;

        float q_value =
            symbols[i].imag / normalization;

        unsigned char i_b0;
        unsigned char i_b1;
        unsigned char i_b2;
        unsigned char i_b3;

        unsigned char q_b0;
        unsigned char q_b1;
        unsigned char q_b2;
        unsigned char q_b3;

        qam256_level_to_bits(
            i_value,
            &i_b0,
            &i_b1,
            &i_b2,
            &i_b3
        );

        qam256_level_to_bits(
            q_value,
            &q_b0,
            &q_b1,
            &q_b2,
            &q_b3
        );

        bits[8 * i]     = i_b0;
        bits[8 * i + 1] = q_b0;
        bits[8 * i + 2] = i_b1;
        bits[8 * i + 3] = q_b1;
        bits[8 * i + 4] = i_b2;
        bits[8 * i + 5] = q_b2;
        bits[8 * i + 6] = i_b3;
        bits[8 * i + 7] = q_b3;
    }

    return 0;
}
