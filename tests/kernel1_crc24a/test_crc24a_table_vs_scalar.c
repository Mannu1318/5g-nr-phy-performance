#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

uint32_t crc24a(const uint8_t *bits, size_t nbits);

uint32_t crc24a_table_lookup(
    const uint8_t *data,
    size_t nbits);

static void bytes_to_bits(
    const uint8_t *data,
    size_t nbytes,
    uint8_t *bits)
{
    size_t bit_index = 0;

    for (size_t i = 0; i < nbytes; i++)
    {
        for (int bit = 7; bit >= 0; bit--)
        {
            bits[bit_index++] =
                (data[i] >> bit) & 1u;
        }
    }
}

int main(void)
{
    const size_t max_bytes = 4096;

    uint8_t *data =
        malloc(max_bytes);

    uint8_t *bits =
        malloc(max_bytes * 8u);

    if (data == NULL || bits == NULL)
    {
        fprintf(stderr, "Memory allocation failed.\n");
        free(data);
        free(bits);
        return 1;
    }

    /*
     * Deterministic pseudo-random test data.
     * Using a fixed seed makes the test reproducible.
     */
    srand(12345);

    for (size_t i = 0; i < max_bytes; i++)
    {
        data[i] = (uint8_t)(rand() & 0xFF);
    }

    /*
     * Test several byte-aligned and non-byte-aligned
     * input lengths.
     */
    const size_t test_bits[] = {
        0,
        1,
        7,
        8,
        9,
        15,
        16,
        17,
        31,
        32,
        33,
        63,
        64,
        65,
        127,
        128,
        129,
        255,
        256,
        257,
        1023,
        1024,
        1025,
        4095,
        4096,
        32768
    };

    const size_t num_tests =
        sizeof(test_bits) / sizeof(test_bits[0]);

    for (size_t test = 0; test < num_tests; test++)
    {
        size_t nbits = test_bits[test];

        size_t nbytes =
            (nbits + 7u) / 8u;

        bytes_to_bits(data, nbytes, bits);

        uint32_t scalar =
            crc24a(bits, nbits);

        uint32_t table =
            crc24a_table_lookup(data, nbits);

        if (scalar != table)
        {
            printf(
                "FAIL: %zu bits: scalar=0x%06X table=0x%06X\n",
                nbits,
                scalar,
                table);

            free(data);
            free(bits);
            return 1;
        }

        printf(
            "PASS: %zu bits -> 0x%06X\n",
            nbits,
            scalar);
    }

    printf(
        "\nAll %zu CRC24A cross-validation tests passed.\n",
        num_tests);

    free(data);
    free(bits);

    return 0;
}
