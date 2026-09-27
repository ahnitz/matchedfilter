#define _GNU_SOURCE
#include <immintrin.h>
#include <x86intrin.h>
#include <time.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>
#include <errno.h>
#include <string.h>
static double now(clockid_t c){struct timespec t;clock_gettime(c,&t);return t.tv_sec+1e-9*t.tv_nsec;}
__attribute__((noinline)) static float peak(long n){
 __asm__ volatile("" : "+r"(n) : : "memory");
 __m256 a=_mm256_set1_ps(0.99999f),b=_mm256_set1_ps(0.00001f);
 __m256 x0=_mm256_set1_ps(1),x1=_mm256_set1_ps(2),x2=_mm256_set1_ps(3),x3=_mm256_set1_ps(4);
 __m256 x4=_mm256_set1_ps(5),x5=_mm256_set1_ps(6),x6=_mm256_set1_ps(7),x7=_mm256_set1_ps(8);
 __m256 x8=_mm256_set1_ps(9),x9=_mm256_set1_ps(10),x10=_mm256_set1_ps(11),x11=_mm256_set1_ps(12);
 for(long i=0;i<n;i++){
#define F(x) x=_mm256_fmadd_ps(x,a,b)
 F(x0);F(x1);F(x2);F(x3);F(x4);F(x5);F(x6);F(x7);F(x8);F(x9);F(x10);F(x11);
#undef F
 }
 x0=_mm256_add_ps(x0,x1);x2=_mm256_add_ps(x2,x3);x4=_mm256_add_ps(x4,x5);
 x6=_mm256_add_ps(x6,x7);x8=_mm256_add_ps(x8,x9);x10=_mm256_add_ps(x10,x11);
 x0=_mm256_add_ps(x0,x2);x4=_mm256_add_ps(x4,x6);x8=_mm256_add_ps(x8,x10);
 x0=_mm256_add_ps(_mm256_add_ps(x0,x4),x8);
 return _mm_cvtss_f32(_mm256_castps256_ps128(x0));
}
int main(void){
 struct perf_event_attr attr={0};attr.type=PERF_TYPE_HARDWARE;attr.size=sizeof(attr);attr.config=PERF_COUNT_HW_CPU_CYCLES;attr.exclude_kernel=1;attr.exclude_hv=1;
 int fd=syscall(__NR_perf_event_open,&attr,0,-1,-1,0);
 printf("{\"hardware_cycles_available\":%s,\"perf_error\":\"%s\",\"iterations\":100000000,\"vector_fmas_per_iteration\":12,\"lanes\":8,\"samples\":[\n",fd>=0?"true":"false",fd>=0?"":strerror(errno));
 volatile float sink=peak(10000000);
 for(int r=0;r<9;r++){
  unsigned aux;uint64_t c0=0,c1=0;if(fd>=0)read(fd,&c0,sizeof(c0));
  double cpu0=now(CLOCK_THREAD_CPUTIME_ID),t0=now(CLOCK_MONOTONIC_RAW);uint64_t tsc0=__rdtscp(&aux);
  sink=peak(100000000);
  uint64_t tsc1=__rdtscp(&aux);double dt=now(CLOCK_MONOTONIC_RAW)-t0,dcpu=now(CLOCK_THREAD_CPUTIME_ID)-cpu0;
  if(fd>=0)read(fd,&c1,sizeof(c1));
  printf("%s{\"seconds\":%.9f,\"thread_seconds\":%.9f,\"gflops\":%.6f,\"tsc_ticks\":%llu,\"core_cycles\":%llu,\"check\":%.6f}",r?",\n":"",dt,dcpu,19.2/dt,(unsigned long long)(tsc1-tsc0),(unsigned long long)(c1-c0),(double)sink);
 }
 puts("\n]}");if(fd>=0)close(fd);return 0;
}
