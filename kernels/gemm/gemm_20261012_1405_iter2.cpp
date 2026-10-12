#include "gemm.h"

void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]) {
    #pragma HLS array_partition variable=A dim=1 complete
    #pragma HLS array_partition variable=B dim=1 complete
    #pragma HLS dataflow
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            acc_t sum = 0;
            for (int k = 0; k < N; k++) {
                #pragma HLS unroll factor=8
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}