#!/usr/bin/env python3
"""Actual mode11 C against a read-only register/translation allowlist."""
from pathlib import Path
import subprocess,sys,tempfile
s=(Path(sys.argv[1])/'bsd/dev/marble_a725_probe.c').read_text()
prefix='''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>
typedef uintptr_t vm_offset_t;
typedef bool boolean_t;
#define TRUE true
#define FALSE false
'''
constants=s[s.index('#define A725_BUILD_ID'):s.index('struct a725_firmware_spec')]
translation=s[s.index('static uint64_t\na725_io_par_pa'):s.index('#define A725_IO_AUDIT_REGS')]
code=s[s.index('#define A725_DEBUG_SNAPSHOT_COUNT'):s.index('void\nmarble_a725_probe(void)')]
mock=r'''
struct a725_io_translation {uint64_t read_par,write_par;};
static unsigned trans,reads,cfg_reads,debug_reads,elapsed;
static int bad_map,bad_read,bad_cfg,changed_reg;static bool busy;
static const unsigned offs[9]={0x9564,0x9270,0x9274,0x72000,0x72004,0x72008,0x7200c,0x72038,0x7203c};
static void delay(unsigned us){elapsed+=us;assert(elapsed<=10001000);}
static void a725_io_translate(vm_offset_t va,struct a725_io_translation *t){
 unsigned i=trans++;assert(i<10);bool gpu=i<3;unsigned off=i<9?offs[i]:0x81004;
 assert(va==(gpu?0x100000000ULL:0x200000000ULL)+off);
 uint64_t pa=(gpu?A725_GPUCC_PA:A725_GCC_PA)+off;
 t->read_par=t->write_par=(pa&~0xfffULL)|0x800;
 if((int)i==bad_map)t->write_par|=1;
}
static uint32_t a725_read32(vm_offset_t base,uint32_t off){
 reads++;
 if(base==0x200000000ULL&&off==0x81004){unsigned n=cfg_reads++;return (int)n==bad_cfg?0:1;}
 unsigned i=debug_reads%9;assert(base==(i<3?0x100000000ULL:0x200000000ULL));assert(off==offs[i]);
 unsigned n=debug_reads++;if((int)n==bad_read)return ~0u;
 uint32_t value=(i==8?0x2000123u:0);
 if(busy&&i==7)value|=1u<<20;
 if(n>=9&&(int)i==changed_reg)value^=1;
 return value;
}
'''
main=r'''
static void init(void){trans=reads=cfg_reads=debug_reads=elapsed=0;bad_map=bad_read=bad_cfg=changed_reg=-1;busy=false;}
int main(void){
 struct marble_a725_resources r={.gpucc=0x100000000ULL,.gcc=0x200000000ULL};struct a725_debug_snapshot a;
 init();memset(&a,0,sizeof(a));assert(a725_debug_snapshot_capture(&r,&a));
 assert(trans==10&&reads==20&&debug_reads==18&&elapsed==1000&&a.changed==0&&a.refusal==0);
 for(int n=0;n<10;n++){
  init();bad_map=n;memset(&a,0,sizeof(a));assert(!a725_debug_snapshot_capture(&r,&a));assert(reads==0&&a.refusal==(1u<<n));
 }
 for(int n=0;n<18;n++){
  init();bad_read=n;memset(&a,0,sizeof(a));assert(!a725_debug_snapshot_capture(&r,&a));assert(debug_reads==(unsigned)n+1&&a.refusal==(1u<<11));
 }
 for(int n=0;n<2;n++){
  init();bad_cfg=n;memset(&a,0,sizeof(a));assert(!a725_debug_snapshot_capture(&r,&a));assert(debug_reads==(n?9u:0u)&&a.refusal==(1u<<10));
 }
 // An active or changing engine is recorded, never stopped/cleared/claimed.
 for(int n=0;n<9;n++){
  init();busy=true;changed_reg=n;memset(&a,0,sizeof(a));assert(a725_debug_snapshot_capture(&r,&a));
  assert(a.changed==(1u<<n)&&(a.values[0][7]&(1u<<20)));
 }
 init();a725_debug_snapshot_test(&r,false);assert(elapsed==1000);
 init();a725_debug_snapshot_test(&r,true);assert(elapsed==10001000);
 puts("PASS mode11 actual C: ten mapping checks, 20-read allowlist, all fault/refusal sites, gate loss, active/changing state preserved, no write/power API, visual-only delay");
}
'''
for forbidden in ['a725_write32','marble_rpmh','a725_ahb_latch_test','a725_root_program']:
 assert forbidden not in code,forbidden
with tempfile.TemporaryDirectory(prefix='a725-debug-snapshot-') as d:
 p=Path(d);(p/'test.c').write_text(prefix+constants+mock+translation+code+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-const-variable',str(p/'test.c'),'-o',str(p/'test')],check=True)
 result=subprocess.check_output([str(p/'test')],text=True);print(result.splitlines()[-1])
