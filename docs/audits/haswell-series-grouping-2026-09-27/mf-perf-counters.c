#include <linux/perf_event.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdint.h>
static int fds[4]={-1,-1,-1,-1};
int init_counters(void){int events[4]={PERF_COUNT_HW_CPU_CYCLES,PERF_COUNT_HW_INSTRUCTIONS,PERF_COUNT_HW_BRANCH_MISSES,PERF_COUNT_HW_CACHE_MISSES};for(int i=0;i<4;i++){struct perf_event_attr a={0};a.type=PERF_TYPE_HARDWARE;a.size=sizeof(a);a.config=events[i];a.exclude_kernel=1;a.exclude_hv=1;a.read_format=PERF_FORMAT_TOTAL_TIME_ENABLED|PERF_FORMAT_TOTAL_TIME_RUNNING;fds[i]=syscall(__NR_perf_event_open,&a,0,-1,-1,0);if(fds[i]<0)return -1;}return 0;}
int read_counters(uint64_t*out){for(int i=0;i<4;i++)if(read(fds[i],out+3*i,24)!=24)return -1;return 0;}
