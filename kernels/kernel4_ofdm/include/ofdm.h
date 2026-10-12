
#ifndef OFDM_H
#define OFDM_H

#include <stddef.h>

/*
 * 5G NR OFDM FFT/IFFT Kernel
 *
 * Complex samples use double-precision real and imaginary components.
 * FFT:  forward transform, unnormalized.
 * IFFT: inverse transform, normalized by 1/N.
 */

typedef struct {
    double real;
    double imag;
} ofdm_sample_t;

/*
 * FFT/IFFT
 *
 * samples: input complex samples
 * output:  output complex samples; must have room for n samples
 * n:       transform length; must be a power of two
 *
 * Returns:
 *   0  on success
 *  -1  if pointers are NULL or n is invalid
 */
int ofdm_fft(
    const ofdm_sample_t *samples,
    ofdm_sample_t *output,
    size_t n
);

int ofdm_ifft(
    const ofdm_sample_t *symbols,
    ofdm_sample_t *output,
    size_t n
);

/*
 * Subcarrier mapping/extraction
 *
 * bin_indices contains n_data FFT-bin indices, each in [0, n_fft).
 * Mapping initializes all FFT bins to zero before placing data symbols.
 *
 * Returns:
 *   0  on success
 *  -1  for invalid pointers or sizes
 *  -2  for an out-of-range or duplicate bin index
 */
int ofdm_map_subcarriers(
    const ofdm_sample_t *data,
    size_t n_data,
    const size_t *bin_indices,
    size_t n_fft,
    ofdm_sample_t *output
);

int ofdm_extract_subcarriers(
    const ofdm_sample_t *fft_output,
    size_t n_fft,
    const size_t *bin_indices,
    size_t n_data,
    ofdm_sample_t *output
);

/*
 * Cyclic-prefix insertion/removal
 *
 * add:    output length is n + cp_len
 * remove: input length is n + cp_len; output length is n
 *
 * Returns:
 *   0  on success
 *  -1  for invalid pointers, sizes, or cp_len > n
 */
int ofdm_add_cyclic_prefix(
    const ofdm_sample_t *samples,
    size_t n,
    size_t cp_len,
    ofdm_sample_t *output
);

int ofdm_remove_cyclic_prefix(
    const ofdm_sample_t *samples,
    size_t n,
    size_t cp_len,
    ofdm_sample_t *output
);

#endif /* OFDM_H */
