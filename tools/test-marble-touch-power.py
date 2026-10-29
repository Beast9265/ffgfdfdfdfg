#!/usr/bin/env python3
"""Exercise actual cmd-db and ACTIVE-TCS logic with bounded synthetic MMIO."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
spec = importlib.util.spec_from_file_location('extract', Path(__file__).with_name('test-marble-input.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
s = (Path(sys.argv[1]) / 'bsd/dev/marble_touch_power.c').read_text()
constants = s[s.index('#define RH_RSC_PA'):s.index('static vm_offset_t rh_rsc')]
prefix = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <errno.h>
typedef uintptr_t vm_offset_t;
'''
mock = r'''
#define RH_ARC 3u
static uintptr_t rh_tcs=1,rh_db=2;
static uint32_t rh_db_size=0x20000,db[0x20000/4],tcs[0x3000/4];
static unsigned rh_ncpt=16,elapsed,triggered;
static uint32_t last_addr,last_data;
static bool rh_poisoned,timeout;
static uint32_t rh_read(uintptr_t base,uint32_t off){
 assert(!(off&3));if(base==1){assert(off<0x3000);return tcs[off/4];}
 assert(base==2&&off<rh_db_size);return db[off/4];
}
static void rh_write(uintptr_t base,uint32_t off,uint32_t value){
 assert(base==1&&off<0x3000);unsigned slot=off/RH_TCS_STRIDE,reg=off%RH_TCS_STRIDE;
 /* All payload/control writes must stay inside the three ACTIVE slots. */
 assert(off<=RH_IRQ_CLEAR||slot<RH_ACTIVE_N);
 if(off==RH_IRQ_CLEAR){tcs[RH_IRQ_STATUS/4]&=~value;return;}
 tcs[off/4]=value;
 if(reg==RH_CONTROL&&(value&RH_TRIGGER)){
  triggered++;last_addr=tcs[(slot*RH_TCS_STRIDE+RH_ADDR)/4];
  last_data=tcs[(slot*RH_TCS_STRIDE+RH_DATA)/4];if(timeout)return;
  tcs[(slot*RH_TCS_STRIDE+RH_STATUS)/4]=1;
  for(unsigned c=0;c<3;c++)tcs[(slot*RH_TCS_STRIDE+RH_CMD_STATUS+c*RH_CMD_STRIDE)/4]=RH_ISSUED|RH_COMPLETE;
  tcs[RH_IRQ_STATUS/4]|=1u<<slot;
 }
}
static void delay(unsigned n){elapsed+=n;}
'''
body = '\n'.join(module.function(s, name) for name in
                ['rh_sync', 'rh_db16', 'rh_range', 'rh_lookup',
                 'rh_lookup_arc', 'rh_one_free', 'rh_send_one',
                 'rh_free', 'rh_send'])
tests = r'''
static void half(unsigned off,unsigned v){assert(off<sizeof(db));uint8_t *p=(uint8_t*)db;p[off]=v;p[off+1]=v>>8;}
static void init(unsigned major){
 memset(tcs,0,sizeof(tcs));memset(db,0,sizeof(db));elapsed=triggered=0;
 last_addr=last_data=0;timeout=rh_poisoned=false;
 rh_cmd_stride=major==3?24:20;rh_wait=major==3?0x20:0x10;rh_control=rh_wait+4;rh_status=rh_wait+8;rh_enable=rh_wait+12;
 rh_msgid=major==3?0x34:0x30;rh_addr=rh_msgid+4;rh_data=rh_msgid+8;rh_cmd_status=rh_msgid+12;
 for(unsigned t=0;t<8;t++)tcs[(t*RH_TCS_STRIDE+RH_STATUS)/4]=1;
 tcs[RH_IRQ_EN/4]=0xaa;
 for(unsigned i=3*RH_TCS_STRIDE/4;i<sizeof(tcs)/4;i++)tcs[i]=0x12345678;
 half(8,4);half(10,0);half(12,48);half(14,2);
 memcpy((uint8_t*)db+RH_DB_HEADER,"ldoc2",5);db[(RH_DB_HEADER+16)/4]=0x40100;
 memcpy((uint8_t*)db+RH_DB_HEADER+24,"ldoc9",5);db[(RH_DB_HEADER+40)/4]=0x40200;
 half(24,3);half(26,48);half(28,96);half(30,2);
 memcpy((uint8_t*)db+RH_DB_HEADER+48,"mx.lvl",6);
 db[(RH_DB_HEADER+64)/4]=0x30010;half(RH_DB_HEADER+68,8);half(RH_DB_HEADER+70,0);
 memcpy((uint8_t*)db+RH_DB_HEADER+72,"cx.lvl",6);
 db[(RH_DB_HEADER+88)/4]=0x30020;half(RH_DB_HEADER+92,8);half(RH_DB_HEADER+94,8);
 half(RH_DB_HEADER+96,0);half(RH_DB_HEADER+98,16);half(RH_DB_HEADER+100,48);half(RH_DB_HEADER+102,0);
 half(RH_DB_HEADER+104,0);half(RH_DB_HEADER+106,16);half(RH_DB_HEADER+108,64);half(RH_DB_HEADER+110,0);
}
int main(void){
 for(unsigned major=2;major<=3;major++){
  init(major);uint32_t address=0;assert(!rh_lookup("ldoc2",&address)&&address==0x40100);
  assert(!rh_lookup("ldoc9",&address)&&address==0x40200);assert(rh_lookup("absent",&address)==ENODEV);
  uint32_t aux=0;uint16_t len=0;
  assert(!rh_lookup_arc("mx.lvl",&address,&aux,&len)&&address==0x30010&&len==8);
  assert(rh_db16(aux+4)==48);assert(!rh_send_one(address,2));
  assert(last_addr==0x30010&&last_data==2&&triggered==1&&!rh_poisoned);
  triggered=0;
  uint32_t inherited[0x3000/4];memcpy(inherited,tcs,sizeof(tcs));
  tcs[RH_CONTROL/4]=RH_AMC_EN;inherited[RH_CONTROL/4]=RH_AMC_EN;
  tcs[RH_MSGID/4]=0x55;tcs[RH_ADDR/4]=0x66;tcs[RH_DATA/4]=0x77;
  assert(!rh_send(0x40100,1800)&&triggered==1&&!rh_poisoned);
  assert(tcs[RH_CONTROL/4]==RH_AMC_EN&&tcs[RH_MSGID/4]==0x55&&tcs[RH_ADDR/4]==0x66&&tcs[RH_DATA/4]==0x77);
  assert(tcs[RH_IRQ_EN/4]==0xaa&&tcs[RH_ENABLE/4]==0&&tcs[RH_WAIT/4]==0);
  assert(!memcmp(tcs+3*RH_TCS_STRIDE/4,inherited+3*RH_TCS_STRIDE/4,sizeof(tcs)-3*RH_TCS_STRIDE));
  init(major);for(unsigned t=0;t<3;t++)tcs[(t*RH_TCS_STRIDE+RH_ENABLE)/4]=1;
  assert(rh_send(0x40100,1800)==EBUSY&&triggered==0);
  init(major);timeout=true;assert(rh_send(0x40100,1800)==ETIMEDOUT&&rh_poisoned&&triggered==1&&elapsed==RH_TIMEOUT_US);
  assert(!(tcs[RH_IRQ_EN/4]&1));
  init(major);half(14,0xffff);assert(rh_lookup("ldoc2",&address)==EINVAL);
  init(major);memcpy((uint8_t*)db+RH_DB_HEADER+24,"ldoc2",6);assert(rh_lookup("ldoc2",&address)==ENODEV);
 }
 puts("PASS RPMh: ARC/VRM cmd-db lookup, HLVL transaction, v2/v3 layouts, ACTIVE-only ownership, payload/IRQ preservation, no free TCS refusal, timeout quarantine");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-power-test-') as directory:
    c=Path(directory)/'test.c';binary=Path(directory)/'test'
    c.write_text(prefix+module.diagnostic_stubs(sys.argv[1])+constants+mock+body+tests)
    subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
