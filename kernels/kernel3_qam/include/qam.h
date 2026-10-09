#ifndef QAM_H
#define QAM_H

#include <stddef.h>

/*
 * 5G NR QAM Mapping and Demapping
 *
 * Supported modulation orders:
 *   QPSK
 *   16-QAM
 *   64-QAM
 *   256-QAM
 *
 * The implementation uses normalized complex symbols.
 */

/* Complex symbol represented by separate float components. */
typedef struct {
    float real;
    float imag;
} qam_symbol_t;

/*
 * QPSK
 *
 * Input:
 *   bits      - input bits
 *   n_bits    - number of input bits
 *   symbols   - output QPSK symbols
 *
 * Returns:
 *   0  on success
 *  -1  if n_bits is not divisible by 2
 *  -2  if an input bit is not 0 or 1
 */
int qpsk_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
);

int qpsk_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
);


/* 16-QAM */

int qam16_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
);

int qam16_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
);


/* 64-QAM */

int qam64_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
);

int qam64_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
);


/* 256-QAM */

int qam256_map(
    const unsigned char *bits,
    size_t n_bits,
    qam_symbol_t *symbols
);

int qam256_demap(
    const qam_symbol_t *symbols,
    size_t n_symbols,
    unsigned char *bits
);

#endif /* QAM_H */
