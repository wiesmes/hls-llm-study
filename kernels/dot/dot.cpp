#include "dot.h"

data_t dot(const data_t a[N], const data_t b[N]){
    data_t sum = 0;
    for (int i=0; i<N; i++){
        sum += a[i] *b[i];
    }
    return sum;
    
}