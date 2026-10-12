#include "gemm.h"

void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]) {
    #pragma HLS array_partition variable=A block factor=4
    #pragma HLS array_partition variable=B block factor=4
    #pragma HLS array_partition variable=C block factor=4

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            acc_t sum = 0;
            #pragma HLS pipeline II=1
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}