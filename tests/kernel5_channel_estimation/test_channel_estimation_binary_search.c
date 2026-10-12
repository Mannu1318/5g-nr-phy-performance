#include "channel_estimation.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    const channel_sample_t pilots[] = {
        {1.0, 0.0},
        {1.0, 0.0},
        {1.0, 0.0},
        {1.0, 0.0}
    };

    /*
     * LS channel estimates at pilot indices 0, 4, 8, and 12:
     * H[0] = 1 + 0j
     * H[4] = 5 + 4j
     * H[8] = 9 + 8j
     * H[12] = 13 + 12j
     */
    const channel_sample_t received[] = {
        {1.0, 0.0},
        {5.0, 4.0},
        {9.0, 8.0},
        {13.0, 12.0}
    };

    const size_t pilot_indices[] = {0, 4, 8, 12};

    /* Deliberately unsorted requests across different intervals. */
    const size_t requested[] = {10, 1, 7, 4, 11, 0, 6, 12, 3};

    const channel_sample_t expected[] = {
        {11.0, 10.0},
        {2.0, 1.0},
        {8.0, 7.0},
        {5.0, 4.0},
        {12.0, 11.0},
        {1.0, 0.0},
        {7.0, 6.0},
        {13.0, 12.0},
        {4.0, 3.0}
    };

    channel_sample_t output[sizeof(requested) / sizeof(requested[0])];
    const size_t n_requests = sizeof(requested) / sizeof(requested[0]);

    int status = estimate_channel(
        pilots,
        received,
        pilot_indices,
        sizeof(pilot_indices) / sizeof(pilot_indices[0]),
        requested,
        n_requests,
        output
    );

    if (status != 0) {
        fprintf(stderr, "FAIL: estimator returned status %d\n", status);
        return EXIT_FAILURE;
    }

    for (size_t i = 0; i < n_requests; ++i) {
        if (fabs(output[i].real - expected[i].real) > 1e-12 ||
            fabs(output[i].imag - expected[i].imag) > 1e-12) {
            fprintf(
                stderr,
                "FAIL: request %zu at subcarrier %zu: "
                "got %.12f + j%.12f, expected %.12f + j%.12f\n",
                i,
                requested[i],
                output[i].real,
                output[i].imag,
                expected[i].real,
                expected[i].imag
            );
            return EXIT_FAILURE;
        }
    }

    printf(
        "PASS: binary search handles %zu unsorted requests "
        "across multiple pilot intervals\n",
        n_requests
    );

    return EXIT_SUCCESS;
}
