#include "gemm.h"

// CHANGE: Vectorize the inner loop
void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]) {
    #pragma HLS PIPELINE II=1
    #pragma HLS ARRAY_PARTITION variable=A dim=1 complete
    #pragma HLS ARRAY_PARTITION variable=B dim=1 complete
    #pragma HLS ARRAY_PARTITION variable=C dim=1 complete
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            acc_t sum = 0;
            #pragma HLS UNROLL factor=4
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}