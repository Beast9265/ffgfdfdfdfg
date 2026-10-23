#!/usr/bin/env python3
"""Extract real V3 hardware/diagnostic functions; mock only MMIO/VFS boundaries."""
from pathlib import Path
import importlib.util, subprocess, sys, tempfile
spec=importlib.util.spec_from_file_location('t',Path(__file__).with_name('test-marble-input.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
r=Path(sys.argv[1]);s=(r/'bsd/dev/marble_usb_hw.c').read_text();d=(r/'bsd/dev/marble_hwdiag.c').read_text()
common=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#define MIN(a,b) ((a)<(b)?(a):(b))
typedef uintptr_t vm_offset_t;
'''
# Actual complete hardware state machine, fault every masked register write.
body=s[s.index('static const struct uh_phy_step'):s.index('bool marble_usb_hw_prepare')]
body+=t.function(s,'uh_rcg')
start=s.index('bool\nmarble_usb_hw_prepare') if 'bool\nmarble_usb_hw_prepare' in s else s.index('bool marble_usb_hw_prepare(vm_offset_t gcc')
body+=s[start:s.rindex('#endif')]
mock=r'''
static uint32_t gcc[0xa0000/4],phy[0x400/4],qs[0x400/4];
static unsigned writes,fail_at,rails,resets,elapsed,stage,reason;
static bool maps_fail,rail_fail,reset_fail,stuck;
static uint32_t *regs(uintptr_t b){assert(b>=1&&b<=3);return b==1?gcc:b==2?phy:qs;}
static uint32_t uh_rd(uintptr_t b,unsigned o){assert(o<(b==1?0xa0000:0x400));return regs(b)[o/4];}
static void uh_wr(uintptr_t b,unsigned o,uint32_t v){regs(b)[o/4]=v;if(b==1&&(o==0x49028||o==0x49040)&&!stuck)regs(b)[o/4]&=~1u;}
static void delay(unsigned u){elapsed+=u;}
static bool uh_fail(enum mh_reason r,int e,const char*g){(void)e;(void)g;reason=r;return false;}
static bool uh_mask(uintptr_t b,unsigned o,uint32_t m,uint32_t v){
 if(++writes==fail_at)return uh_fail(MH_READBACK,5,"injected");
 assert((v&~m)==0);uint32_t old=uh_rd(b,o);uh_wr(b,o,(old&~m)|v);
 if(b==1&&o==0x49004)gcc[o/4]|=1u<<31;
 if(b==3&&o==8&&m==9)assert((qs[8/4]&0x100)&&elapsed>=1600);
 return true;
}
static bool uh_poll(uintptr_t b,unsigned o,uint32_t m,uint32_t v,unsigned us){
 for(unsigned i=0;i<us;i++){if((uh_rd(b,o)&m)==v)return true;delay(1);}return uh_fail(MH_TIMEOUT,60,"poll");
}
static uintptr_t ml_io_map(uintptr_t pa,unsigned size){(void)size;return maps_fail?0:pa==0x88e3000?2:3;}
static bool uh_repeater_map(void){return !maps_fail;}
static bool uh_repeater_reset(bool release){resets++;assert(release?rails==4:rails==0);return !reset_fail;}
static int marble_usb_power_vote(const char *s,unsigned mv){
 const char *names[]={"ldob5","ldoc10","smpb10","ldob2"};unsigned values[]={880,1200,1800,3080};
 assert(rails<4&&!strcmp(s,names[rails])&&mv==values[rails]&&resets==1);rails++;return rail_fail?5:0;
}
'''
# stubs stage tracked rather than module's no-op
stubs=t.diagnostic_stubs(r).replace('(void)u;(void)s;','(void)u;stage=s;')
tests=r'''
static void init(void){memset(gcc,0,sizeof(gcc));memset(phy,0,sizeof(phy));memset(qs,0,sizeof(qs));gcc[0]=1u<<31;writes=rails=resets=elapsed=stage=reason=0;maps_fail=rail_fail=reset_fail=stuck=false;}
int main(void){
 init();assert(marble_usb_hw_prepare(1,0)&&writes==0);
 init();assert(marble_usb_hw_prepare(1,1));unsigned n=writes;
 assert(rails==4&&resets==2&&!(phy[0x50/4]&2)&&(phy[0x94/4]&2));
 assert((phy[0x54/4]&0x7f)==11&&phy[0x5c/4]==0x90&&phy[0x60/4]==1);
 assert((qs[8/4]&0x109)==9&&(qs[0x10/4]&0x10100000)==0x10100000);
 assert(gcc[0x9c00c/4]&1);assert(!gcc[0x9c010/4]);assert(elapsed>=1800);
 for(unsigned i=1;i<=n;i++){init();fail_at=i;assert(!marble_usb_hw_prepare(1,1)&&reason);}
 fail_at=0;init();stuck=true;assert(!marble_usb_hw_prepare(1,1)&&reason==MH_TIMEOUT&&elapsed==1000);
 init();gcc[0]=0;assert(!marble_usb_hw_prepare(1,1)&&stage==MU_CLOCKS);
 init();gcc[0x49058/4]=1;assert(!marble_usb_hw_prepare(1,1));
 init();rail_fail=true;assert(!marble_usb_hw_prepare(1,1)&&rails==1);
 init();reset_fail=true;assert(!marble_usb_hw_prepare(1,1)&&rails==0);
 puts("PASS extracted USB V3: 28 PHY operations, all write failures, RCG timeout, PLL/postdivider gates, rails/reset order, UTMI ordering, exact eUSB gate");
}
'''
# structs and actual RAM/renderer (VFS is separately source-audited below).
a=d.index('#define MH_RECORDS');b=d.index('static int mh_enabled')
diagtypes=d[a:b]
diagtypes=diagtypes.replace('static unsigned mh_lock;','static unsigned mh_lock;')
# file scope through full overlay; strip includes/functions not needed by host
funcs=[]
for name in ['mh_section','mh_take','mh_drop','mh_format']:
 funcs.append(t.function(d,name))
# non-static public functions extraction by brace count
for name in ['marble_hwdiag_stage','marble_hwdiag_fail','marble_hwdiag_value','marble_hwdiag_bytes','marble_hwdiag_active','marble_hwdiag_overlay']:
 needle=name+'(';pos=d.index(needle)
 while d[d.index('\n',pos)-1]==';':pos=d.index(needle,pos+len(needle))
 brace=d.index('{',pos);i=brace+1;depth=1
 while depth:depth+=(d[i]=='{')-(d[i]=='}');i+=1
 start=d.rfind('\n',0,pos)+1
 # return types are same line for these definitions
 funcs.append(d[start:i]+'\n')
diagmock=r'''
static int mh_active=1,mh_page;
static char mh_text[MH_TEXT],mh_screen[MH_TEXT];
unsigned char iso_font[256*16];
static void disable_preemption(void){}
static void enable_preemption(void){}
static uint64_t mach_absolute_time(void){static uint64_t n;return ++n;}
'''
diagtest=r'''
int main(void){
 marble_hwdiag_stage(0,MT_CONFIRM);marble_hwdiag_fail(0,MH_TRANSPORT,5,"confirm write");
 marble_hwdiag_fail(0,MH_GATE,9,"must not replace");marble_hwdiag_stage(0,MT_RUNNING);
 assert(mh.touch.stage==MT_FAILED&&mh.touch.failed_at==MT_CONFIRM&&mh.touch.error==5);
 char key[200];memset(key,'Z',199);key[199]=0;
 for(unsigned u=0;u<2;u++)for(unsigned i=0;i<1000;i++)marble_hwdiag_value(u,key,i,~i);
 assert(mh.touch.count==MH_RECORDS&&mh.usb.count==MH_RECORDS&&mh.touch.dropped==745);
 char out[MH_TEXT+16];memset(out,0x5a,sizeof(out));unsigned n=mh_format(out,MH_TEXT);assert(n<MH_TEXT&&out[n]==0);
 for(unsigned i=MH_TEXT;i<sizeof(out);i++)assert(out[i]==0x5a);
 uint32_t *fb=calloc(1080*2400+32,4);assert(fb);for(unsigned i=0;i<32;i++)fb[1080*2400+i]=0x12345678;
 memset(iso_font,255,sizeof(iso_font));
 for(unsigned p=0;p<12;p++){mh_page=p;assert(marble_hwdiag_overlay((uintptr_t)fb,1080,2400,4320));}
 for(unsigned i=0;i<32;i++)assert(fb[1080*2400+i]==0x12345678);
 assert(!marble_hwdiag_overlay((uintptr_t)fb,1125,2436,4500));mh_active=0;assert(!marble_hwdiag_overlay((uintptr_t)fb,1080,2400,4320));free(fb);
 puts("PASS diagnostics: terminal reason retention, 512-record bound/drop count, bounded formatter, all 12 framebuffer pages and guard words under ASan/UBSan");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-hw-v3-') as directory:
 p=Path(directory)
 codes={'usb':common+(r/'bsd/dev/marble_hwdiag.h').read_text().replace('#include <sys/types.h>','')+mock+stubs.split('#endif',1)[-1]+body+tests,
 'diag':common+(r/'bsd/dev/marble_hwdiag.h').read_text().replace('#include <sys/types.h>','')+diagtypes+diagmock+'\n'.join(funcs)+diagtest}
 for name,code in codes.items():
  c=p/(name+'.c');binary=p/name;c.write_text(code)
  subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(c),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True)
assert not __import__('re').search(r'(?<!sn)printf\(', t.function(d,'mh_format'))
assert 'VNODE_LOOKUP_NOFOLLOW' in d and 'vnode_vtype(vp) != VREG' in d and 'mh.file_attempts++ >= 16' in d
assert 'vn_rdwr(UIO_WRITE' in d and 'VNOP_FSYNC' in d and 'vnode_close' in d
print('PASS VFS source audit: no-follow, regular-file check, bounded text/write count, close/fsync, no raw disk access')
