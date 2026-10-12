
#include "ofdm.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define TOLERANCE 1e-9

static int tests_passed = 0;
static int tests_failed = 0;

static void check(int condition, const char *test_name)
{
    if (condition) {
        printf("PASS: %s\n", test_name);
        ++tests_passed;
    } else {
        printf("FAIL: %s\n", test_name);
        ++tests_failed;
    }
}

static int close_enough(double a, double b)
{
    return fabs(a - b) < TOLERANCE;
}

static int samples_equal(
    const ofdm_sample_t *a,
    const ofdm_sample_t *b,
    size_t n
)
{
    for (size_t i = 0; i < n; ++i) {
        if (!close_enough(a[i].real, b[i].real) ||
            !close_enough(a[i].imag, b[i].imag)) {
            return 0;
        }
    }

    return 1;
}

static void test_fft_known_values(void)
{
    /*
     * FFT of [1, 1, 1, 1] is [4, 0, 0, 0].
     */
    const ofdm_sample_t input[4] = {
        {1.0, 0.0}, {1.0, 0.0},
        {1.0, 0.0}, {1.0, 0.0}
    };

    const ofdm_sample_t expected[4] = {
        {4.0, 0.0}, {0.0, 0.0},
        {0.0, 0.0}, {0.0, 0.0}
    };

    ofdm_sample_t output[4];

    int status = ofdm_fft(input, output, 4);

    check(status == 0 && samples_equal(output, expected, 4),
          "FFT known values for constant input");
}

static void test_fft_ifft_round_trip(void)
{
    const ofdm_sample_t input[8] = {
        {1.0, 0.5}, {-2.0, 1.0},
        {0.25, -0.75}, {3.0, 2.0},
        {-1.0, -1.0}, {0.5, 0.25},
        {2.0, -0.5}, {-0.25, 1.5}
    };

    ofdm_sample_t frequency[8];
    ofdm_sample_t recovered[8];

    int fft_status = ofdm_fft(input, frequency, 8);
    int ifft_status = ofdm_ifft(frequency, recovered, 8);

    check(fft_status == 0 && ifft_status == 0 &&
          samples_equal(input, recovered, 8),
          "FFT/IFFT round-trip reconstruction");
}

static void test_fft_impulse(void)
{
    /*
     * FFT of a unit impulse at index zero is all ones.
     */
    const ofdm_sample_t input[4] = {
        {1.0, 0.0}, {0.0, 0.0},
        {0.0, 0.0}, {0.0, 0.0}
    };

    const ofdm_sample_t expected[4] = {
        {1.0, 0.0}, {1.0, 0.0},
        {1.0, 0.0}, {1.0, 0.0}
    };

    ofdm_sample_t output[4];

    int status = ofdm_fft(input, output, 4);

    check(status == 0 && samples_equal(output, expected, 4),
          "FFT of unit impulse");
}

static void test_invalid_fft_length(void)
{
    const ofdm_sample_t input[3] = {
        {1.0, 0.0}, {2.0, 0.0}, {3.0, 0.0}
    };
    ofdm_sample_t output[3];

    check(ofdm_fft(input, output, 3) == -1,
          "FFT rejects non-power-of-two length");
}

static void test_subcarrier_mapping(void)
{
    const ofdm_sample_t data[2] = {
        {1.0, 2.0}, {3.0, 4.0}
    };
    const size_t bins[2] = {1, 3};

    const ofdm_sample_t expected[4] = {
        {0.0, 0.0}, {1.0, 2.0},
        {0.0, 0.0}, {3.0, 4.0}
    };

    ofdm_sample_t mapped[4];

    int status = ofdm_map_subcarriers(data, 2, bins, 4, mapped);

    check(status == 0 && samples_equal(mapped, expected, 4),
          "Subcarrier mapping and zero-filled unused bins");
}

static void test_subcarrier_extraction(void)
{
    const ofdm_sample_t frequency[4] = {
        {10.0, 0.0}, {1.0, 2.0},
        {20.0, 0.0}, {3.0, 4.0}
    };
    const size_t bins[2] = {1, 3};

    const ofdm_sample_t expected[2] = {
        {1.0, 2.0}, {3.0, 4.0}
    };

    ofdm_sample_t extracted[2];

    int status = ofdm_extract_subcarriers(
        frequency, 4, bins, 2, extracted
    );

    check(status == 0 && samples_equal(extracted, expected, 2),
          "Subcarrier extraction");
}

static void test_cyclic_prefix_round_trip(void)
{
    const ofdm_sample_t input[4] = {
        {1.0, 0.0}, {2.0, 0.0},
        {3.0, 0.0}, {4.0, 0.0}
    };

    const ofdm_sample_t expected_with_cp[6] = {
        {3.0, 0.0}, {4.0, 0.0},
        {1.0, 0.0}, {2.0, 0.0},
        {3.0, 0.0}, {4.0, 0.0}
    };

    ofdm_sample_t with_cp[6];
    ofdm_sample_t recovered[4];

    int add_status = ofdm_add_cyclic_prefix(input, 4, 2, with_cp);
    int remove_status = ofdm_remove_cyclic_prefix(
        with_cp, 4, 2, recovered
    );

    check(add_status == 0 &&
          samples_equal(with_cp, expected_with_cp, 6),
          "Cyclic-prefix insertion");

    check(remove_status == 0 && samples_equal(input, recovered, 4),
          "Cyclic-prefix removal");
}


static void test_invalid_inputs(void)
{
    const ofdm_sample_t samples[4] = {
        {1.0, 0.0}, {2.0, 0.0},
        {3.0, 0.0}, {4.0, 0.0}
    };
    ofdm_sample_t output[4];

    check(ofdm_fft(NULL, output, 4) == -1,
          "FFT rejects NULL input");

    check(ofdm_ifft(samples, output, 0) == -1,
          "IFFT rejects zero transform length");

    check(ofdm_add_cyclic_prefix(samples, 4, 5, output) == -1,
          "Cyclic-prefix insertion rejects cp_len greater than n");

    check(ofdm_remove_cyclic_prefix(samples, 4, 5, output) == -1,
          "Cyclic-prefix removal rejects cp_len greater than n");
}

static void test_invalid_subcarrier_indices(void)
{
    const ofdm_sample_t data[2] = {
        {1.0, 0.0}, {2.0, 0.0}
    };
    ofdm_sample_t output[4];

    const size_t out_of_range[2] = {1, 4};
    const size_t duplicate[2] = {2, 2};

    check(ofdm_map_subcarriers(data, 2, out_of_range, 4, output) == -2,
          "Mapping rejects out-of-range bin index");

    check(ofdm_map_subcarriers(data, 2, duplicate, 4, output) == -2,
          "Mapping rejects duplicate bin indices");

    check(ofdm_extract_subcarriers(
              data, 4, out_of_range, 2, output
          ) == -2,
          "Extraction rejects out-of-range bin index");

    check(ofdm_extract_subcarriers(
              data, 4, duplicate, 2, output
          ) == -2,
          "Extraction rejects duplicate bin indices");
}

int main(void)
{
    printf("Kernel 4: OFDM C correctness tests\n\n");

    test_fft_known_values();
    test_fft_ifft_round_trip();
    test_fft_impulse();
    test_invalid_fft_length();
    test_subcarrier_mapping();
    test_subcarrier_extraction();
    test_cyclic_prefix_round_trip();
    test_invalid_inputs();
    test_invalid_subcarrier_indices();
    printf("\nResults: %d passed, %d failed\n",
           tests_passed, tests_failed);

    return tests_failed == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
}
