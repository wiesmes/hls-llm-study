#include "gemm.h"

//pragmas introduced to optimize the kernel 
void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            #pragma HLS PIPELINE II=1
            acc_t sum = 0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}