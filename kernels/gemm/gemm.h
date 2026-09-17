#ifndef GEMM_H
#define GEMM_H

#include <stdint.h> // Include the header for fixed-width integer types

#define N 32            //  Matrix size (32x32)
typedef int16_t data_t; // input element type
typedef int32_t acc_t; // accumulator/output type (avoids overflow)


void gemm(data_t A[N][N], data_t B[N][N], acc_t C[N][N]);

#endif // GEMM_H