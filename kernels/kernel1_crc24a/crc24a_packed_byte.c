#include <stddef.h>
#include <stdint.h>

#define CRC24A_POLY  0x864CFBu
#define CRC24A_WIDTH 24u
#define CRC24A_MASK  ((1u << CRC24A_WIDTH) - 1u)

uint32_t crc24a_packed_byte(const uint8_t *data, size_t nbits)
{
    uint32_t crc = 0u;

    size_t full_bytes = nbits / 8u;

    for (size_t i = 0; i < full_bytes; i++)
    {
        uint8_t byte = data[i];

        for (int bit = 7; bit >= 0; bit--)
        {
            uint32_t input_bit =
                (uint32_t)((byte >> bit) & 1u);

            uint32_t top_bit =
                (crc >> (CRC24A_WIDTH - 1u)) & 1u;

            crc = (crc << 1u) & CRC24A_MASK;

            if (top_bit ^ input_bit)
            {
                crc ^= CRC24A_POLY;
            }
        }
    }

    size_t remaining_bits = nbits % 8u;

    if (remaining_bits != 0u)
    {
        uint8_t byte = data[full_bytes];

        for (size_t bit = 0; bit < remaining_bits; bit++)
        {
            size_t bit_position = 7u - bit;

            uint32_t input_bit =
                (uint32_t)((byte >> bit_position) & 1u);

            uint32_t top_bit =
                (crc >> (CRC24A_WIDTH - 1u)) & 1u;

            crc = (crc << 1u) & CRC24A_MASK;

            if (top_bit ^ input_bit)
            {
                crc ^= CRC24A_POLY;
            }
        }
    }

    return crc;
}
