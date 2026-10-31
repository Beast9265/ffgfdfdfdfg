#!/usr/bin/env python3
"""Run 0106's real read-only C with an MMIO read allowlist; no write API."""
from pathlib import Path
import subprocess
import sys
import tempfile
s = (Path(sys.argv[1]) / 'bsd/dev/marble_a725_probe.c').read_text()
code = s[s.index('struct a725_pll_sample {'):s.index('/*\n * The matching GCC driver exposes GPLL0')]
constants = '\n'.join(line for line in s.splitlines() if line.startswith('#define A725_'))
branch = s[s.index('\tif (enabled == 6) {'):s.index('\tr.gpucc = ml_io_map')]
assert all(word not in branch for word in ('a725_write32', 'marble_rpmh', 'r.gpucc =', 'r.gmu =', 'r.smmu ='))
prefix = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <assert.h>
typedef uintptr_t vm_offset_t;
typedef bool boolean_t;
static unsigned reads,elapsed;
static uint32_t a725_read32(vm_offset_t base,uint32_t at) {
 assert(base==1);
 if(at==A725_GPLL0_VOTE){reads++;return 1;}
 if(at==A725_GPU_GPLL0_VOTES){reads++;return 0;}
 unsigned pll=at/0x4000,off=at%0x4000;
 assert(pll<2);reads++;
 switch(off){
 case 0:return pll?0x80000005:5;
 case 4:return pll?1:0;
 case 12:return 0;
 case 16:return pll?0x4444001f:0x444400ff;
 case 20:return 0x4000;
 case 24:return 0x02000403;
 default:assert(0);return 0;
 }
}
static void delay(unsigned us){elapsed+=us;assert(elapsed<=10001000);}
'''
main = r'''
int main(void){
 struct a725_pll_sample s;
 a725_pll_sample(1,0,&s);assert(a725_pll_refusal(&s)==0x0d);
 a725_pll_sample(1,0x4000,&s);assert(a725_pll_refusal(&s)==0);
 s.mode&=~1u;assert(a725_pll_refusal(&s)==2);s.mode|=1;
 s.user=0;assert(a725_pll_refusal(&s)==16);s.user=1<<10;
 s.alpha++;assert(a725_pll_refusal(&s)==8);
 reads=elapsed=0;a725_pll_readonly_test(1,false);assert(reads==32&&elapsed==1000);
 reads=elapsed=0;a725_pll_readonly_test(1,true);assert(reads==32&&elapsed==10001000);
}
'''
with tempfile.TemporaryDirectory(prefix='a725-pll-audit-') as directory:
    p=Path(directory);(p/'test.c').write_text('#include <stdint.h>\n'+constants+prefix+code+main)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True)
    result=subprocess.run([str(p/'test')],capture_output=True,text=True,check=True)
    assert 'GPLL0 REFUSAL=0d' in result.stdout
    assert 'REGISTER-DECODE Hz=4900800000' in result.stdout
    print('PASS PLL audit: exact observed refusal, strict valid/invalid prerequisites, read allowlist, 32 reads, visual-only delay, no write API')
