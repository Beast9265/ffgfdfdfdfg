"""Compile the actual MARBLE device-management code with host MMIO/timer mocks."""
from pathlib import Path
import re
import subprocess
import tempfile

source = (Path(__file__).resolve().parents[1] / 'ufs.c').read_text()
code = source[source.index('/* UTP transfer request descriptor'):source.index('\n/*\n * Issue one SCSI command')]
code = code.replace('#ifdef SHIM_MARBLE', '').replace('#endif', '')
code = re.sub(r'static uint64_t ticks\(void\).*?\n}', 'static uint64_t ticks(void) { return clock_ticks++; }', code, flags=re.S)
code = code.replace('__asm__ volatile("dsb sy" ::: "memory");', '')
code = code.replace('__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(freq));', 'freq = 1000000;')
prefix = r'''
#include <stdint.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define BLOCK 4096
#define REG_UTRLBA 0x50
#define REG_UTRLBAU 0x54
#define REG_UTRLDBR 0x58
#define REG_UTRLCLR 0x5c
#define REG_UTRLRSR 0x60
static uint64_t clock_ticks;
static unsigned mode, nops, queries, reads, cleared, badguard;
static uint32_t ufs_rd(uint32_t);
static void ufs_wr(uint32_t, uint32_t);
static void con_str(const char *a,const char *b) { (void)a;(void)b; }
static void con_hex2(const char *a,const char *b,uint32_t c,const char *d,uint32_t e)
{ (void)a;(void)b;(void)c;(void)d;(void)e; }
'''
suffix = r'''
static uint32_t ufs_rd(uint32_t r) {
 if(r==REG_UTRLBA) return (uint32_t)(uintptr_t)utrl + (badguard==1);
 if(r==REG_UTRLBAU) return ((uintptr_t)utrl >> 32) + (badguard==2);
 if(r==REG_UTRLRSR) return badguard!=3;
 if(r==REG_UTRLDBR) return badguard==4 || ((mode==4 || mode==5) && nops>cleared);
 assert(0); return 0;
}
static void ufs_wr(uint32_t r,uint32_t v) {
 if(r==REG_UTRLCLR) { assert(v==~1u); if(mode!=5) cleared++; return; }
 assert(r==REG_UTRLDBR && v==1 && dev_list_ready());
 assert(utrl[0].dw0==0x11000000 && utrl[0].dw2==15);
 assert(utrl[0].prdt==0 && utrl[0].resp==0x00800080);
 assert(utrl[0].ucdba==(uint32_t)(uintptr_t)&ucd);
 assert(utrl[0].ucdbau==((uintptr_t)&ucd>>32));
 for(unsigned i=0;i<sizeof(ucd.prdt);i++) assert(((uint8_t*)ucd.prdt)[i]==0);
 uint8_t expected[512]={0}; expected[3]=ucd.cmd[3];
 if(ucd.cmd[0]==0) {
  static uint8_t last;
  assert(ucd.cmd[3]==(uint8_t)(last+1)); last=ucd.cmd[3];
  nops++;
  assert(!memcmp(expected,ucd.cmd,512));
  ucd.resp[0]=(mode==1 || (mode==6 && nops<3))?0x21:0x20;
  ucd.resp[3]=ucd.cmd[3]+(mode==2);
  ucd.resp[7]=0xff; /* Not SCSI: status must be ignored. */
  utrl[0].dw2=mode==3?1:0;
 } else {
  assert(nops && mode!=1 && mode!=2 && mode!=3 && mode!=4 && mode!=5);
  queries++;
  expected[0]=0x16; expected[5]=1;
  expected[12]=5; expected[13]=1;
  assert(!memcmp(expected,ucd.cmd,512));
  memcpy(ucd.resp,ucd.cmd,32); ucd.resp[0]=mode==10?0x21:0x36;
  ucd.resp[6]=mode==8?0xff:0;
  ucd.resp[23]=(mode==7 || (mode!=9 && ++reads==1))?1:0;
  if(mode==12) { ucd.resp[20]=0x80; ucd.resp[23]=2; }
  utrl[0].dw2=mode==11?1:0;
 }
}
static void reset(unsigned m) { mode=m; nops=queries=reads=cleared=badguard=0; clock_ticks=0; }
int main(void) {
 reset(0); assert(ufs_complete_dev_init()); assert(nops==1 && queries==2);
 for(unsigned m=1;m<=4;m++) {
  reset(m); assert(!ufs_complete_dev_init()); assert(nops==10 && !queries);
  if(m==4) assert(cleared==10 && clock_ticks<500100);
 }
 reset(5); assert(!ufs_complete_dev_init()); assert(nops==1 && !queries);
 reset(6); assert(ufs_complete_dev_init()); assert(nops==3 && queries==2);
 reset(7); assert(!ufs_complete_dev_init()); assert(clock_ticks<1500100);
 reset(9); assert(ufs_complete_dev_init()); assert(queries==1);
 reset(8); assert(!ufs_complete_dev_init()); assert(queries==1);
 for(unsigned m=10;m<=11;m++) { reset(m); assert(!ufs_complete_dev_init()); assert(queries==1); }
 reset(12); assert(ufs_complete_dev_init()); assert(queries==1);
 for(unsigned g=1;g<=4;g++) {
  reset(0); badguard=g; assert(!ufs_complete_dev_init()); assert(!nops && !queries);
 }
 reset(0); struct query_diag d; unsigned value;
 for(unsigned op=0;op<256;op++) if(op!=5)
  assert(query_flag(op,&value,&d,0,1500000)==5 && !queries);
 assert(!strcmp(query_result_name(0xff),"GENERAL FAILURE"));
 for(unsigned r=0xf6;r<=0xff;r++) assert(strcmp(query_result_name(r),"unknown result"));
 /* Exercise task-tag wrap. */
 for(unsigned i=0;i<260;i++) { reset(0); assert(ufs_complete_dev_init()); }
 puts("NOP/query: layout, tags/wrap, OCS, retries, timeout/cancel, stuck slot, guards, init gate, flag polling, opcode allowlist passed");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp) / 'test.c'
    c.write_text(prefix + code + suffix)
    binary = Path(tmp) / 'test'
    subprocess.run(['cc', '-fsanitize=address,undefined', '-g', str(c), '-o', str(binary)], check=True)
    import os
    subprocess.run([str(binary)], check=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
