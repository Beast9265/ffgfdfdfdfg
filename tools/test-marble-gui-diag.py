#!/usr/bin/env python3
"""Compile/run actual MARBLE diagnostic helpers with host stubs and sanitizers.
Usage: python3 tools/test-marble-gui-diag.py REPLAYED_XNU_TREE
"""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(sys.argv[1])
mem = (root / 'bsd/dev/mem.c').read_text()
helper = mem[mem.index('bool marble_gui_diag_take'):mem.index('\n#endif\n\nstatic bool\nsweet_null_tee')]
tee = mem[mem.index('static bool\nsweet_null_tee'):mem.index('\nint\nmmrw')].rsplit('#endif', 1)[0]
heap = (root / 'osfmk/kern/exception.c').read_text()
heap = heap[heap.index('static void\nsweet_crash_strings'):heap.index('\n#if defined(ARM64_BOARD_CONFIG_MARBLE)\nvoid marble_crash_strings')]
exit_source = (root / 'bsd/kern/kern_exit.c').read_text()
start = exit_source.index('#if defined(ARM64_BOARD_CONFIG_MARBLE)', exit_source.index('proc_prepareexit(proc_t'))
crash = exit_source[start:exit_source.index('#endif', start)]
crash = crash.split('\n', 1)[1]
prelude = r''' 
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <pthread.h>
#include <signal.h>
#include <sys/wait.h>
#define ARM64_BOARD_CONFIG_MARBLE 1
#define Z_WAITOK 0
#define VM_PROT_READ 1
#define VM_PROT_WRITE 2
#define KERN_SUCCESS 0
#define VM_REGION_SUBMAP_INFO_V2_COUNT_64 1
static int enabled=1, mode, queries, copies, strings, crashes, reasons;
static uint64_t attempted;
static const char *who="Setup";
static const char *names[]={"SpringBoard","backboardd","Setup","nanotimekitcompaniond","maintenanced","ReportCrash","mobileactivationd","installcoordinationd","mediaserverd"};
static int PE_parse_boot_argn(const char *key, int *out, size_t size) { (void)key;(void)size;*out=enabled;return 1; }
static void proc_selfname(char *out,int len) { snprintf(out,(size_t)len,"%s",who); }
static void *kalloc_data(size_t size,int flags) { (void)flags;return malloc(size); }
static void kfree_data(void *p,size_t size) { (void)size;free(p); }
static size_t test_strlcpy(char *out,const char *in,size_t size) { size_t len=strlen(in);if(size)snprintf(out,size,"%s",in);return len; }
#define strlcpy test_strlcpy
static char *strnstr(const char *s,const char *find,size_t size) { (void)size;return strstr(s,find); }
static int diag_print(const char *fmt,...) { if(!strcmp(fmt,"STR %s\n"))strings++;if(!strncmp(fmt,"CRASH ",6)){if(strstr(fmt,"reason ns")){reasons++;va_list args;va_start(args,fmt);(void)va_arg(args,const char *);(void)va_arg(args,unsigned);(void)va_arg(args,uint64_t);const char *text=va_arg(args,const char *);assert(!strpbrk(text,"\n\r"));assert(strlen(text)<=512);va_end(args);}else crashes++;}return 0; }
#define printf diag_print
typedef void *vm_map_t;
typedef uint64_t vm_map_offset_t;
typedef uint64_t vm_map_size_t;
typedef unsigned natural_t;
typedef unsigned mach_msg_type_number_t;
typedef uint64_t user_addr_t;
typedef struct { int is_submap,protection,user_tag; } vm_region_submap_info_data_64_t;
typedef vm_region_submap_info_data_64_t *vm_region_submap_info_64_t;
static vm_map_t current_map(void) { return NULL; }
static int vm_map_region_recurse_64(vm_map_t map,uint64_t *addr,uint64_t *size,unsigned *depth,vm_region_submap_info_64_t info,unsigned *count) {
 (void)map;(void)depth;(void)count;queries++;
 info->is_submap=0;info->protection=3;info->user_tag=1;
 *size=mode==1?0:mode==2?UINT64_MAX:mode==3?1:((32ull<<20)+17);
 if(mode==2)*addr=16;
 if(mode==3)info->protection=0;
 return 0;
}
static int copyin(user_addr_t addr,char *buf,size_t size) {
 (void)addr;copies++;attempted+=size;
 if(mode==4)return 1;
 memset(buf,0,size);
 for(size_t i=0;i+100<size;i+=100)snprintf(buf+i,100,"Exception reason failed container %zu",i);
 return 0;
}
'''
crash_stubs = r'''
#define CS_KILLED 1
#define OS_REASON_FLAG_GENERATE_CRASH_REPORT 2
struct reason { unsigned osr_namespace; uint64_t osr_code; };
struct process { struct reason *p_exit_reason; int flags; };
struct uthread { unsigned uu_exception; uint64_t uu_code, uu_subcode; };
static struct reason test_reason={2,5};
static struct process test_proc={&test_reason,0};
static struct process *current_proc(void) { return &test_proc; }
static int proc_getcsflags(struct process *p) { return p->flags; }
static int proc_getpid(struct process *p) { (void)p;return 42; }
static char *exit_reason_get_string_desc(struct reason *r) { (void)r;return "failure\nreason"; }
#define PROC_HAS_EXITREASON(p) ((p)->p_exit_reason!=NULL)
#define PROC_EXITREASON_FLAGS(p) 0
static void marble_crash_strings(const char *name) { sweet_crash_strings(name); }
static void exit_diag(struct process *p,int rv) {
 struct uthread ut_value={6,1,2};struct uthread *ut=&ut_value;
''' + crash + '\n}\n'
main = r'''
#undef printf
static unsigned shared;
static void *reserve(void *unused) { (void)unused;for(int i=0;i<10000;i++)marble_gui_diag_take(&shared,512);return NULL; }
int main(int argc,char **argv) {
 assert(argc==2);mode=atoi(argv[1]);char name[64];
 enabled=0;exit_diag(&test_proc,SIGSEGV);assert(!crashes);enabled=1;
 exit_diag(&test_proc,0);assert(!crashes);
 struct process other=test_proc;exit_diag(&other,SIGSEGV);assert(!crashes);
 for(int i=0;i<9;i++){who=names[i];for(int j=0;j<20;j++)exit_diag(&test_proc,j&1?SIGSEGV:(1<<8));}
 assert(crashes==32);assert(reasons==32);who="Setup";
 for(int i=0;i<9;i++){assert(marble_gui_diag_index(names[i])==i);}
 assert(marble_gui_diag_index("nanotimekitcompa")==-1);
 assert(marble_gui_diag_index("installcoordinationdExtra")==-1);
 pthread_t threads[8];for(int i=0;i<8;i++)assert(!pthread_create(&threads[i],NULL,reserve,NULL));
 for(int i=0;i<8;i++)pthread_join(threads[i],NULL);assert(shared==512);
 enabled=0;assert(!sweet_null_tee(name,sizeof(name)));sweet_crash_strings(who);assert(!queries);
 enabled=1;who="unrelated";assert(!sweet_null_tee(name,sizeof(name)));sweet_crash_strings(who);assert(!queries);
 unsigned chunks=0;
 for(int i=0;i<9;i++){who=names[i];unsigned per=0;while(sweet_null_tee(name,sizeof(name))){per++;chunks++;}assert(per<=64);}
 assert(chunks==512);
 // ReportCrash itself never consumes a heap scan; long full names do.
 sweet_crash_strings("ReportCrash");assert(!queries);
 for(int i=0;i<9;i++){
  int previous=queries;attempted=0;strings=0;copies=0;queries=0;
  sweet_crash_strings(names[i]);
  assert(queries<=4096);assert(attempted<=(16ull<<20));assert(strings<=64);
  if(mode==1||mode==2)assert(!copies);
  if(mode==3&&queries)assert(queries==4096);
  if(mode==4&&queries)assert(attempted==(16ull<<20));
  (void)previous;
 }
 assert(!queries); // Four scans exhausted before last process.
 puts("PASS actual helper allowlist/atomic/stderr/heap bounds");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='marble-diag-test-') as tmp:
    source = Path(tmp) / 'test.c'
    binary = Path(tmp) / 'test'
    source.write_text(prelude + helper + '\n' + tee + '\n' + heap + crash_stubs + main)
    subprocess.run(['clang', '-std=gnu11', '-fsanitize=address,undefined', '-pthread', str(source), '-o', str(binary)], check=True)
    for mode in range(5):
        subprocess.run([str(binary), str(mode)], check=True, env={'ASAN_OPTIONS': 'detect_leaks=0'})
