#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

uint32_t crc24a(const uint8_t *bits, size_t nbits);

int main(void)
{
    const char *data = "123456789";

    uint8_t bits[72];

    size_t bit_index = 0;

    for (size_t i = 0; data[i] != '\0'; i++)
    {
        uint8_t byte = (uint8_t)data[i];

        for (int bit = 7; bit >= 0; bit--)
        {
            bits[bit_index++] = (byte >> bit) & 1u;
        }
    }

    uint32_t result = crc24a(bits, 72);

    printf("CRC24A: 0x%06X\n", result);

    return 0;
}
