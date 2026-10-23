#!/usr/bin/env python3
"""Run the actual replayed GPI and SMMU state machines with MMIO/DMA models.

No hardware access. Golden TREs are independent literals from Pzqqt cf63f539
msm_gpi.h macros. The MMIO models enforce GPII0-only writes, route ownership,
cache publication, IOVA bounds and command/event completion ordering.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import importlib.util

root=Path(sys.argv[1])
header=(root/'bsd/dev/marble_gpi.h').read_text().replace('#include <sys/types.h>','')
diag=(root/'bsd/dev/marble_hwdiag.h').read_text().replace('#include <sys/types.h>','')
spec=importlib.util.spec_from_file_location('touch_test',Path(__file__).with_name('test-marble-input.py'))
touch_test=importlib.util.module_from_spec(spec);spec.loader.exec_module(touch_test)
common=r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <errno.h>
#define MIN(a,b) ((a)<(b)?(a):(b))
typedef uintptr_t vm_offset_t; typedef unsigned long vm_size_t;
typedef uint64_t ppnum_t; typedef uint64_t addr64_t;
#define PAGE_SIZE 16384u
#define PAGE_MASK 16383u
#define KERN_SUCCESS 0
#define KMA_DATA 0
#define KMA_ZERO 0
#define KMA_PERMANENT 0
#define VM_KERN_MEMORY_IOKIT 0
#define TRUE 1
#define kernel_map 0
#define kernel_pmap 0
#define ptoa_64(x) ((uint64_t)(x)<<14)
static unsigned reason,stage,waited,snapshots;
void marble_hwdiag_stage(unsigned u,unsigned s){(void)u;if(!reason)stage=s;}
void marble_hwdiag_fail(unsigned u,enum mh_reason r,int e,const char*g){(void)u;(void)e;if(!reason){reason=r;fprintf(stderr,"gate: %s\n",g);}}
void marble_hwdiag_value(unsigned u,const char*n,uint32_t a,uint32_t b){(void)u;(void)n;(void)a;(void)b;}
void marble_hwdiag_bytes(unsigned u,const char*n,const uint8_t*p,unsigned z){(void)u;(void)n;(void)p;assert(z<=96);}
void marble_hwdiag_failure_snapshot(unsigned u){(void)u;snapshots++;}
static void delay(unsigned n){waited+=n;}
'''

def body(name):
    s=(root/'bsd/dev'/name).read_text()
    s=s[s.index('#define MS_PA') if name.endswith('smmu.c') else s.index('#define MC_CH'):]
    s=s[:s.rindex('#endif')]
    return re.sub(r'__asm__ volatile\([^;]+;', '', s)

def replace_body(source,name,replacement):
    start=source.index(name+'(')
    brace=source.index('{',start);end=brace+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[:brace]+'{'+replacement+'}'+source[end:]

pure=r'''
int main(void){
 _Static_assert(MT_FAILED==17 && MT_CLOCK_S4==21 && MU_FAILED==20,"preserve diagnostic ABI");
 uint32_t tx[5]={0,4,1,64,2},rx[5]={1,4,1,64,2};unsigned g,p;
 assert(!mg_decode(tx,&g,&p)&&g==0&&p==0);assert(!mg_decode(rx,&g,&p)&&g==0&&p==0);
 const unsigned vendor[]={0x20000,0x20080,0x21000,0x22000,0x22008,0x22100,0x23008,0x23010};
 const unsigned expected[]={0x910000,0x910080,0x911000,0x912000,0x912008,0x912100,0x913008,0x913010};
 for(unsigned i=0;i<8;i++)assert(MG_RESOURCE+mg_offset(vendor[i])==expected[i]);
 struct mg_tre a=mg_config(2,2,false),b=mg_go(1032,true),c=mg_buffer(0x103000,1032,true),d=mg_buffer(0x104000,1032,false);
 const uint32_t av[4]={0x03000004,0,0x00020002,0x00220001};
 const uint32_t bv[4]={3,0,1032,0x00200801};
 const uint32_t cv[4]={0x103000,0,1032,0x00100200};
 const uint32_t dv[4]={0x104000,0,1032,0x00100000};
 assert(!memcmp(&a,av,16)&&!memcmp(&b,bv,16)&&!memcmp(&c,cv,16)&&!memcmp(&d,dv,16));
 assert(mg_config(0,2,true).d[0]==0x03000104);assert(mg_go(13,false).d[0]==1&&mg_go(13,false).d[2]==0);
 for(unsigned count=64;count<=256;count*=4)for(unsigned rp=0;rp<count;rp++)for(unsigned wp=0;wp<count;wp++){
  unsigned used=(wp+count-rp)%count;assert(mg_available(rp,wp,count)==count-used-1);
  assert(mg_next(wp,count)==(wp+1)%count);assert(mg_index(0x100000+wp*16,0x100000,count)==(int)wp);
 }
 assert(mg_index(0x100001,0x100000,64)<0&&mg_index(0x100400,0x100000,64)<0);
 uint64_t tables[1536];assert(mg_tables(tables,0x840000000ull,40));
 for(unsigned i=0;i<1536;i++){
  uint64_t v=0;if(i==0)v=0x840001003ull;if(i==512)v=0x840002003ull;
  if(i>=1280&&i<1285)v=(0x840004000ull+(i-1280)*0x4000)|(3ull<<53)|0xf47;
  assert(tables[i]==v);
 }
 assert(!mg_tables(tables,0x840000001ull,40)&&!mg_tables(tables,0x840000000ull,32));
 puts("PASS static GPII0 decode, all eight EE addresses, exact vendor TRE vectors, ring wrap/full/index bounds, five-page SMMU tables and unmapped guards");
}
'''

smmu_model=r'''
static uint32_t regs[0x100000/4];static void *allocation;static unsigned write_count,drop_at;
static bool noncontiguous,ats_enabled,ats_wrong,tlb_stuck;static uint64_t alloc_pa=0x840000000ull;
static uintptr_t ml_io_map(uintptr_t pa,unsigned size){assert(pa==0x15000000&&size==0x100000);return (uintptr_t)regs;}
static int kmem_alloc_contig(unsigned map,uintptr_t *va,unsigned size,unsigned mask,unsigned a,unsigned b,unsigned c,unsigned d){
 (void)map;(void)a;(void)b;(void)c;(void)d;assert(size==0x18000&&mask==16383);allocation=aligned_alloc(16384,size);assert(allocation);memset(allocation,0,size);*va=(uintptr_t)allocation;return 0;}
static uint64_t pmap_find_phys(unsigned map,uintptr_t va){(void)map;unsigned off=va-(uintptr_t)allocation;assert(off<0x18000);return (alloc_pa+off+(noncontiguous&&off?16384:0))>>14;}
static void clean_dcache64(uint64_t pa,unsigned n,bool physical){assert(physical&&pa==alloc_pa&&n==12288);}
static void model_write(unsigned off,uint32_t value);
static void model_write64(unsigned off,uint64_t value);
'''
smmu_body=body('marble_gpi_smmu.c')
smmu_body=replace_body(smmu_body,'ms_write','model_write(off,v);')
smmu_body=replace_body(smmu_body,'ms_write64','model_write64(off,v);')
smmu_tests=r'''
static void model_write(unsigned off,uint32_t value){
 /* No global CR0, global TLBI, unrelated stream or context writes. */
 assert((off>=ms_context&&off<ms_context+0x900)||off==ms_gr1+ms_cb*4||off==ms_gr1+0x800+ms_cb*4||off==0xc14||off==0x814||off==0xc00||off==0x800);
 if(++write_count==drop_at && regs[off/4]!=value)return;
 if(off==0xc00 && (value&(1u<<10)))assert(regs[0x800/4]==0x5b6); /* no transient SID0 publication in EXID mode */
 regs[off/4]=value;
 if(off==ms_context+0x58)regs[off/4]=0; /* W1C */
 if(off==ms_context+0x7f0)regs[(ms_context+0x7f4)/4]=tlb_stuck;
}
static void model_write64(unsigned off,uint64_t value){
 assert(off>=ms_context&&off<ms_context+0x900);
 if(++write_count==drop_at && *(uint64_t *)&regs[off/4]!=value)return;
 *(uint64_t *)&regs[off/4]=value;
 if(off==ms_context+0x800){
  unsigned i=(unsigned)(value-0x100000)/4096;
  *(uint64_t *)&regs[(ms_context+0x50)/4]=i<5?(alloc_pa+0x4000*(i+1)):1;
  if(ats_wrong) *(uint64_t *)&regs[(ms_context+0x50)/4]=1;
 }
}
static void init(void){
 free(allocation);allocation=0;memset(regs,0,sizeof(regs));reason=stage=waited=snapshots=write_count=drop_at=0;noncontiguous=ats_wrong=tlb_stuck=false;
 ms_owned=ms_attempted=false;ms_base=0;ms_context=0;ms_cb=ms_asid=0;
 regs[0x20/4]=(1u<<30)|(1u<<27)|(ats_enabled?0:1u<<26)|120;
 regs[0x24/4]=0x6004004e;regs[0x28/4]=(1u<<12)|(2u<<8)|(2u<<4); /* 4K/40bit */
 for(unsigned i=0;i<120;i++)regs[(0xc00+i*4)/4]=2u<<16;
 regs[0x814/4]=(1u<<31)|0x5b6;regs[0xc14/4]=6;regs[0x86000/4]=1;
 *(uint64_t *)&regs[(0x86000+0x20)/4]=0x9000000001234000ull;
 regs[0x804/4]=1u<<31;regs[0xc04/4]=1;regs[0x81000/4]=1;
}
int main(void){
 struct mg_memory memory;
 init();assert(!marble_gpi_dma_init(&memory)&&ms_cb==4&&ms_owned);assert(regs[0xc14/4]==4&&regs[0x86000/4]==1&&regs[0xc04/4]==1&&regs[0]==0);assert(!marble_gpi_dma_fault());
 init();regs[0x814/4]=0;regs[0xc14/4]=2u<<16;assert(!marble_gpi_dma_init(&memory)&&regs[0x800/4]==((1u<<31)|0x5b6)&&regs[0xc00/4]==4);
 init();regs[0x814/4]|=1u<<16;assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_SMMU_OWNERSHIP&&!write_count);
 init();regs[0x818/4]=regs[0x814/4];regs[0xc18/4]=6;assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_SMMU_OWNERSHIP&&!write_count);
 init();for(unsigned i=4;i<78;i++)regs[(0x80000+i*0x1000)/4]=1;assert(marble_gpi_dma_init(&memory)&&!write_count);
 init();regs[0x28/4]&=~(1u<<12);assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_SMMU_CAPS&&!write_count);
 init();noncontiguous=true;assert(marble_gpi_dma_init(&memory)&&reason==MH_DMA_PHYS&&!write_count);
 init();drop_at=2;assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_SMMU_READBACK);
 init();tlb_stuck=true;assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_TLBI&&waited==10000);
 init();regs[0]=8;regs[0x20/4]|=256;regs[0x814/4]=0x5b6;regs[0xc14/4]=6|(1u<<10);assert(!marble_gpi_dma_init(&memory)&&regs[0xc14/4]==(4|(1u<<10)));
 init();regs[0]=8;regs[0x20/4]|=256;regs[0x814/4]=0;regs[0xc14/4]=2u<<16;assert(!marble_gpi_dma_init(&memory)&&regs[0xc00/4]==(4|(1u<<10)));
 ats_enabled=true;init();assert(!marble_gpi_dma_init(&memory));
 init();ats_wrong=true;assert(marble_gpi_dma_init(&memory)&&reason==MH_GPI_SMMU_READBACK);
 ats_enabled=false;init();assert(!marble_gpi_dma_init(&memory));regs[(ms_context+0x58)/4]=2;assert(marble_gpi_dma_fault()&&reason==MH_GPI_SMMU_FAULT);
 free(allocation);puts("PASS actual SMMU initialization: translated SID lease, free bank/ASID, no unrelated writes, wildcard/duplicate/busy/refusal, contiguous backing, readbacks, ATS+guard and translation fault");
}
'''

gpi_model=r'''
static uint32_t regs[0x60000/4],se_regs[0x4000/4];static void *allocation;
static unsigned fault,commands,doorbells,producer,tx_consumer,rx_consumer;static bool dma_fault;
static uintptr_t ml_io_map(uintptr_t pa,unsigned size){assert(pa==MG_RESOURCE&&size==MG_RESOURCE_SIZE);return (uintptr_t)regs;}
static void clean_dcache64(uint64_t pa,unsigned n,bool physical){assert(physical&&pa>=0x840000000ull&&pa+n<=0x840018000ull);}
static void flush_dcache64(uint64_t pa,unsigned n,bool physical){clean_dcache64(pa,n,physical);}
int marble_gpi_dma_init(struct mg_memory *memory){allocation=aligned_alloc(16384,0x18000);assert(allocation);memset(allocation,0,0x18000);memory->va=(uintptr_t)allocation;memory->pa=0x840000000ull;return 0;}
bool marble_gpi_dma_fault(void){return dma_fault;}
void marble_gpi_dma_snapshot(void){}
static void model_write(unsigned vendor,uint32_t value);
'''
gpi_body=body('marble_gpi.c')
gpi_body=replace_body(gpi_body,'mg_wr','model_write(vendor,v);')
gpi_tests=r'''
static uint32_t get(unsigned vendor){return regs[mg_offset(vendor)/4];}
static void put(unsigned vendor,uint32_t v){regs[mg_offset(vendor)/4]=v;}
static void completion(unsigned ch,unsigned index,unsigned length){
 struct mg_tre *ev=(struct mg_tre *)((uintptr_t)allocation+0xc000);
 ev[producer]=(struct mg_tre){{MG_IOVA+ch*4096+index*16,0,(2u<<24)|length,(ch<<24)|(0x22u<<16)}};
 if(fault==3)ev[producer].d[2]=16u<<24;
 if(fault==4)ev[producer].d[0]=MG_IOVA+0x70000;
 producer=(producer+1)&255;put(MC_EV+0x10,MG_IOVA+8192+producer*16);put(0x230b0,1);
}
static void transfer(void){
 unsigned wp=mg_index(get(MC_CH(0)+0x18),MG_IOVA,64);if(wp==tx_consumer)return;
 struct mg_tre *tx=(struct mg_tre *)((uintptr_t)allocation+0x4000),*rx=(struct mg_tre *)((uintptr_t)allocation+0x8000);
 struct mg_tre cfg=tx[tx_consumer],go=tx[(tx_consumer+1)&63],out=tx[(tx_consumer+2)&63];
 unsigned n=out.d[2];bool receive=go.d[0]==3;
 assert(((cfg.d[3]>>16)&255)==0x22&&cfg.d[2]==2&&go.d[3]==(receive?0x200801:0x200001));
 assert(out.d[0]==0x103000&&out.d[1]==0&&out.d[3]==0x100200&&n<=1032);
 if(receive){unsigned rw=mg_index(get(MC_CH(1)+0x18),MG_IOVA+4096,64);if(rw==rx_consumer)return;
  assert(rx[rx_consumer].d[0]==0x104000&&rx[rx_consumer].d[2]==n&&rx[rx_consumer].d[3]==0x100000);
  uint8_t *a=(uint8_t *)allocation+0x10000,*b=(uint8_t *)allocation+0x14000;
  if(cfg.d[0]&0x100)memcpy(b,a,n);else{memset(b,0,n);if(n>=8)memset(b+8,0xaa,n-8);}
 }
 if(fault==2)return; /* DMA never completes */
 completion(0,(wp+63)&63,n);tx_consumer=wp;put(MC_CH(0)+0x10,MG_IOVA+wp*16);
 if(receive){unsigned rw=mg_index(get(MC_CH(1)+0x18),MG_IOVA+4096,64);completion(1,(rw+63)&63,n);rx_consumer=rw;put(MC_CH(1)+0x10,MG_IOVA+4096+rw*16);}
}
static void model_write(unsigned off,uint32_t value){
 /* No writes to GPII1..11; only GPII0 context/control window. */
 assert(off>=0x20000&&off<=0x23404);
 if(off==MC_CH_CLEAR){put(MC_CH_IRQ,get(MC_CH_IRQ)&~value);return;}
 if(off==MC_EV_CLEAR){put(MC_EV_IRQ,get(MC_EV_IRQ)&~value);return;}
 if(off==MC_IEOB_CLEAR){put(0x230b0,get(0x230b0)&~value);return;}
 if(off==MC_CH_CMD||off==MC_EV_CMD){commands++;unsigned ch=value&255,opcode=value>>24;bool event=off==MC_EV_CMD;unsigned base=event?MC_EV:MC_CH(ch);unsigned state=opcode==1?2:opcode==2?3:1;
  if(fault==1)return;put(base,(get(base)&~0xf00000u)|(state<<20));put(event?MC_EV_IRQ:MC_CH_IRQ,event?1:1u<<ch);return;}
 if(off==MC_CH(0)||off==MC_CH(1)||off==MC_EV){value|=get(off)&0xf00000u;}
 put(off,value);
 for(unsigned ch=0;ch<2;ch++)if(off==MC_CH(ch)+8){put(MC_CH(ch)+0x10,value);put(MC_CH(ch)+0x18,value);}
 if(off==MC_EV+8)put(MC_EV+0x10,value);
 if(off==MC_CH_DB(0)||off==MC_CH_DB(1)){unsigned ch=off==MC_CH_DB(1);doorbells++;put(MC_CH(ch)+0x18,value);transfer();}
}
static void init(void){free(allocation);allocation=0;memset(&mg,0,sizeof(mg));memset(regs,0,sizeof(regs));memset(se_regs,0,sizeof(se_regs));se_regs[0x48/4]=0x21;reason=stage=waited=snapshots=fault=commands=doorbells=producer=tx_consumer=rx_consumer=0;dma_fault=false;}
int main(void){
 uint8_t tx[1032]={0xf1,0,1,0,0x14,255,255,255},rx[1032];
 init();assert(!marble_gpi_spi_init((uintptr_t)se_regs,0,2));assert(doorbells==2&&commands==5&&mg.ready&&!mg.loopback); /* internal loopback */
 for(unsigned i=0;i<200;i++){unsigned n=8+i%1025;assert(!marble_gpi_spi_xfer(tx,rx,n,true));for(unsigned b=8;b<n;b++)assert(rx[b]==0xaa);}
 assert(!marble_gpi_spi_xfer(tx,rx,1032,true));for(unsigned b=8;b<1032;b++)assert(rx[b]==0xaa);
 tx[0]=0xf0;assert(!marble_gpi_spi_xfer(tx,0,13,false));assert(mg_available(mg.rp[0],mg.wp[0],64)==63);
 assert(marble_gpi_spi_xfer(tx,0,1033,false));
 for(unsigned f=2;f<=4;f++){init();assert(!marble_gpi_spi_init((uintptr_t)se_regs,0,2));fault=f;assert(marble_gpi_spi_xfer(tx,rx,16,true)&&reason&&mg.failed&&snapshots);}
 init();fault=1;assert(marble_gpi_spi_init((uintptr_t)se_regs,0,2)&&reason==MH_GPI_COMMAND_TIMEOUT&&!doorbells&&waited==500000);
 init();put(MC_CH(0)+0x4000,2u<<20);assert(marble_gpi_spi_init((uintptr_t)se_regs,0,2)&&reason==MH_GPI_OWNERSHIP&&!commands&&!doorbells);
 free(allocation);puts("PASS actual GPI init/loopback, command order and timeout, TX-only/full-duplex transfers through1032bytes, 200 transfers exercising wrap, exact event validation, no unrelated GPII writes, refusal before unsafe doorbells");
}
'''

touch=(root/'bsd/dev/marble_touch.c').read_text()
goodix_model=r'''
#define MT_MAX 1024u
static uint8_t mt_tx[1032],mt_rx[1032];static unsigned mt_event=0x10308,mode,transactions;
static uint8_t mt_confirm_tx[13],mt_confirm_raw[8];
static void mt_wait(unsigned ms){assert(ms==5);}
static bool mt_stop(const char *gate){(void)gate;return false;}
static bool mt_exchange(unsigned n){
 transactions++;
 if(mt_tx[0]==0xf0){const uint8_t exact[]={0xf0,0,1,0,0,0xaa,0xaa,0xaa,0xaa,0xaa,0xaa,0xaa,0xaa};assert(mode==1&&n==13&&!memcmp(mt_tx,exact,13));return true;}
 const uint8_t prefix[]={0xf1,0,1,0,0x14,255,255,255};
 if(mode==0)assert(n==12&&!memcmp(mt_tx,prefix,8));
 else {assert(n==16&&mt_tx[0]==0xf1&&mt_tx[4]==0&&mt_tx[5]==255&&mt_tx[6]==255&&mt_tx[7]==255);}
 memset(mt_rx,0x55,sizeof(mt_rx));for(unsigned i=8;i<n;i++)mt_rx[i]=mode==1?0xaa:(uint8_t)(0x80+i-8);return true;
}
'''
goodix_body='\n'.join(touch_test.function(touch,n) for n in ['mt_read','mt_confirm'])
goodix_tests=r'''
int main(void){uint8_t out[4];assert(mt_read(0x10014,out,4)&&transactions==1);const uint8_t expected[]={0x80,0x81,0x82,0x83};assert(!memcmp(out,expected,4));mode=1;transactions=0;assert(mt_confirm()&&transactions==2);for(unsigned i=0;i<8;i++)assert(mt_confirm_raw[i]==0xaa);puts("PASS actual Berlin-D read F1/BE32/three dummy bytes/RX offset8 and exact F0/0x10000/8xAA confirm, single transfer framing");}
'''

with tempfile.TemporaryDirectory(prefix='marble-gpi-test-') as directory:
    for name,code in [('pure',pure),('smmu',smmu_model+smmu_body+smmu_tests),('gpi',gpi_model+gpi_body+gpi_tests),('goodix',goodix_model+goodix_body+goodix_tests)]:
        p=Path(directory)/name
        p.with_suffix('.c').write_text(common.replace('static unsigned reason',diag+'\nstatic unsigned reason')+header+code)
        subprocess.run(['clang','-std=gnu11','-O1','-g','-fsanitize=address,undefined',str(p.with_suffix('.c')),'-o',str(p)],check=True)
        subprocess.run([str(p)],check=True)
