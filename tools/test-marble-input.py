#!/usr/bin/env python3
"""Exercise actual replayed MARBLE input parsers/FIFO logic under ASan/UBSan.

Usage: tools/test-marble-input.py PATCHED_XNU_TREE
No hardware access. MMIO and HID delivery are modeled; protocol functions are
extracted verbatim from the requested patched tree, not reimplemented tests.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def function(source, name):
    start = source.index(name + '(')
    start = source.rfind('\nstatic ', 0, start) + 1
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tree', type=Path)
    args = parser.parse_args()
    source = (args.tree / 'bsd/dev/marble_touch.c').read_text()
    names = ['mt_le16', 'mt_le32', 'mt_checksum', 'mt_cs', 'mt_exchange',
             'mt_read', 'mt_ack', 'mt_parse_info', 'mt_frame']
    body = '\n'.join(function(source, name) for name in names)
    harness = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define MT_MAX 1024u
#define MT_FINGERS 10u
#define MT_ERRORS 0x33007e3eu
static uintptr_t mt_se;
static uint32_t mt_depth=16,mt_rxdepth=16,mt_event;
static unsigned mt_factor;
static bool mt_bad,mt_legacy_range,mt_down[10];
static int mt_x[10],mt_y[10],mt_diag;
static uint8_t mt_tx[1032],mt_rx[1032];
static unsigned hidcalls,downs,ups,xx,yy;
static void marble_hid_touch(int id,int down,int x,int y) {
 assert(id>=0 && id<10);hidcalls++;downs+=!!down;ups+=!down;xx=x;yy=y;
}
static unsigned txbytes,rxbytes,total,commands[4],cmdcount,waits,mode;
static uint32_t mockirq;
static void delay(unsigned n) {waits+=n;}
static void mt_wr(unsigned off,uint32_t v) {
 if(off==0x26c || off==0x270) total=v;
 if(off==0x600) {
  assert(cmdcount<4);commands[cmdcount++]=v>>27;
  if((v>>27)==3) mockirq=0;else mockirq=1;
 }
 if(off==0x700) {assert(txbytes<total);unsigned n=total-txbytes;n=n<4?n:4;
  for(unsigned b=0;b<n;b++) assert((uint8_t)(v>>(8*b))==mt_tx[txbytes+b]);
  txbytes+=n;
 }
}
static uint32_t mt_rd(uintptr_t base,unsigned off) {
 (void)base;
 if(off==0x40) return mode==3?1:0;
 if(off==0x610) return mode==2?0:(mockirq?mockirq:(rxbytes==total?1:0));
 if(off==0x800) return mode==4?17:0;
 if(off==0x804) {
  if(mode==1)return 17;
  unsigned pending=txbytes-rxbytes,words=(pending+3)/4;
  uint32_t value=words;
  if(pending && txbytes==total)value|=0x80000000u|((pending%4)<<28);
  return value;
 }
 if(off==0x780) {
  uint32_t word=0;for(unsigned i=0;i<4 && rxbytes<txbytes;i++,rxbytes++)word|=(uint32_t)mt_tx[rxbytes]<<(i*8);
  return word;
 }
 return 0;
}
'''
    tests = r'''
static void checksum(uint8_t *p,unsigned n) {
 unsigned s=0;for(unsigned i=0;i<n-2;i++)s+=p[i];p[n-2]=s;p[n-1]=s>>8;
}
static void u16(uint8_t *p,unsigned v) {p[0]=v;p[1]=v>>8;}
static void u32(uint8_t *p,unsigned v) {u16(p,v);u16(p+2,v>>16);}
static void reset(void) {txbytes=rxbytes=total=cmdcount=waits=mode=0;mt_bad=false;mockirq=0;}
int main(void) {
 for(unsigned n=1;n<=1032;n++) {
  reset();for(unsigned i=0;i<n;i++)mt_tx[i]=(uint8_t)(i*37);
  assert(mt_exchange(n));assert(rxbytes==n && txbytes==n);
  assert(!memcmp(mt_tx,mt_rx,n));assert(cmdcount==3 && commands[0]==8 && commands[1]==3 && commands[2]==9);
 }
 for(unsigned m=1;m<=4;m++) {reset();mode=m;assert(!mt_exchange(24));assert(waits<=5000);}
 reset();assert(!mt_exchange(1033));assert(cmdcount==0);
 uint8_t data[1024]={0};unsigned pos=37,n=pos+144;
 u16(data,n);data[13]=1;u32(data+pos+44,0x10308);u16(data+pos+48,8);u16(data+pos+50,8);
 u16(data+pos+138,10800);u16(data+pos+140,24000);checksum(data,n);
 assert(mt_parse_info(data,n) && mt_event==0x10308 && mt_factor==10);
 u16(data+pos+140,23999);checksum(data,n);assert(!mt_parse_info(data,n));
 u16(data+pos+140,24000);data[32]=6;checksum(data,n);assert(!mt_parse_info(data,n));
 data[32]=0;n=pos+116;u16(data,n);data[4]=0x22;checksum(data,n);
 assert(!mt_parse_info(data,n));mt_legacy_range=true;assert(mt_parse_info(data,n));
 uint8_t f[90]={0};f[0]=0x80;f[2]=1;checksum(f,8);u16(f+10,10354);u16(f+12,23125);checksum(f+8,10);
 assert(mt_frame(f,18));assert(downs==1 && xx==1035 && yy==2312);
 unsigned calls=hidcalls;f[9]^=1;assert(!mt_frame(f,18) && calls==hidcalls);f[9]^=1;
 u16(f+10,0);u16(f+12,23999);checksum(f+8,10);assert(mt_frame(f,18));assert(xx==0 && yy==2399);
 f[2]=0;checksum(f,8);assert(mt_frame(f,10));assert(ups==1);
 f[2]=2;checksum(f,8);memcpy(f+16,f+8,8);checksum(f+8,18);calls=hidcalls;
 assert(!mt_frame(f,26) && calls==hidcalls); /* duplicate ID, atomic rejection */
 f[2]=11;checksum(f,8);assert(!mt_frame(f,90));
 /* Fuzz every truncation and many structured corruptions under sanitizers. */
 uint32_t random=1;
 for(unsigned iter=0;iter<100000;iter++) {
  unsigned len=iter%1025;for(unsigned i=0;i<len;i++){random=random*1664525+1013904223;data[i]=random>>24;}
  if(len>=2 && (iter&1)){u16(data,len);checksum(data,len);}
  (void)mt_parse_info(data,len);
  unsigned flen=iter%91;memcpy(f,data,flen);if(flen>=8)checksum(f,8);
  (void)mt_frame(f,flen);
 }
 puts("PASS: 1032 FIFO lengths/order, command3/CS8/9, faults/timeouts, IC-info schemas, checksums, 10x mapping, down/move/up, atomic duplicate rejection, 100000 malformed/truncated cases");
}
'''
    with tempfile.TemporaryDirectory(prefix='marble-input-test-') as directory:
        c = Path(directory) / 'input.c'
        binary = Path(directory) / 'input'
        c.write_text(harness + body + tests)
        subprocess.run(['clang', '-std=gnu11', '-O1', '-g', '-fsanitize=address,undefined',
                        '-fno-omit-frame-pointer', str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    subprocess.run([__import__("sys").executable, str(Path(__file__).with_name("test-marble-touchinit.py")), str(args.tree)], check=True)
    subprocess.run([__import__("sys").executable, str(Path(__file__).with_name("test-marble-touch-power.py")), str(args.tree)], check=True)


if __name__ == '__main__':
    main()
