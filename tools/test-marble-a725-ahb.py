#!/usr/bin/env python3
"""Reuse the mode8 MMIO harness to fault-inject actual mode9 C, no phone I/O."""
from pathlib import Path
import sys
base=Path(__file__).with_name('test-marble-a725-dependencies.py').read_text()
# Retain the root/branch MMIO allowlist and existing power-service mocks.
a=base.index("main=r'''");b=base.index("\ncode=",a)
main=r'''
static int ahb_behavior;
static unsigned ahb_write_at,ahb_enable_writes;
static void setup9(void){
 setup();ahb_behavior=0;ahb_write_at=ahb_enable_writes=0;
 gcc[0x81004/4]=1;cc[A725_GPUCC_GX_GDSCR/4]=1;
 cc[A725_GPUCC_CX_HWCTRL/4]=A725_GDSC_PWR_ON;
}
int main(void){
 struct marble_a725_resources r={.gcc=1,.gpucc=2};struct a725_power_results q;
 struct a725_pll_sample pre;struct a725_ahb_audit a;
 setup9();memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
 assert(a725_ahb_stage_test(&r,&q,&pre,&a));
 assert(a.attempted&&ahb_enable_writes==1&&a.before==0&&a.after==0);
 assert(q.clocks[5]==A725_ACKNOWLEDGED&&votes==4&&updates==6&&rollbacks==1);
 for(unsigned i=0;i<5;i++)assert(a.sample[i]==1);
 // Inherited AHB bit is never toggled or withdrawn.
 setup9();cc[0x911c/4]=1;memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
 assert(a725_ahb_stage_test(&r,&q,&pre,&a));assert(!a.attempted&&ahb_enable_writes==0&&a.after==1);
 // 0108 observation (write ignored), delayed latch, self-clear and RAZ/all-ones.
 for(int failure=1;failure<=8;failure++){
  setup9();ahb_behavior=failure;memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
  assert(!a725_ahb_stage_test(&r,&q,&pre,&a));
  assert(ahb_enable_writes==1&&q.root_uncertain&&votes==2&&updates==3&&rollbacks==0);
  assert(q.clocks[5]==A725_NOT_ATTEMPTED&&q.clock_cleanup==A725_NOT_ATTEMPTED);
  assert(a.attempted&&elapsed<2000);
 }
 // Config bus refusal happens before any power or GPUCC transaction.
 setup9();gcc[0x81004/4]=0;memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
 assert(!a725_ahb_stage_test(&r,&q,&pre,&a));assert(a.refusal==1&&votes==0&&writes==0);
 // Guards: GX owner, unknown AHB control bits, missing HUB, bad divider read.
 for(unsigned bad=0;bad<4;bad++){
  setup9();memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
  if(bad==0)cc[A725_GPUCC_GX_GDSCR/4]=0;
  if(bad==1)cc[0x911c/4]=2;
  if(bad==2)cc[0x9148/4]=0;
  if(bad==3)cc[0x9430/4]=~0u;
  assert(!a725_ahb_stage_test(&r,&q,&pre,&a));
  assert(!a.attempted&&ahb_enable_writes==0&&q.root_uncertain&&votes==2&&updates==3);
 }
 // Each cleanup/root failure keeps upstream resources, no second experiment.
 for(unsigned failure=1;failure<=6;failure++){
  setup9();fail_update=failure;memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
  assert(!a725_ahb_stage_test(&r,&q,&pre,&a));assert(q.root_uncertain&&votes==2&&rollbacks==0);
 }
 setup9();restore_fail=4;memset(&q,0,sizeof(q));memset(&a,0,sizeof(a));
 assert(!a725_ahb_stage_test(&r,&q,&pre,&a));assert(q.root_uncertain&&votes==2&&rollbacks==0);
 puts("PASS mode9 actual C: single AHB write, stable/inherited latch, ignored/late/self-clear/invalid reads, CFG/GX/HUB/ownership refusals, bounded capture, rollback and retention");
}
'''
# Keep setup() from the old harness, replace only its old main.
setup=base[a:b].split('int main(void){')[0]
base=base[:a]+setup+main+"'''"+base[b:]
base=base.replace("code=r['prefix']", "extra=s[s.index('/* Cape AHB: software bit0'):s.index('static void\\na725_show_ahb_audit')]\ncode=r['prefix']")
base=base.replace('+voted+stage+main', '+voted+stage+extra+main')
# The legacy harness uses unrelated bit30 as a preservation marker; AHB
# diagnostic intentionally refuses unknown bits, so AHB reset view is zero.
base=base.replace('gcc[0x81004/4]=1;cc[A725_GPUCC_GX_GDSCR/4]=1;', 'gcc[0x81004/4]=1;cc[0x911c/4]=0;cc[A725_GPUCC_GX_GDSCR/4]=1;')
# Add readback effects after the real test's single enable write.
base=base.replace("code=r['prefix']", '''mock=mock.replace('static unsigned writes, elapsed, updates;', 'static unsigned writes, elapsed, updates;\\nstatic int ahb_behavior;static unsigned ahb_write_at,ahb_enable_writes;')
mock=mock.replace('assert(!(off&3));', 'assert(!(off&3)); if(base==2 && off==0x911c && ahb_enable_writes){ unsigned t=elapsed-ahb_write_at; if(ahb_behavior==1)return 0; if(ahb_behavior==2 && t<100)return 0; if(ahb_behavior==3 && t>=10)return 0; if(ahb_behavior==4)return ~0u; if(ahb_behavior==5)gcc[0x81004/4]=0; if(ahb_behavior==6)cc[0x9430/4]=1; if(ahb_behavior==7)cc[0x9148/4]=0; if(ahb_behavior==8)gcc[A725_GPLL0_MODE/4]&=~(1u<<31); }',1)
mock=mock.replace('*reg=v;return;', 'if(i==4 && (v&1)){ahb_enable_writes++;ahb_write_at=elapsed;} *reg=v;return;')
code=r['prefix']''')
# setup9/main refer to the same globals declared by the MMIO model.
base=base.replace('static int ahb_behavior;\nstatic unsigned ahb_write_at,ahb_enable_writes;\nstatic void setup9', 'static void setup9')
# Exec local test source in its own filename context for helper-path resolution.
exec(compile(base,str(Path(__file__).with_name('test-marble-a725-dependencies.py')),'exec'))
