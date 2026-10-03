#include <stddef.h>
#include <stdint.h>

#define CRC24A_POLY  0x864CFBu
#define CRC24A_WIDTH 24u
#define CRC24A_MASK  ((1u << CRC24A_WIDTH) - 1u)

static uint32_t crc24a_table[256];
static int table_initialized = 0;


/*
 * Process one input bit using the same CRC24A definition
 * as the established scalar reference implementation.
 */
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


/*
 * Build the CRC contribution table.
 *
 * table[x] is the CRC produced by processing the eight
 * bits of byte x starting from a CRC value of zero.
 */
static void crc24a_init_table(void)
{
    if (table_initialized)
    {
        return;
    }

    for (unsigned int byte = 0; byte < 256u; byte++)
    {
        uint32_t crc = 0u;

        for (int bit = 7; bit >= 0; bit--)
        {
            uint32_t input_bit =
                (byte >> bit) & 1u;

            crc = crc24a_process_bit(crc, input_bit);
        }

        crc24a_table[byte] = crc;
    }

    table_initialized = 1;
}


uint32_t crc24a_table_lookup(
    const uint8_t *data,
    size_t nbits)
{
    crc24a_init_table();

    uint32_t crc = 0u;

    size_t full_bytes = nbits / 8u;

    /*
     * Process complete bytes using one table lookup
     * per byte.
     */
    for (size_t i = 0; i < full_bytes; i++)
    {
        uint32_t byte = data[i];

        uint32_t table_index =
            ((crc >> 16u) ^ byte) & 0xFFu;

        crc =
            ((crc << 8u) & CRC24A_MASK)
            ^ crc24a_table[table_index];
    }

    /*
     * Process any remaining bits using the original
     * bit-by-bit method.
     */
    size_t remaining_bits = nbits % 8u;

    if (remaining_bits != 0u)
    {
        uint8_t byte = data[full_bytes];

        for (size_t bit = 0; bit < remaining_bits; bit++)
        {
            uint32_t input_bit =
                (byte >> (7u - bit)) & 1u;

            crc = crc24a_process_bit(crc, input_bit);
        }
    }

    return crc;
}
