#include <stdio.h>
#include <math.h>

/*
 * Current/reference 256-QAM decision logic.
 */
static void qam256_level_to_bits_reference(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3)
{
    if (value >= 14.0f) {
        *b0 = 0; *b1 = 0; *b2 = 0; *b3 = 0;
    } else if (value >= 12.0f) {
        *b0 = 0; *b1 = 0; *b2 = 0; *b3 = 1;
    } else if (value >= 10.0f) {
        *b0 = 0; *b1 = 0; *b2 = 1; *b3 = 0;
    } else if (value >= 8.0f) {
        *b0 = 0; *b1 = 0; *b2 = 1; *b3 = 1;
    } else if (value >= 6.0f) {
        *b0 = 0; *b1 = 1; *b2 = 0; *b3 = 0;
    } else if (value >= 4.0f) {
        *b0 = 0; *b1 = 1; *b2 = 0; *b3 = 1;
    } else if (value >= 2.0f) {
        *b0 = 0; *b1 = 1; *b2 = 1; *b3 = 0;
    } else if (value >= 0.0f) {
        *b0 = 0; *b1 = 1; *b2 = 1; *b3 = 1;
    } else if (value >= -2.0f) {
        *b0 = 1; *b1 = 1; *b2 = 1; *b3 = 1;
    } else if (value >= -4.0f) {
        *b0 = 1; *b1 = 1; *b2 = 1; *b3 = 0;
    } else if (value >= -6.0f) {
        *b0 = 1; *b1 = 1; *b2 = 0; *b3 = 1;
    } else if (value >= -8.0f) {
        *b0 = 1; *b1 = 1; *b2 = 0; *b3 = 0;
    } else if (value >= -10.0f) {
        *b0 = 1; *b1 = 0; *b2 = 1; *b3 = 1;
    } else if (value >= -12.0f) {
        *b0 = 1; *b1 = 0; *b2 = 1; *b3 = 0;
    } else if (value >= -14.0f) {
        *b0 = 1; *b1 = 0; *b2 = 0; *b3 = 1;
    } else {
        *b0 = 1; *b1 = 0; *b2 = 0; *b3 = 0;
    }
}


/*
 * Experimental branch-reduced version.
 *
 * We first determine which of the 16 decision regions contains
 * the input value, then use a lookup table.
 */
static void qam256_level_to_bits_experimental(
    float value,
    unsigned char *b0,
    unsigned char *b1,
    unsigned char *b2,
    unsigned char *b3)
{
    static const unsigned char table[16][4] = {
        {0, 0, 0, 0},  /* +15 */
        {0, 0, 0, 1},  /* +13 */
        {0, 0, 1, 0},  /* +11 */
        {0, 0, 1, 1},  /*  +9 */
        {0, 1, 0, 0},  /*  +7 */
        {0, 1, 0, 1},  /*  +5 */
        {0, 1, 1, 0},  /*  +3 */
        {0, 1, 1, 1},  /*  +1 */
        {1, 1, 1, 1},  /*  -1 */
        {1, 1, 1, 0},  /*  -3 */
        {1, 1, 0, 1},  /*  -5 */
        {1, 1, 0, 0},  /*  -7 */
        {1, 0, 1, 1},  /*  -9 */
        {1, 0, 1, 0},  /* -11 */
        {1, 0, 0, 1},  /* -13 */
        {1, 0, 0, 0}   /* -15 */
    };

    int index;

if (value >= 0.0f) {
    index = 7 - (int)(value * 0.5f);
} else {
    index = 7 + (int)ceilf((-value) * 0.5f);
}
    if (index < 0)
        index = 0;

    if (index > 15)
        index = 15;

    *b0 = table[index][0];
    *b1 = table[index][1];
    *b2 = table[index][2];
    *b3 = table[index][3];
}
/*
 * Compare reference and experimental implementations.
 */
static int compare_value(float value)
{
    unsigned char r0, r1, r2, r3;
    unsigned char e0, e1, e2, e3;

    qam256_level_to_bits_reference(
        value, &r0, &r1, &r2, &r3);

    qam256_level_to_bits_experimental(
        value, &e0, &e1, &e2, &e3);

    if (r0 != e0 ||
        r1 != e1 ||
        r2 != e2 ||
        r3 != e3) {

        printf(
            "MISMATCH value=%f "
            "reference=%u%u%u%u "
            "experimental=%u%u%u%u\n",
            value,
            r0, r1, r2, r3,
            e0, e1, e2, e3
        );

        return 0;
    }

    return 1;
}


int main(void)
{
    /*
     * Test every decision boundary and values immediately
     * below and above each boundary.
     */
    const float boundaries[] = {
        -14.0f, -12.0f, -10.0f, -8.0f,
        -6.0f,  -4.0f,  -2.0f,   0.0f,
         2.0f,   4.0f,   6.0f,   8.0f,
        10.0f,  12.0f,  14.0f
    };

    const float epsilon = 0.001f;

    size_t n_boundaries =
        sizeof(boundaries) / sizeof(boundaries[0]);

    for (size_t i = 0; i < n_boundaries; i++) {

        float b = boundaries[i];

        if (!compare_value(b - epsilon))
            return 1;

        if (!compare_value(b))
            return 1;

        if (!compare_value(b + epsilon))
            return 1;
    }

    /*
     * Test the exact constellation levels.
     */
    const float levels[] = {
         15.0f, 13.0f, 11.0f,  9.0f,
          7.0f,  5.0f,  3.0f,  1.0f,
         -1.0f,-3.0f,-5.0f,-7.0f,
         -9.0f,-11.0f,-13.0f,-15.0f
    };

    size_t n_levels =
        sizeof(levels) / sizeof(levels[0]);

    for (size_t i = 0; i < n_levels; i++) {

        if (!compare_value(levels[i]))
            return 1;
    }

    printf("256-QAM optimized demapper correctness: PASS\n");

    return 0;
}
