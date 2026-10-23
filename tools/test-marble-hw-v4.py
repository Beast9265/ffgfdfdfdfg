#!/usr/bin/env python3
"""Fault-inject extracted v4 clock/core helpers; no hardware access."""
from pathlib import Path
import importlib.util, subprocess, sys, tempfile
spec=importlib.util.spec_from_file_location('t',Path(__file__).with_name('test-marble-input.py'));t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
r=Path(sys.argv[1]);touch=(r/'bsd/dev/marble_touch.c').read_text();usb=(r/'bsd/dev/sweet_usb.c').read_text()
common='''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
typedef uintptr_t vm_offset_t;
'''+(r/'bsd/dev/marble_hwdiag.h').read_text().replace('#include <sys/types.h>','')+'''
static unsigned reason,stage,elapsed;static char gate[128],last_value_name[64];
void marble_hwdiag_stage(unsigned u,unsigned s){(void)u;if(!reason)stage=s;}
void marble_hwdiag_fail(unsigned u,enum mh_reason r,int e,const char*g){(void)u;(void)e;if(!reason){reason=r;snprintf(gate,sizeof(gate),"%s",g);}}
void marble_hwdiag_value(unsigned u,const char*n,uint32_t b,uint32_t a){(void)u;(void)b;(void)a;snprintf(last_value_name,sizeof(last_value_name),"%s",n);}
static void delay(unsigned n){elapsed+=n;}
'''
clockmock='''
static uintptr_t mt_gcc=1;static unsigned mt_clock_level;static bool mt_rcg_forced;
static uint32_t regs[0x70000/4];static unsigned fault;static bool source_ready;
static uint32_t mt_rd(uintptr_t b,unsigned o){assert(b==1&&o<0x70000);return regs[o/4];}
static void mt_store(uintptr_t b,unsigned o,uint32_t v){assert(b==1);regs[o/4]=v;if(o==0x274e4&&(v&1)&&fault!=1){regs[o/4]&=~(1u|(1u<<31));source_ready=true;}}
static bool mt_mask(uintptr_t b,unsigned o,uint32_t m,uint32_t v){
 assert(!(v&~m));mt_store(b,o,(mt_rd(b,o)&~m)|v);
 if(o==0x62008){assert(source_ready);unsigned off[]={0x27004,0x27008,0x274dc};unsigned bits[]={6,7,14};for(unsigned i=0;i<3;i++)if((v&(1u<<bits[i]))&&fault!=i+2)regs[off[i]/4]&=~(1u<<31);}
 return true;
}
'''
clockbody='\n'.join(t.function(touch,n) for n in ['mt_clock_fail','mt_clock_snapshot','mt_clock_poll','mt_source_clock','mt_branch_clock','mt_ahb_branch_clock','mt_clocks'])
clocktests='''
static void init(void){memset(regs,0,sizeof(regs));memset(gate,0,sizeof(gate));memset(last_value_name,0,sizeof(last_value_name));regs[0x274e4/4]=1u<<31;regs[0x27004/4]=regs[0x27008/4]=regs[0x274dc/4]=1u<<31;reason=stage=elapsed=fault=0;source_ready=false;}
int main(void){
 init();assert(mt_clocks()&&source_ready&&!reason);assert(!(regs[0x274e4/4]&2));
 init();regs[0x274e8/4]=0x100001;regs[0x274e4/4]=0;source_ready=true;assert(mt_clocks());
 init();regs[0x27004/4]=regs[0x27008/4]=0;assert(mt_clocks());
 const unsigned expected[]={MH_S4_RCG_UPDATE,MH_M_AHB_BRANCH,MH_S_AHB_BRANCH,MH_S4_BRANCH};
 const char* names[]={"S4 RCG update timeout","QUP0 M_AHB halt timeout","QUP0 S_AHB halt timeout","S4 branch halt timeout"};
 for(unsigned f=1;f<=4;f++){init();fault=f;assert(!mt_clocks()&&reason==expected[f-1]&&!strcmp(gate,names[f-1])&&elapsed==1000);}
 init();regs[0x274f8/4]=1;regs[0x27508/4]=1;source_ready=true;assert(mt_clocks()&&mt_clock_level==2);
 init();regs[0x274f8/4]=1;assert(!mt_clocks()&&reason==MH_PROTOCOL);
 /* Qualcomm BRANCH_HALT_VOTED: declared wrapper AHB HWCG bit1 bypasses
  * CLK_OFF polling. S4 deliberately has no equivalent shortcut. */
 init();source_ready=true;fault=2;regs[0x27004/4]=0x80000002;assert(mt_ahb_branch_clock(6,0x27004,MT_CLOCK_M_AHB,MH_M_AHB_BRANCH,"M_AHB","QUP0 M_AHB halt timeout")&&!strcmp(last_value_name,"M_AHB_HWCG_ACCEPTED")&&!elapsed);
 init();source_ready=true;fault=2;regs[0x27004/4]=0x00000002;assert(mt_ahb_branch_clock(6,0x27004,MT_CLOCK_M_AHB,MH_M_AHB_BRANCH,"M_AHB","QUP0 M_AHB halt timeout")&&!strcmp(last_value_name,"M_AHB_HWCG_ACCEPTED")&&!elapsed);
 init();source_ready=true;regs[0x27004/4]=0x00000000;assert(mt_ahb_branch_clock(6,0x27004,MT_CLOCK_M_AHB,MH_M_AHB_BRANCH,"M_AHB","QUP0 M_AHB halt timeout")&&!strcmp(last_value_name,"M_AHB_CLK_OFF_CLEAR")&&!elapsed);
 init();source_ready=true;fault=2;regs[0x27004/4]=0x80000000;assert(!mt_ahb_branch_clock(6,0x27004,MT_CLOCK_M_AHB,MH_M_AHB_BRANCH,"M_AHB","QUP0 M_AHB halt timeout")&&reason==MH_M_AHB_BRANCH&&elapsed==1000);
 init();source_ready=true;fault=2;regs[0x27004/4]=0xffffffff;assert(!mt_ahb_branch_clock(6,0x27004,MT_CLOCK_M_AHB,MH_M_AHB_BRANCH,"M_AHB","QUP0 M_AHB halt timeout")&&reason==MH_READBACK&&!strcmp(last_value_name,"M_AHB_CBCR_UNREADABLE")&&!elapsed);
 init();source_ready=true;fault=3;regs[0x27008/4]=0x80000002;assert(mt_ahb_branch_clock(7,0x27008,MT_CLOCK_S_AHB,MH_S_AHB_BRANCH,"S_AHB","QUP0 S_AHB halt timeout")&&!strcmp(last_value_name,"S_AHB_HWCG_ACCEPTED")&&!elapsed);
 init();source_ready=true;fault=4;regs[0x274dc/4]=0x80000002;assert(!mt_branch_clock(14,0x274dc,MT_CLOCK_S4,MH_S4_BRANCH,"S4 branch halt timeout")&&reason==MH_S4_BRANCH&&elapsed==1000);
 init();source_ready=true;regs[0x274dc/4]=0;assert(mt_branch_clock(14,0x274dc,MT_CLOCK_S4,MH_S4_BRANCH,"S4 branch halt timeout"));
 puts("PASS Qualcomm HWCG AHB acceptance, active/unreadable/timeout states, strict S4, parent-before-votes and DFS ownership");}
'''
usbmocks='''
#define CBCR_CLK_OFF (1u<<31)
#define DWC3_PA 0xa600000
#define DWC3_SIZE 0x10000
static uint32_t gcc[0xa0000/4],dwc[0x10000/4];static bool mapfail;
static uint32_t usb_rd(uintptr_t b,unsigned o){return b==1?gcc[o/4]:((uint32_t*)b)[o/4];}
static uintptr_t ml_io_map(uintptr_t p,unsigned s){assert(p==DWC3_PA&&s>=0xd93c);return mapfail?0:(uintptr_t)dwc;}
'''
usbody='\n'.join(t.function(usb,n) for n in ['ud_marble_post_clocks','ud_marble_core_prepare']).replace('__asm__ volatile("dsb sy" ::: "memory");','')
usbody=usbody.replace('*(volatile uint32_t *)(dwc+0xc110)=(ctl&~(3u<<12))|(2u<<12);','if(fault!=1) *(volatile uint32_t *)(dwc+0xc110)=(ctl&~(3u<<12))|(2u<<12);').replace('*(volatile uint32_t *)(dwc+0xc200)=(phy&~mask)|(9u<<10);','if(fault!=2) *(volatile uint32_t *)(dwc+0xc200)=(phy&~mask)|(9u<<10);')
usbt='''
static void init(void){memset(gcc,0,sizeof(gcc));memset(dwc,0,sizeof(dwc));gcc[0x49004/4]=1u<<31;gcc[0x9c00c/4]=1;dwc[0xc120/4]=0x55333333;reason=stage=fault=0;mapfail=false;}
int main(void){
 const unsigned off[]={0x49004,0x49018,0x49020,0x49024,0x49084,0x49088,0x9c00c};
 const unsigned expected[]={MH_POST_GDSC_OFF,MH_POST_MASTER_OFF,MH_POST_SLEEP_OFF,MH_POST_UTMI_OFF,MH_POST_CFGNOC_OFF,MH_POST_AGGRE_OFF,MH_POST_EUSB_REF_OFF};
 init();assert(ud_marble_post_clocks(1)&&ud_marble_core_prepare(2));
 for(unsigned i=0;i<7;i++){init();gcc[off[i]/4]=i==0||i==6?0:1u<<31;assert(!ud_marble_post_clocks(1)&&reason==expected[i]);marble_hwdiag_fail(1,MH_GATE,0,"generic");assert(reason==expected[i]);}
 init();mapfail=true;assert(!ud_marble_core_prepare(2)&&reason==MH_DWC_MAP);
 const unsigned bad[]={0,~0u,0x12340000,0x34300000};for(unsigned i=0;i<4;i++){init();dwc[0xc120/4]=bad[i];assert(!ud_marble_core_prepare(2)&&reason==MH_GSNPSID_INVALID);}
 const unsigned ids[]={0x55330001,0x33310000,0x33320000};for(unsigned i=0;i<3;i++){init();dwc[0xc120/4]=ids[i];dwc[0xc1a0/4]=0x31323061;assert(ud_marble_core_prepare(2));}
 init();fault=1;assert(!ud_marble_core_prepare(2)&&reason==MH_DEVICE_ROLE);
 init();fault=2;assert(!ud_marble_core_prepare(2)&&reason==MH_USB2_CONFIG);
 puts("PASS all post-QSCRATCH clocks independently, map/ID/revision/role/PHY failures, first failure retained");}
'''
with tempfile.TemporaryDirectory(prefix='marble-v4-') as directory:
 for name,code in [('clock',common+clockmock+clockbody+clocktests),('usb',common+usbmocks+'static unsigned fault;\n'+usbody+usbt)]:
  p=Path(directory)/name;p.with_suffix('.c').write_text(code);subprocess.run(['clang','-O1','-g','-fsanitize=address,undefined',str(p.with_suffix('.c')),'-o',str(p)],check=True);subprocess.run([str(p)],check=True)
# Vendor five cells: channel, SE, protocol, TRE count, priority. This
# test documents decoding, and deliberately does not authorize runtime DMA.
def decode(cells):
 assert len(cells)==5
 ch,se,proto,tres,priority=cells
 assert ch in (0,1) and se<12 and proto in (1,2,3) and tres>0
 return ('TX' if ch==0 else 'RX',se,{1:'SPI',2:'UART',3:'I2C'}[proto],tres,priority)
assert decode([0,4,1,0x40,2])==('TX',4,'SPI',64,2)
assert decode([1,4,1,0x40,2])==('RX',4,'SPI',64,2)
assert 'USB probe refused' not in usb and 'gadget startup refused' not in usb
fb=(r/'iokit/Kernel/arm/SweetFramebuffer.cpp').read_text();diag=(r/'bsd/dev/marble_hwdiag.c').read_text()
assert fb.count('marble_hwdiag_overlay(')==2 # declaration plus one vsync caller
assert 'if (marble_hwdiag_active()) return;' in fb
assert 'glyph[gy] & (1u << gx)' in diag and 'mh_draw_revision==revision' in diag
assert 'glyph[gy] & (1u << gx)' in (r/'pexpert/arm/pe_serial.c').read_text()
print('PASS OEM five-cell decode; single overlay render path, console font convention, inactive present guard')
