#include <stddef.h>
#include <stdint.h>

#define CRC24A_POLY  0x864CFBu
#define CRC24A_WIDTH 24u
#define CRC24A_MASK  ((1u << CRC24A_WIDTH) - 1u)

static uint32_t crc24a_process_bit(
    uint32_t crc,
    uint32_t input_bit)
{
    uint32_t top_bit =
        (crc >> (CRC24A_WIDTH - 1u)) & 1u;

    crc = (crc << 1u) & CRC24A_MASK;

    if (top_bit ^ input_bit)
    {
        crc ^= CRC24A_POLY;
    }

    return crc;
}

uint32_t crc24a_unrolled(const uint8_t *data, size_t nbits)
{
    uint32_t crc = 0u;

    size_t full_bytes = nbits / 8u;

    for (size_t i = 0; i < full_bytes; i++)
    {
        uint8_t byte = data[i];

        crc = crc24a_process_bit(crc, (byte >> 7u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 6u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 5u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 4u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 3u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 2u) & 1u);
        crc = crc24a_process_bit(crc, (byte >> 1u) & 1u);
        crc = crc24a_process_bit(crc, byte & 1u);
    }

    size_t remaining_bits = nbits % 8u;

    if (remaining_bits != 0u)
    {
        uint8_t byte = data[full_bytes];

        for (size_t bit = 0; bit < remaining_bits; bit++)
        {
            size_t bit_position = 7u - bit;

            crc = crc24a_process_bit(
                crc,
                (byte >> bit_position) & 1u);
        }
    }

    return crc;
}
