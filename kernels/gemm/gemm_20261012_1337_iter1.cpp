#include "gemm.h"

// Use HLS pragmas to optimize the loop
void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]) {
    #pragma HLS array_partition variable=A dim=1
    #pragma HLS array_partition variable=B dim=1
    #pragma HLS array_partition variable=C dim=1

    for (int i = 0; i < N; i++) {
        #pragma HLS unroll factor=4
        for (int j = 0; j < N; j++) {
            acc_t sum = 0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}