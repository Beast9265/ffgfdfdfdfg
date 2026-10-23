#!/usr/bin/env python3
"""Extract Linux-aligned pin, mode-selection and packing functions; mock MMIO only."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
spec=importlib.util.spec_from_file_location('extract',Path(__file__).with_name('test-marble-input.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s=(Path(sys.argv[1])/'bsd/dev/marble_touch.c').read_text()
body='\n'.join(m.function(s,n) for n in ['mt_spi_pin_mask','mt_spi_pin_value','mt_fifo_available','mt_select_fifo','mt_pack8'])
prefix=r'''
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <stdio.h>
static uintptr_t mt_se=1;
static uint32_t regs[0x4000/4];static unsigned writes;
static uint32_t mt_rd(uintptr_t base,unsigned off){assert(base==1&&off<0x4000);return regs[off/4];}
static void mt_wr(unsigned off,uint32_t v){assert(off<0x4000);writes++;regs[off/4]=v;}
static bool mt_stop(const char *why){(void)why;return false;}
'''
tests=r'''
int main(void){
 assert(mt_spi_pin_mask(19)==0x1ff&&mt_spi_pin_value(19)==0x84);
 for(unsigned pin=16;pin<=18;pin++){assert(mt_spi_pin_mask(pin)==0x3c&&mt_spi_pin_value(pin)==4);}
 for(unsigned old=0;old<0x10000;old++){
  unsigned mask=mt_spi_pin_mask(19),now=(old&~mask)|mt_spi_pin_value(19);
  assert(((now>>2)&15)==1&&((now>>6)&7)==2&&!(now&3));assert((now&~mask)==(old&~mask));
 }
 assert(mt_fifo_available(0)&&mt_fifo_available(2)&&!mt_fifo_available(1)&&!mt_fifo_available(0xffffffff));
 regs[0x64/4]=1;assert(!mt_select_fifo()&&!writes);
 regs[0x64/4]=0;regs[0x40/4]=1;assert(!mt_select_fifo()&&!writes);
 regs[0x40/4]=0;regs[0x258/4]=1;regs[0xc54/4]=4;assert(!mt_select_fifo()&&!writes);
 regs[0xc54/4]=0;assert(mt_select_fifo()&&!(regs[0x258/4]&1));
 mt_pack8();assert(regs[0x260/4]==0x7f8fe&&regs[0x264/4]==0xffefe);
 assert(regs[0x284/4]==regs[0x260/4]&&regs[0x288/4]==regs[0x264/4]);
 assert(regs[0x254/4]==0&&regs[0x268/4]==4);
 puts("PASS Linux SPI: all65536 GPIO19 configs,6mA/no bias, data mux-only, FIFO disable/busy/DMA gates with zero writes on refusal, Linux8x4 MSB packing/word length");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-spi-linux-') as directory:
    p=Path(directory);(p/'test.c').write_text(prefix+body+tests)
    subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
