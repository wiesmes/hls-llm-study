#include <cstdio>
#include <cmath>
#include "vecadd.h"

// THE CORRECTNESS GATE.
// Returning non-zero makes csim_design fail, which stops the flow.
// A design that computes the wrong answer must never reach synthesis
// and must never contribute a row to results.csv.

int main() {
    data_t a[N], b[N], c[N], golden[N];

    for (int i = 0; i < N; i++) {
        a[i] = (data_t)(i * 0.5);
        b[i] = (data_t)(i * 0.25 + 1.0);
        golden[i] = a[i] + b[i];   // reference answer
    }

    vecadd(a, b, c);

    int errors = 0;
    for (int i = 0; i < N; i++) {
        if (std::fabs(c[i] - golden[i]) > 1e-4) {
            if (errors < 10)
                printf("MISMATCH at %d: got %f expected %f\n",
                       i, (double)c[i], (double)golden[i]);
            errors++;
        }
    }

    if (errors == 0) {
        printf("PASS\n");
        return 0;
    } else {
        printf("FAIL: %d mismatches\n", errors);
        return 1;
    }
}
