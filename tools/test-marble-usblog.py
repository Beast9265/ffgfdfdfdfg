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
 puts("PASS USB: CDC-ECM topology/strings, 4MiB RAM-ring wrap/backlog, bounded read-only SMMUv2 bypass/translation/fault/duplicate/EXID gates; logger no printf, eight-chunk budget and send-failure rewind");
}
'''
with tempfile.TemporaryDirectory(prefix='marble-usblog-test-') as directory:
    c=Path(directory)/'test.c';binary=Path(directory)/'test'
    c.write_text(prefix+body+tests)
    subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(c),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
# Parse embedded host Python without starting a listener or touching networking.
host = Path(__file__).with_name('marble-usbnet.sh').read_text().split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
compile(host,'marble-usbnet.sh embedded Python','exec')
subprocess.run(['sh','-n',str(Path(__file__).with_name('marble-usbnet.sh'))],check=True)
print('PASS host shell/Python syntax; host networking deliberately not executed')
