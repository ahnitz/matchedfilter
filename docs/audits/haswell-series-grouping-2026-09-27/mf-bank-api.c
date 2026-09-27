#define _GNU_SOURCE
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <dlfcn.h>
#include "matchedfilter.h"
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC_RAW,&t);return t.tv_sec+1e-9*t.tv_nsec;}
int main(int argc,char**argv){
 if(argc!=3)return 2;
 ap_mf_plan *p[5][2]; void*h[2];
 ap_mf_plan *(*create[2])(size_t,int,int);
 int(*data[2])(ap_mf_plan*,int,const float*),(*tmpl[2])(ap_mf_plan*,int,const float*);
 int(*run[2])(ap_mf_plan*,int,int,int,int,size_t,float,ap_peak*,int*,size_t,size_t);
 void(*destroy[2])(ap_mf_plan*);
 for(int j=0;j<2;j++){h[j]=dlopen(argv[j+1],RTLD_NOW|RTLD_LOCAL);if(!h[j]){puts(dlerror());return 3;}create[j]=dlsym(h[j],"ap_mf_create");data[j]=dlsym(h[j],"ap_mf_set_data");tmpl[j]=dlsym(h[j],"ap_mf_set_template");run[j]=dlsym(h[j],"ap_mf_run");destroy[j]=dlsym(h[j],"ap_mf_destroy");if(!create[j]||!run[j])return 4;}
 float spec[45][2048];unsigned seed=169;for(int j=0;j<45;j++)for(int i=0;i<2048;i++){seed=1664525u*seed+1013904223u;spec[j][i]=(float)(seed>>8)*(2.f/16777216.f)-1.f;}
 ap_peak out[2][296];
 for(int l=0;l<5;l++)for(int k=0;k<2;k++){int j=k^(l&1);p[l][j]=create[j](1024,8,37);if(!p[l][j])return 5;for(int i=0;i<8;i++)if(data[j](p[l][j],i,spec[i]))return 6;for(int i=0;i<37;i++)if(tmpl[j](p[l][j],i,spec[8+i]))return 7;for(int i=0;i<20;i++)if(run[j](p[l][j],0,8,0,37,1024,0,out[j],NULL,0,1024)<0)return 8;}
 for(int i=0;i<296;i++)if(out[0][i].index!=out[1][i].index||fabsf(out[0][i].re-out[1][i].re)>1e-3f||fabsf(out[0][i].im-out[1][i].im)>1e-3f)return 9;
 printf("{\"samples\":[");
 for(int r=0;r<21;r++)for(int l=0;l<5;l++){double t[2];for(int k=0;k<2;k++){int j=k^(r&1);double s=now();for(int i=0;i<100;i++)run[j](p[l][j],0,8,0,37,1024,0,out[j],NULL,0,1024);t[j]=(now()-s)*1e9/(100*296);}printf("%s{\"round\":%d,\"layout\":%d,\"baseline_ns\":%.3f,\"candidate_ns\":%.3f}",r||l?",":"",r,l,t[0],t[1]);}
 puts("]}");for(int l=0;l<5;l++)for(int j=0;j<2;j++)destroy[j](p[l][j]);return 0;
}
