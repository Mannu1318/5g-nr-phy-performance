#include <stdint.h>
#include <stdio.h>
#include <stddef.h>

uint32_t crc24a_packed(const uint8_t *data, size_t nbits);

int main(void)
{
    const char *data = "123456789";

    uint32_t result =
        crc24a_packed((const uint8_t *)data, 72);

    printf("CRC24A packed: 0x%06X\n", result);

    return 0;
}
