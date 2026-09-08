#include "vecadd.h"

// Throwaway kernel used only to prove the harness works end to end.
// No pragmas on purpose -- this is a "naive" design.



void vecadd(const data_t a[N], const data_t b[N], data_t c[N]) {
    #pragma HLS INTERFACE m_axi     port=a offset=slave bundle=gmem0
    #pragma HLS INTERFACE m_axi     port=b offset=slave bundle=gmem1
    #pragma HLS INTERFACE m_axi     port=c offset=slave bundle=gmem2
    #pragma HLS INTERFACE s_axilite port=a
    #pragma HLS INTERFACE s_axilite port=b
    #pragma HLS INTERFACE s_axilite port=c
    #pragma HLS INTERFACE s_axilite port=return
    
    for (int i = 0; i < N; i++) {
        c[i] = a[i] + b[i];
    }
}
