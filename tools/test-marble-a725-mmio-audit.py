#!/usr/bin/env python3
"""Actual mode10 C: PAR decoding and read-only capture, no device write API."""
import ast
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
code=s[s.index('struct a725_io_translation {'):s.index('void\nmarble_a725_probe(void)')]
a=code.index('static void\na725_io_translate');b=code.index('static uint64_t\na725_io_par_pa',a)
mock=r'''
static unsigned translates,reads,elapsed,gcc_reads,gpu_reads;
static int bad_map,bad_kind,bad_gate,bad_reg;
static void delay(unsigned us){elapsed+=us;assert(elapsed<=10001000);}
static void a725_io_translate(vm_offset_t va,struct a725_io_translation *t){
 unsigned i=translates++;assert(i<3);
 const uint64_t targets[3]={0x03d9911c,0x03d993f0,0x00181004};
 const uint64_t vas[3]={0x10000911c,0x1000093f0,0x200081004};assert(va==vas[i]);
 t->read_par=t->write_par=(targets[i]&~0xfffULL)|0x800;
 if((int)i==bad_map){
  if(bad_kind==0)t->read_par|=1;
  if(bad_kind==1)t->write_par|=1;
  if(bad_kind==2)t->read_par^=0x4000;
  if(bad_kind==3)t->write_par^=0x4000;
  if(bad_kind==4)t->read_par|=0xffULL<<56;
  if(bad_kind==5)t->write_par|=4ULL<<56;
 }
}
static uint32_t a725_read32(vm_offset_t base,uint32_t off){
 reads++;
 if(base==0x200000000){assert(off==0x81004);unsigned n=gcc_reads++;return (int)n==bad_gate?0:1;}
 assert(base==0x100000000);bool allowed=false;
 const uint32_t offsets[]={0x911c,0x9108,0x953c,0x905c,0x9430,0x942c,0x93e8,0x9148,0x93ec,0x93f0,0x913c,0x9144};
 for(unsigned i=0;i<12;i++)if(off==offsets[i])allowed=true;
 assert(allowed);unsigned n=gpu_reads++;return (int)n==bad_reg?~0u:0;
}
'''
code=code[:a]+mock+code[b:]
# No store/vote/map/SCM or firmware callback is linked into the tested module.
for forbidden in ['a725_write32','marble_rpmh','ml_io_map','a725_cx_enable','a725_ahb_latch_test']:
 assert forbidden not in code,forbidden
main=r'''
static void init(void){translates=reads=elapsed=gcc_reads=gpu_reads=0;bad_map=bad_gate=bad_reg=-1;bad_kind=0;}
int main(void){
 struct marble_a725_resources r={.gpucc=0x100000000,.gcc=0x200000000};struct a725_io_audit a;
 init();memset(&a,0,sizeof(a));assert(a725_io_readonly_capture(&r,&a));
 assert(a.maps==3&&reads==26&&gpu_reads==24&&elapsed==1000&&a.reads[0]==12&&a.reads[1]==12);
 // Zero AHB values are captured, never transformed into clock enable ACK.
 assert(a.value[0][0]==0&&a.value[1][0]==0);
 for(int m=0;m<3;m++)for(int k=0;k<6;k++){
  init();bad_map=m;bad_kind=k;memset(&a,0,sizeof(a));
  assert(!a725_io_readonly_capture(&r,&a));assert(a.refusal==(1u<<m)&&reads==0&&elapsed==0);
 }
 for(int g=0;g<2;g++){
  init();bad_gate=g;memset(&a,0,sizeof(a));assert(!a725_io_readonly_capture(&r,&a));
  assert(a.refusal==8&&gpu_reads==(g?12u:0u));
 }
 for(int n=0;n<24;n++){
  init();bad_reg=n;memset(&a,0,sizeof(a));assert(!a725_io_readonly_capture(&r,&a));
  assert(a.refusal==16&&gpu_reads==(unsigned)n+1);
 }
 // Actual renderer completes both paths; only visual=1 adds ten seconds.
 init();a725_io_readonly_test(&r,false);assert(elapsed==1000);
 init();a725_io_readonly_test(&r,true);assert(elapsed==10001000);
 init();bad_map=0;a725_io_readonly_test(&r,false);assert(reads==0&&elapsed==0);
 puts("PASS mode10 actual C: PAR faults/PA/attribute refusals, 26-read allowlist, two snapshots, zero AHB observation, gate-loss/all-ones stop, visual-only delay, no write/vote API");
}
'''
with tempfile.TemporaryDirectory(prefix='a725-mmio-audit-') as d:
 p=Path(d);(p/'test.c').write_text(prefix+constants+code+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-const-variable',str(p/'test.c'),'-o',str(p/'test')],check=True)
 out=subprocess.check_output([str(p/'test')],text=True);print(out.splitlines()[-1])
