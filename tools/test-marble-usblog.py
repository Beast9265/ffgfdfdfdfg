#!/usr/bin/env python3
"""No hardware: extract and test shared USB descriptors, RAM ring and SMMU guard."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
spec = importlib.util.spec_from_file_location('extract', Path(__file__).with_name('test-marble-input.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
root = Path(sys.argv[1])
usb = (root/'bsd/dev/sweet_usb.c').read_text()
ufs = (root/'bsd/dev/sweet_ufs.c').read_text()
serial = (root/'osfmk/console/serial_console.c').read_text()
log_body = module.function(usb, 'ud_log_thread')
assert 'printf(' not in log_body and 'IOLog(' not in log_body
assert 'unsigned budget = 8' in log_body and 'pos = committed' in log_body
assert 'if (!ud.host_ready) continue;' in log_body
# Persistent writer must remain unavailable on MARBLE, while RAM capture is shared.
assert '#ifdef ARM64_BOARD_CONFIG_SWEET\nstruct sweet_log_header' in ufs
assert '#if defined(ARM64_BOARD_CONFIG_SWEET) || defined(ARM64_BOARD_CONFIG_MARBLE)\n\tsweet_log_append(c, size);\n#endif' in serial
prefix = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stdatomic.h>
#define ARM64_BOARD_CONFIG_MARBLE 1
#define ETHER_ADDR_LEN 6
#define USB_LOG "MARBLE USB: "
#define MIN(a,b) ((a)<(b)?(a):(b))
#define SWEET_LOG_SIZE (4u<<20)
#define relaxed memory_order_relaxed
#define os_atomic_add_orig(p,v,o) atomic_fetch_add_explicit(p,v,o)
#define os_atomic_load(p,o) atomic_load_explicit(p,o)
static char sweet_log_ring[SWEET_LOG_SIZE];
static _Atomic uint64_t sweet_log_total;
typedef uintptr_t vm_offset_t;
static uint32_t regs[0x10000/4];
static vm_offset_t ml_io_map(uintptr_t pa,unsigned n){assert(pa==0x15000000&&n==0x10000);return 1;}
static uint32_t usb_rd(vm_offset_t base,unsigned off){assert(base==1&&off<0x10000&&!(off&3));return regs[off/4];}
'''
body = usb[usb.index('static const uint8_t ud_dev_desc'):usb.index('static uint32_t\nud_string')]
body += module.function(usb, 'ud_string') + module.function(usb, 'ud_marble_dma_ok')
prefix += r'''
#define printf(...) ((void)0)
#define UD_SETUP 0x1040
#define UD_DATA 0x1100
#define DCFG 0xc700
#define TRBCTL_DATA (5u<<4)
static uint8_t dma[0x4000+16];
static struct {uintptr_t dma; bool data_in,configured; unsigned state,data_alt;} ud;
enum {EP0_SETUP,EP0_DATA,EP0_WAIT_STATUS2,EP0_WAIT_STATUS3,EP0_STATUS};
static unsigned starts,stalls,last_len,last_ep;static uint32_t cfg;
static uint32_t dwc_rd(unsigned off){assert(off==DCFG);return cfg;}
static void dwc_wr(unsigned off,uint32_t v){assert(off==DCFG);cfg=v;}
static void ud_start(unsigned ep,unsigned off,unsigned n,unsigned ctl){assert(ep<2&&off==UD_DATA&&n<=512&&ctl==TRBCTL_DATA);starts++;last_len=n;last_ep=ep;}
static void ud_stall(void){stalls++;}
static void ud_configure(void){ud.configured=true;}
static void ud_notify_connected(void){}
static void ud_link_event(bool up){(void)up;}
'''
body += module.function(usb, 'ud_setup')
for name,typ in [('sweet_log_append','void'),('sweet_log_copy','uint32_t'),('sweet_log_position','uint64_t')]:
    start = ufs.index('\n'+typ+'\n'+name+'(')+1
    brace = ufs.index('{',start); end=brace+1;depth=1
    while depth:
        depth += (ufs[end]=='{')-(ufs[end]=='}');end+=1
    body += ufs[start:end]+'\n'
tests = r'''
int main(void){
 assert(sizeof(ud_dev_desc)==18&&sizeof(ud_cfg_desc)==80&&ud_dev_desc[7]==64);
 assert(ud_cfg_desc[4]==2);unsigned pos=0,bulk=0,intr=0;
 while(pos<80){unsigned n=ud_cfg_desc[pos];assert(n>=2&&pos+n<=80);
  if(ud_cfg_desc[pos+1]==5){unsigned addr=ud_cfg_desc[pos+2];if(ud_cfg_desc[pos+3]==2){assert(addr==0x81||addr==1);bulk++;}else{assert(addr==0x82&&ud_cfg_desc[pos+3]==3);intr++;}}
  pos+=n;
 }
 assert(bulk==2&&intr==1);uint8_t str[128];assert(ud_string(0,str)==4);assert(ud_string(99,str)==0);
 assert(ud_string(1,str)==22&&str[2]=='i');assert(ud_string(4,str)==26);
 static char input[5u<<20],out[1400];for(unsigned i=0;i<sizeof(input);i++)input[i]=(char)(i*37);
 sweet_log_append(input,sizeof(input));assert(sweet_log_position()==sizeof(input));
 uint64_t cursor=0;unsigned copied=0;
 while(cursor<sizeof(input)){unsigned n=sweet_log_copy(&cursor,out,sizeof(out));assert(n&&n<=1400);assert(!memcmp(out,input+cursor-n,n));copied+=n;}
 assert(copied==SWEET_LOG_SIZE&&!sweet_log_copy(&cursor,out,1400));
 memset(regs,0,sizeof(regs));assert(!ud_marble_dma_ok());
 regs[0x20/4]=(1u<<27)|120;regs[0]=1;assert(ud_marble_dma_ok());
 regs[0]=1|(1u<<10);assert(!ud_marble_dma_ok());
 regs[0]=0;assert(ud_marble_dma_ok());regs[0]=1u<<10;assert(!ud_marble_dma_ok());
 regs[0x800/4]=1u<<31;regs[0xc00/4]=1u<<16;assert(ud_marble_dma_ok());
 regs[0xc00/4]=0;assert(!ud_marble_dma_ok());regs[0xc00/4]=2u<<16;assert(!ud_marble_dma_ok());
 regs[0xc00/4]=1u<<16;regs[0x804/4]=1u<<31;regs[0xc04/4]=1u<<16;assert(!ud_marble_dma_ok());
 regs[0x804/4]=0;regs[0]|=8;regs[0x20/4]|=256;regs[0x800/4]=0;regs[0xc00/4]=(1u<<16)|(1u<<10);assert(ud_marble_dma_ok());
 ud.dma=(uintptr_t)dma;memset(dma+0x4000,0x5a,16);
 uint8_t *setup=dma+UD_SETUP;
 memset(setup,0,8);setup[0]=0x80;setup[1]=6;setup[3]=1;setup[6]=18;ud_setup();
 assert(last_len==18&&last_ep==1&&!memcmp(dma+UD_DATA,ud_dev_desc,18));
 setup[6]=8;ud_setup();assert(last_len==8);
 setup[1]=5;setup[0]=0;setup[2]=42;setup[3]=setup[6]=0;ud_setup();assert(((cfg>>3)&127)==42&&ud.state==EP0_WAIT_STATUS2);
 setup[1]=9;setup[2]=1;ud_setup();assert(ud.configured);
 uint32_t rng=1;
 for(unsigned i=0;i<100000;i++){for(unsigned b=0;b<8;b++){rng=rng*1664525+1013904223;setup[b]=rng>>24;}ud_setup();}
 for(unsigned i=0;i<16;i++)assert(dma[0x4000+i]==0x5a);
 puts("PASS extracted EP0: descriptor short reads, SET_ADDRESS/CONFIGURATION, 100000 arbitrary SETUP packets with TRB/buffer bounds");
 puts("PASS USB: CDC-ECM topology/strings, 4MiB RAM-ring wrap/backlog, bounded read-only SMMUv2 bypass/translation/fault/duplicate/EXID gates; logger no printf, eight-chunk budget and send-failure rewind");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-usblog-test-') as directory:
    c=Path(directory)/'test.c';binary=Path(directory)/'test'
    c.write_text(prefix+module.diagnostic_stubs(root)+body+tests)
    subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
# Parse embedded host Python without starting a listener or touching networking.
host = Path(__file__).with_name('marble-usbnet.sh').read_text().split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
compile(host,'marble-usbnet.sh embedded Python','exec')
subprocess.run(['sh','-n',str(Path(__file__).with_name('marble-usbnet.sh'))],check=True)
print('PASS host shell/Python syntax; host networking deliberately not executed')
