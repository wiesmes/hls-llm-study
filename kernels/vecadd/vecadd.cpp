#include "vecadd.h"

// Throwaway kernel used only to prove the harness works end to end.
// No pragmas on purpose -- this is a "naive" design.
void vecadd(const data_t a[N], const data_t b[N], data_t c[N]) {
    for (int i = 0; i < N; i++) {
        c[i] = a[i] + b[i];
    }
}
