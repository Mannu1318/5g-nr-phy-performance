#include <math.h>
#include <stddef.h>
#include <stdio.h>

#include "qam.h"

typedef struct {
    float real;
    float imag;
} packed_qam256_entry_t;


/*
 * 256-QAM packed-byte lookup table.
 *
 * Each input byte represents one complete 256-QAM symbol:
 *
 *   bit 7 -> b0
 *   bit 6 -> b1
 *   bit 5 -> b2
 *   bit 4 -> b3
 *   bit 3 -> b4
 *   bit 2 -> b5
 *   bit 1 -> b6
 *   bit 0 -> b7
 *
 * The table stores the already-normalized I/Q symbol.
 */
static packed_qam256_entry_t qam256_packed_table[256];


static float qam256_level_from_index(unsigned int index)
{
    static const float levels[16] = {
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

    return levels[index];
}


static void qam256_packed_table_init(void)
{
    const float normalization = 1.0f / sqrtf(170.0f);

    for (unsigned int value = 0; value < 256; value++) {

        unsigned char b0 = (unsigned char)((value >> 7) & 1);
        unsigned char b1 = (unsigned char)((value >> 6) & 1);
        unsigned char b2 = (unsigned char)((value >> 5) & 1);
        unsigned char b3 = (unsigned char)((value >> 4) & 1);
        unsigned char b4 = (unsigned char)((value >> 3) & 1);
        unsigned char b5 = (unsigned char)((value >> 2) & 1);
        unsigned char b6 = (unsigned char)((value >> 1) & 1);
        unsigned char b7 = (unsigned char)(value & 1);

        unsigned int i_index =
            ((unsigned int)b0 << 3) |
            ((unsigned int)b2 << 2) |
            ((unsigned int)b4 << 1) |
            (unsigned int)b6;

        unsigned int q_index =
            ((unsigned int)b1 << 3) |
            ((unsigned int)b3 << 2) |
            ((unsigned int)b5 << 1) |
            (unsigned int)b7;

        qam256_packed_table[value].real =
            qam256_level_from_index(i_index) * normalization;

        qam256_packed_table[value].imag =
            qam256_level_from_index(q_index) * normalization;
    }
}


static void qam256_map_packed(
    const unsigned char *packed_bits,
    size_t n_symbols,
    qam_symbol_t *symbols
)
{
    for (size_t i = 0; i < n_symbols; i++) {
        symbols[i].real =
            qam256_packed_table[packed_bits[i]].real;

        symbols[i].imag =
            qam256_packed_table[packed_bits[i]].imag;
    }
}


int main(void)
{
    qam256_packed_table_init();

    qam_symbol_t reference;
    qam_symbol_t packed;

    unsigned char bits[8];
    unsigned char packed_byte;

    for (unsigned int value = 0; value < 256; value++) {

        for (int bit = 0; bit < 8; bit++) {
            bits[bit] =
                (unsigned char)((value >> (7 - bit)) & 1);
        }

        if (qam256_map(bits, 8, &reference) != 0) {
            printf("Reference mapper failed for value %u\n", value);
            return 1;
        }

        packed_byte = (unsigned char)value;

        qam256_map_packed(
            &packed_byte,
            1,
            &packed
        );

        if (fabsf(reference.real - packed.real) > 1e-6f ||
            fabsf(reference.imag - packed.imag) > 1e-6f) {

            printf(
                "Mismatch at value %u: "
                "reference=(%.9f, %.9f), "
                "packed=(%.9f, %.9f)\n",
                value,
                reference.real,
                reference.imag,
                packed.real,
                packed.imag
            );

            return 1;
        }
    }

    printf("256-QAM packed-byte exhaustive cross-check: PASS\n");

    return 0;
}
