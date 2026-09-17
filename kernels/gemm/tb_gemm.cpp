#include <cstdio>
#include "gemm.h"

int main() {
    data_t a[N][N], b[N][N];
    acc_t c[N][N], c_ref[N][N];

    // 1. fill inputs
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            a[i][j] = i + j;
            b[i][j] = i - j;
        }
    }

    // 2. function under test
    gemm(a, b, c);

    // 3. software reference
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            acc_t sum = 0;
            for (int k = 0; k < N; k++) {
                sum += a[i][k] * b[k][j];
            }
            c_ref[i][j] = sum;
        }
    }

    // 4. compare
    int errors = 0;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (c[i][j] != c_ref[i][j]) errors++;
        }
    }

    // 5. report
    if (errors) printf("FAIL: %d mismatches\n", errors);
    else        printf("PASS\n");
    return errors ? 1 : 0;
}