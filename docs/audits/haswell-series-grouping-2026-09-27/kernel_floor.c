#define _GNU_SOURCE
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "backend.h"
static double now(clockid_t c){struct timespec t;clock_gettime(c,&t);return t.tv_sec+1e-9*t.tv_nsec;}
int main(void){
 const ap_backend *b=ap_backend_active();size_t n=1024;
 void *p=b->create(n);if(!p)return 2;
 float *d[4];for(int j=0;j<4;j++){if(posix_memalign((void**)&d[j],64,n*sizeof(float)))return 3;for(size_t i=0;i<n;i++)d[j][i]=sinf((float)(i*13+j*97)*.017f);}
 ap_peak out;volatile float sink=0;
 for(int i=0;i<10000;i++){b->binmax_prod(p,d[0],d[1],d[2],d[3],n,0,&out,1,100,924);sink=out.re;}
 printf("{\"backend\":\"%s\",\"n\":%zu,\"iterations\":100000,\"samples\":[",b->name,n);
 for(int k=0;k<9;k++){
 double cpu=now(CLOCK_THREAD_CPUTIME_ID),t=now(CLOCK_MONOTONIC_RAW);
 for(int i=0;i<100000;i++){b->binmax_prod(p,d[0],d[1],d[2],d[3],n,0,&out,1,100,924);sink=out.re;}
 double dt=now(CLOCK_MONOTONIC_RAW)-t,dc=now(CLOCK_THREAD_CPUTIME_ID)-cpu;
 printf("%s{\"ns_per_pair\":%.3f,\"cpu_ns_per_pair\":%.3f,\"check\":%.9g}",k?",":"",dt*1e4,dc*1e4,(double)sink);
 }
 puts("]}");b->destroy(p);for(int j=0;j<4;j++)free(d[j]);return 0;
}
