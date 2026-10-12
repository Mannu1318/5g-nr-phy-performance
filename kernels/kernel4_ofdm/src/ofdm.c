
#include "ofdm.h"

#include <math.h>
#include <stdint.h>
#include <stdlib.h>

/*
 * Check whether n is a nonzero power of two.
 *
 * Radix-2 FFT requires the transform length to be a power of two.
 */
static int is_power_of_two(size_t n)
{
    return n != 0 && (n & (n - 1)) == 0;
}

/*
 * Reverse the lowest 'bits' bits of value.
 *
 * Example:
 *   value = 3 (binary 011), bits = 3
 *   result = 6 (binary 110)
 */
static size_t reverse_bits(size_t value, unsigned int bits)
{
    size_t reversed = 0;

    for (unsigned int i = 0; i < bits; ++i) {
        reversed = (reversed << 1) | (value & 1U);
        value >>= 1;
    }

    return reversed;
}

/*
 * Forward radix-2 Cooley-Tukey FFT.
 *
 * Convention:
 *   X[k] = sum(x[n] * exp(-j * 2*pi*k*n/N))
 *
 * The forward FFT is unnormalized.
 */
int ofdm_fft(
    const ofdm_sample_t *samples,
    ofdm_sample_t *output,
    size_t n
)
{
    if (samples == NULL || output == NULL || !is_power_of_two(n)) {
        return -1;
    }

    /* Find the number of bits required to represent indices 0..n-1. */
    unsigned int bits = 0;
    for (size_t temp = n; temp > 1; temp >>= 1) {
        ++bits;
    }

    /*
     * Step 1: Copy input samples into bit-reversed order.
     * Use separate input and output arrays.
     */
    for (size_t i = 0; i < n; ++i) {
        size_t reversed = reverse_bits(i, bits);
        output[reversed] = samples[i];
    }

    /*
     * Step 2: Perform iterative butterfly stages.
     * Each stage doubles the butterfly group length.
     */



    for (size_t len = 2; len <= n; len *= 2) {
        size_t half = len / 2;
        double angle_step = -2.0 * acos(-1.0) / (double)len;

        for (size_t j = 0; j < half; ++j) {
            double angle = angle_step * (double)j;
            double wr = cos(angle);
            double wi = sin(angle);

            for (size_t base = 0; base < n; base += len) {
                size_t even_index = base + j;
                size_t odd_index = even_index + half;

                double even_real = output[even_index].real;
                double even_imag = output[even_index].imag;
                double odd_real = output[odd_index].real;
                double odd_imag = output[odd_index].imag;

                /* Multiply the odd sample by the complex twiddle factor. */
                double temp_real = wr * odd_real - wi * odd_imag;
                double temp_imag = wr * odd_imag + wi * odd_real;

                /* Butterfly: sum and difference. */
                output[even_index].real = even_real + temp_real;
                output[even_index].imag = even_imag + temp_imag;

                output[odd_index].real = even_real - temp_real;
                output[odd_index].imag = even_imag - temp_imag;
            }
        }

        if (len == n) {
            break;  /* Avoid overflowing len when doubling the final stage. */
        }
    }
    return 0;
}

/*
 * Inverse FFT using the forward FFT:
 *
 * IFFT(X) = conjugate(FFT(conjugate(X))) / N
 *
 * The inverse transform is normalized by 1/N.
 */
int ofdm_ifft(
    const ofdm_sample_t *symbols,
    ofdm_sample_t *output,
    size_t n
)
{
    if (symbols == NULL || output == NULL || !is_power_of_two(n)) {
        return -1;
    }

    /* Allocate a temporary buffer for the conjugated input. */
    ofdm_sample_t *temp = malloc(n * sizeof(*temp));
    if (temp == NULL) {
        return -1;
    }

    for (size_t i = 0; i < n; ++i) {
        temp[i].real = symbols[i].real;
        temp[i].imag = -symbols[i].imag;
    }

    /* Compute the forward FFT of the conjugated input. */
    int status = ofdm_fft(temp, output, n);
    free(temp);

    if (status != 0) {
        return status;
    }

    /* Conjugate the output and normalize by N. */
    for (size_t i = 0; i < n; ++i) {
        output[i].real /= (double)n;
        output[i].imag = -output[i].imag / (double)n;
    }

    return 0;
}

/*
 * Validate subcarrier indices.
 *
 * Returns:
 *   0  if all indices are unique and in range
 *  -1  if memory allocation fails
 *  -2  if an index is out of range or duplicated
 */
static int validate_bin_indices(
    const size_t *bin_indices,
    size_t n_data,
    size_t n_fft
)
{
    unsigned char *seen = calloc(n_fft, sizeof(*seen));

    if (seen == NULL) {
        return -1;
    }

    for (size_t i = 0; i < n_data; ++i) {
        size_t bin = bin_indices[i];

        if (bin >= n_fft || seen[bin]) {
            free(seen);
            return -2;
        }

        seen[bin] = 1;
    }

    free(seen);
    return 0;
}

/*
 * Map data symbols into FFT bins.
 *
 * All output bins are initialized to zero. Data symbols are then
 * placed at the requested bin indices.
 */
int ofdm_map_subcarriers(
    const ofdm_sample_t *data,
    size_t n_data,
    const size_t *bin_indices,
    size_t n_fft,
    ofdm_sample_t *output
)
{
    if (data == NULL || bin_indices == NULL || output == NULL ||
        n_fft == 0 || n_data > n_fft) {
        return -1;
    }

    int status = validate_bin_indices(bin_indices, n_data, n_fft);
    if (status != 0) {
        return status;
    }

    for (size_t i = 0; i < n_fft; ++i) {
        output[i].real = 0.0;
        output[i].imag = 0.0;
    }

    for (size_t i = 0; i < n_data; ++i) {
        output[bin_indices[i]] = data[i];
    }

    return 0;
}

/*
 * Extract data symbols from selected FFT bins.
 */
int ofdm_extract_subcarriers(
    const ofdm_sample_t *fft_output,
    size_t n_fft,
    const size_t *bin_indices,
    size_t n_data,
    ofdm_sample_t *output
)
{
    if (fft_output == NULL || bin_indices == NULL || output == NULL ||
        n_fft == 0 || n_data > n_fft) {
        return -1;
    }

    int status = validate_bin_indices(bin_indices, n_data, n_fft);
    if (status != 0) {
        return status;
    }

    for (size_t i = 0; i < n_data; ++i) {
        output[i] = fft_output[bin_indices[i]];
    }

    return 0;
}

/*
 * Add a cyclic prefix by copying the final cp_len samples
 * to the beginning of the output.
 *
 * Output length: n + cp_len
 */
int ofdm_add_cyclic_prefix(
    const ofdm_sample_t *samples,
    size_t n,
    size_t cp_len,
    ofdm_sample_t *output
)
{
    if (samples == NULL || output == NULL || n == 0 || cp_len > n) {
        return -1;
    }

    /* Copy the cyclic prefix from the end of the input. */
    for (size_t i = 0; i < cp_len; ++i) {
        output[i] = samples[n - cp_len + i];
    }

    /* Append the complete original OFDM symbol. */
    for (size_t i = 0; i < n; ++i) {
        output[cp_len + i] = samples[i];
    }

    return 0;
}

/*
 * Remove a cyclic prefix.
 *
 * Input length:  n + cp_len
 * Output length: n
 */
int ofdm_remove_cyclic_prefix(
    const ofdm_sample_t *samples,
    size_t n,
    size_t cp_len,
    ofdm_sample_t *output
)
{
    if (samples == NULL || output == NULL || n == 0 || cp_len > n) {
        return -1;
    }

    for (size_t i = 0; i < n; ++i) {
        output[i] = samples[cp_len + i];
    }

    return 0;
}
