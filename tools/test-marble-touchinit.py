#!/usr/bin/env python3
"""Host tests of extracted MARBLE active-init functions; no hardware access."""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import sys

spec = importlib.util.spec_from_file_location('input_tests', Path(__file__).with_name('test-marble-input.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
f = module.function
source = (Path(sys.argv[1]) / 'bsd/dev/marble_touch.c').read_text()
prefix = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define MT_MAX 1024u
#define MT_FINGERS 10u
static uintptr_t mt_tlmm=1;
static uint32_t mt_event=0x10308,regs[0x16000/4];
static uint8_t mt_tx[1032],event[90];
static bool mt_down[10]; static int mt_x[10],mt_y[10],mt_diag;
static unsigned mt_factor=10;
static unsigned stage,clockms,reads,acks,calls,exchanges,attempts,failvote;
static bool io_fail,mismatch;
static uint32_t mt_rd(uintptr_t base,unsigned off){assert(base==1);assert(off<0x16000);return regs[off/4];}
static bool mt_mask(uintptr_t base,unsigned off,uint32_t mask,uint32_t value){assert(base==1);regs[off/4]=(regs[off/4]&~mask)|value;return true;}
static bool mt_stop(const char *gate){(void)gate;return false;}
static void mt_wait(unsigned ms){clockms+=ms;}
static int marble_touch_power_prepare(void){assert(stage==0);stage=1;return 0;}
static int marble_touch_power_vote(const char *name,unsigned mv){
 assert(!(regs[0x14004/4]&2));assert(regs[0x14000/4]&0x200);
 if(stage==1){assert(!strcmp(name,"ldoc2")&&mv==1800&&clockms==2);stage=2;}
 else {assert(stage==2&&!strcmp(name,"ldoc9")&&mv==3224&&clockms==32);stage=3;}
 return failvote==stage?5:0;
}
static bool mt_exchange(unsigned n){
 assert(n==13&&mt_tx[0]==0xf0&&mt_tx[1]==0&&mt_tx[2]==1&&mt_tx[3]==0&&mt_tx[4]==0);
 for(unsigned i=5;i<13;i++)assert(mt_tx[i]==0xaa);
 exchanges++;return !io_fail;
}
static bool mt_read(uint32_t addr,uint8_t *out,unsigned n){
 if(io_fail)return false;
 if(addr==0x10000){assert(n==8);memset(out,mismatch?0:0xaa,n);attempts++;return true;}
 if(reads++==0){assert(addr==mt_event&&n==26);memcpy(out,event,26);}
 else{unsigned count=event[2]&15;assert(count>2&&addr==mt_event+26&&n==(count-2)*8);memcpy(out,event+26,n);}
 return true;
}
static bool mt_ack(void){acks++;return !io_fail;}
static void marble_hid_touch(int id,int down,int x,int y){assert(id>=0&&id<10);(void)down;(void)x;(void)y;calls++;}
'''
body = '\n'.join(f(source, name) for name in ['mt_le16', 'mt_checksum', 'mt_reset', 'mt_spi_pin_mask', 'mt_spi_pin_value', 'mt_power_on', 'mt_confirm', 'mt_frame', 'mt_poll_event'])
tests = r'''
static void checksum(uint8_t *p,unsigned n){unsigned sum=0;for(unsigned i=0;i<n-2;i++)sum+=p[i];p[n-2]=sum;p[n-1]=sum>>8;}
static void frame(unsigned count){
 memset(event,0,sizeof(event));event[0]=0x80;event[2]=count;checksum(event,8);
 for(unsigned i=0;i<count;i++){event[8+8*i]=i<<4;event[10+8*i]=100;event[12+8*i]=200;}
 checksum(event+8,count*8+2);reads=acks=0;
}
int main(void){
 assert(mt_power_on()&&stage==3&&clockms==147&&(regs[0x14004/4]&2));
 assert(!(regs[0x15000/4]&0x200));
 for(unsigned pin=16;pin<=19;pin++)assert(((regs[pin*0x1000/4]>>2)&15)==1);
 stage=clockms=0;failvote=2;assert(!mt_power_on()&&!(regs[0x14004/4]&2)&&clockms==2);
 stage=clockms=0;failvote=3;assert(!mt_power_on()&&!(regs[0x14004/4]&2)&&clockms==32);
 clockms=0;assert(mt_confirm()&&attempts==1&&exchanges==1);
 mismatch=true;attempts=exchanges=clockms=0;assert(!mt_confirm()&&attempts==3&&exchanges==3&&clockms==10);
 io_fail=true;attempts=exchanges=0;assert(!mt_confirm()&&attempts==0&&exchanges==1);io_fail=false;
 unsigned counts[]={0,1,2,3,4,5,6,7,8,9,10};
 for(unsigned i=0;i<11;i++){frame(counts[i]);assert(mt_poll_event()==1&&acks==1&&reads==(counts[i]>2?2:1));}
 frame(1);event[7]^=1;unsigned before=calls;assert(mt_poll_event()==-1&&acks==0&&calls==before);
 frame(1);event[9]^=1;assert(mt_poll_event()==-1&&acks==0&&calls==before);
 frame(2);event[16]=0;checksum(event+8,18);assert(mt_poll_event()==-1&&acks==0&&calls==before);
 frame(0);event[0]=0;assert(mt_poll_event()==0&&acks==0);
 frame(1);event[0]=0x40;checksum(event,8);assert(mt_poll_event()==-2&&acks==0);
 frame(1);io_fail=true;assert(mt_poll_event()==-2&&acks==0);
 puts("PASS active-init: rail order/settling/failure, physical reset polarity, confirm framing/3 attempts/transport stop, initial26, 0/1/2/3/10 contacts, checksum/duplicate rejection, no invalid ACK");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-touchinit-test-') as directory:
    c = Path(directory) / 'test.c'
    binary = Path(directory) / 'test'
    c.write_text(prefix + module.diagnostic_stubs(sys.argv[1]) + body + tests)
    subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-fsanitize=address,undefined', str(c), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
