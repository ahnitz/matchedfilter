#define _GNU_SOURCE
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <dlfcn.h>
#include "backend.h"
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return t.tv_sec+1e-9*t.tv_nsec;}
int main(int argc,char **argv){
 if(argc!=3 && argc!=4)return 2;
 float threshold=argc==4 ? strtof(argv[3],NULL) : 0;
 const ap_backend *b[2];void *handle[2],*p[5][2];
 for(int j=0;j<2;j++){handle[j]=dlopen(argv[j+1],RTLD_NOW|RTLD_LOCAL);if(!handle[j]){fprintf(stderr,"%s\n",dlerror());return 3;}const ap_backend *(*active)(void)=dlsym(handle[j],"ap_backend_active");if(!active)return 4;b[j]=active();}
 for(int l=0;l<5;l++)for(int k=0;k<2;k++){int j=k^(l&1);p[l][j]=b[j]->create(1024);if(!p[l][j])return 5;}
 float *d[4];for(int j=0;j<4;j++){if(posix_memalign((void**)&d[j],64,1024*sizeof(float)))return 6;for(int i=0;i<1024;i++)d[j][i]=sinf((float)(i*13+j*97)*.017f);}
 ap_peak out[2];
 for(int l=0;l<5;l++){
  for(int j=0;j<2;j++)for(int k=0;k<1000;k++)b[j]->binmax_prod(p[l][j],d[0],d[1],d[2],d[3],1024,threshold,&out[j],1,100,924);
  if(out[0].index!=out[1].index || fabsf(out[0].re-out[1].re)>1e-3f || fabsf(out[0].im-out[1].im)>1e-3f)return 7;
 }
 printf("{\"threshold\":%.9g,\"iterations\":10000,\"layouts\":5,\"rounds\":21,\"backend\":[\"%s\",\"%s\"],\"samples\":[",(double)threshold,b[0]->name,b[1]->name);
 for(int r=0;r<21;r++)for(int l=0;l<5;l++){
  double t[2];
  for(int k=0;k<2;k++){int j=k^(r&1);double start=now();for(int i=0;i<10000;i++)b[j]->binmax_prod(p[l][j],d[0],d[1],d[2],d[3],1024,threshold,&out[j],1,100,924);t[j]=(now()-start)*1e5;}
  printf("%s{\"round\":%d,\"layout\":%d,\"baseline_ns\":%.3f,\"candidate_ns\":%.3f}",r||l?",":"",r,l,t[0],t[1]);
 }
 puts("]}");for(int l=0;l<5;l++)for(int j=0;j<2;j++)b[j]->destroy(p[l][j]);for(int j=0;j<4;j++)free(d[j]);for(int j=0;j<2;j++)dlclose(handle[j]);return 0;
}
