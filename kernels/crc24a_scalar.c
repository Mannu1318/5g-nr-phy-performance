#include <stddef.h>
#include <stdint.h>

#define CRC24A_POLY  0x864CFBu
#define CRC24A_WIDTH 24u
#define CRC24A_MASK  ((1u << CRC24A_WIDTH) - 1u)
uint32_t crc24a(const uint8_t *bits, size_t nbits)
{    uint32_t crc = 0u;

    for (size_t i = 0; i < nbits; i++)
    {
        uint32_t bit = (uint32_t)(bits[i] & 1u);

        uint32_t top_bit = (crc >> (CRC24A_WIDTH - 1u)) & 1u;

        crc = (crc << 1u) & CRC24A_MASK;

        if (top_bit ^ bit)
        {
            crc ^= CRC24A_POLY;
        }
    }

    return crc;
}
