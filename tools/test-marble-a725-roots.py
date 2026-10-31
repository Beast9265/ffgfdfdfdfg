#!/usr/bin/env python3
"""Exercise 0105's actual C against synthetic MMIO, including failed cleanup.

Usage: test-marble-a725-roots.py PATH_TO_REPLAYED_XNU
This proves software control flow, not hardware completion or clock frequency.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / 'bsd/dev/marble_a725_probe.c').read_text()
constants = source[source.index('#define A725_BUILD_ID'):source.index('struct a725_firmware_spec')]
functions = source[source.index('static boolean_t\na725_root_parent_acquire'):source.index('static boolean_t\na725_enable_gmu_clocks')]
prefix = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <errno.h>
typedef uintptr_t vm_offset_t;
typedef bool boolean_t;
#define TRUE true
#define FALSE false
'''
mock = r'''
static uint32_t gcc[0x63000/4], cc[0xa000/4];
static unsigned writes, elapsed, updates;
static unsigned fail_update, ignore_enable, ignore_vote, ignore_cfg;
static void delay(unsigned us) {elapsed+=us;assert(elapsed<10000);}
static uint32_t a725_read32(vm_offset_t base, uint32_t off) {
 assert(!(off&3));
 if(base==1){assert(off<sizeof(gcc));return gcc[off/4];}
 assert(base==2 && off<sizeof(cc));return cc[off/4];
}
static void a725_write32(vm_offset_t base, uint32_t off, uint32_t v) {
 writes++;assert(!(off&3));
 if(base==1){assert(off==A725_GPU_GPLL0_VOTES);
  if(!ignore_vote){gcc[off/4]=v;}
  return;}
 assert(base==2);
 bool allowed=false;
 for(unsigned i=0;i<A725_ROOT_COUNT;i++){
  unsigned cmd=a725_roots[i].cmd;
  if(off==cmd){
   allowed=true;
   if(ignore_enable && !(v&A725_RCG_UPDATE))return;
   if(v&A725_RCG_UPDATE){updates++;if(updates!=fail_update)v&=~A725_RCG_UPDATE;}
   if(v&A725_RCG_ROOT_EN)v&=~A725_RCG_ROOT_OFF;
  }
  if(off==cmd+4){allowed=true;if(ignore_cfg)return;}
 }
 assert(allowed);cc[off/4]=v;
}
static boolean_t a725_poll32(vm_offset_t base, uint32_t off,
 uint32_t mask,uint32_t value,unsigned bound) {
 for(unsigned i=0;i<bound;i++){
  if((a725_read32(base,off)&mask)==value){return TRUE;}
  delay(1);
 }
 return FALSE;
}
static void init(void){
 memset(cc,0,sizeof(cc));memset(gcc,0,sizeof(gcc));
 writes=elapsed=updates=fail_update=ignore_enable=ignore_vote=ignore_cfg=0;
 gcc[A725_GPLL0_MODE/4]=0x80000001;
 gcc[A725_GPLL0_OPMODE/4]=1;gcc[A725_GPLL0_L/4]=31;
 gcc[A725_GPLL0_ALPHA/4]=0x4000;gcc[A725_GPLL0_USER/4]=1<<10;
 gcc[A725_GPU_GPLL0_VOTES/4]=1<<15; /* sibling must survive */
}
'''
tests = r'''
int main(void){
 const struct marble_a725_resources r={.gcc=1,.gpucc=2};
 struct a725_power_results q;
 // Exact restoration and unrelated CFG bits, with/without inherited vote.
 for(unsigned inherited=0;inherited<2;inherited++){
  init();memset(&q,0,sizeof(q));
  gcc[A725_GPU_GPLL0_VOTES/4]|=inherited*A725_GPU_GPLL0_DIV;
  for(unsigned i=0;i<3;i++)cc[(a725_roots[i].cmd+4)/4]=0x40000000;
  uint32_t before[sizeof(cc)/4];memcpy(before,cc,sizeof(cc));
  assert(a725_root_parent_acquire(&r,&q));
  for(unsigned i=0;i<3;i++)assert(a725_root_program_one(&r,&q,i));
  a725_root_cleanup(&r,&q);assert(q.root_cleanup==A725_ACKNOWLEDGED);
  assert(!memcmp(before,cc,sizeof(cc)));
  assert(gcc[A725_GPU_GPLL0_VOTES/4]==((1u<<15)|inherited*A725_GPU_GPLL0_DIV));
 }
 // Unlocked PLL, wrong rate/divider: no MMIO write is allowed.
 for(unsigned bad=0;bad<5;bad++){
  init();memset(&q,0,sizeof(q));
  if(bad==0)gcc[A725_GPLL0_MODE/4]=1;
  if(bad==1)gcc[A725_GPLL0_OPMODE/4]=0;
  if(bad==2)gcc[A725_GPLL0_L/4]++;
  if(bad==3)gcc[A725_GPLL0_ALPHA/4]++;
  if(bad==4)gcc[A725_GPLL0_USER/4]=0;
  assert(!a725_root_parent_acquire(&r,&q)&&writes==0);
 }
 // Ignored parent vote must fail, sibling untouched.
 init();memset(&q,0,sizeof(q));ignore_vote=1;
 assert(!a725_root_parent_acquire(&r,&q));assert(gcc[A725_GPU_GPLL0_VOTES/4]==1<<15);
 // Reject inherited force owner, pending update, unknown parent without root writes.
 for(unsigned bad=0;bad<3;bad++){
  init();memset(&q,0,sizeof(q));
  if(bad==0)cc[0x9318/4]=2;
  if(bad==1)cc[0x9318/4]=1;
  if(bad==2)cc[0x931c/4]=0x100303;
  assert(!a725_root_program_one(&r,&q,0)&&writes==0);
  assert(q.root_uncertain);a725_root_cleanup(&r,&q);assert(writes==0);
 }
 // Ignored force write is detected even if ROOT_OFF reads zero.
 init();memset(&q,0,sizeof(q));assert(a725_root_parent_acquire(&r,&q));
 ignore_enable=1;assert(!a725_root_program_one(&r,&q,0));assert(q.root_uncertain);
 unsigned n=writes;a725_root_cleanup(&r,&q);assert(writes==n&&elapsed>=500);
 assert(gcc[A725_GPU_GPLL0_VOTES/4]&A725_GPU_GPLL0_DIV);
 // Each update timeout, including reverse cleanup, quarantines resources.
 for(unsigned failure=1;failure<=6;failure++){
  init();memset(&q,0,sizeof(q));assert(a725_root_parent_acquire(&r,&q));
  fail_update=failure;
  for(unsigned i=0;i<3;i++)if(!a725_root_program_one(&r,&q,i))break;
  n=writes;a725_root_cleanup(&r,&q);
  assert(q.root_uncertain && (gcc[A725_GPU_GPLL0_VOTES/4]&A725_GPU_GPLL0_DIV));
  if(failure<=3)assert(writes==n);
  n=writes;a725_root_cleanup(&r,&q);assert(writes==n);
 }
 // Ignored CFG write cannot pass configuration validation.
 init();memset(&q,0,sizeof(q));assert(a725_root_parent_acquire(&r,&q));
 ignore_cfg=1;assert(!a725_root_program_one(&r,&q,0));
 a725_root_cleanup(&r,&q);assert(q.root_cleanup==A725_ACKNOWLEDGED);
 puts("PASS A725 roots: restoration/ownership, rate prerequisites, ignored writes, bounded timeouts, cleanup quarantine, MMIO allowlist");
}
'''
with tempfile.TemporaryDirectory(prefix='a725-roots-test-') as directory:
    path = Path(directory)
    (path / 'test.c').write_text(prefix + constants + mock + functions + tests)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-Wno-unused-const-variable', str(path / 'test.c'), '-o', str(path / 'test')], check=True)
    subprocess.run([str(path / 'test')], check=True)
