#include "mimo_zf_scalar.h"

#include <complex.h>
#include <stdio.h>

int main(void)
{
    size_t count;

    if (scanf("%zu", &count) != 1) {
        fprintf(stderr, "Failed to read test-case count.\n");
        return 1;
    }

    for (size_t i = 0; i < count; ++i) {
        double values[12];

        for (size_t j = 0; j < 12; ++j) {
            if (scanf("%lf", &values[j]) != 1) {
                fprintf(stderr, "Failed to read test case %zu.\n", i);
                return 1;
            }
        }

        double complex H[4];
        double complex y[2];
        double complex x_hat[2];

        for (size_t j = 0; j < 4; ++j) {
            H[j] = values[2 * j] + values[2 * j + 1] * I;
        }

        for (size_t j = 0; j < 2; ++j) {
            y[j] = values[8 + 2 * j] + values[9 + 2 * j] * I;
        }

        zf_status status = zf_detect_single(H, y, x_hat);

        printf("%d %.17g %.17g %.17g %.17g\n",
               (int)status,
               creal(x_hat[0]), cimag(x_hat[0]),
               creal(x_hat[1]), cimag(x_hat[1]));
    }

    return 0;
}
