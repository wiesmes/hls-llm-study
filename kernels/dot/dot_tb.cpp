#include <cstdio>
#include <cmath>
#include "dot.h"

int main(){
    data_t a[N], b[N];
    data_t golden = 0;
    for (int i=0; i<N; i++){
        a[i] = data_t(i*0.5);
        b[i] =data_t(i*0.25 + 1.0);
        golden += a[i] * b[i];
    }


    //run the kernel
    data_t result = dot(a,b);


    // compare the result with the golden value

    if (std :: fabs (result - golden )>1e-5 *std::fabs(golden)){
        printf("MISMATCH: got %f expected %f\n", (double)result, (double)golden);
        return 1;
    } else {
        //pass
        printf("PASS\n");
        return 0;
    }

}