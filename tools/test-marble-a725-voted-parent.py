#!/usr/bin/env python3
"""Actual mode7 C: voted vs manual PLL semantics, MMIO ownership, cleanup."""
import ast
from pathlib import Path
import subprocess
import sys
import tempfile
s=(Path(sys.argv[1])/'bsd/dev/marble_a725_probe.c').read_text()
# Reuse the existing root model, without importing/executing its test script.
tree=ast.parse(Path(__file__).with_name('test-marble-a725-roots.py').read_text())
parts={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
       if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
       and n.targets[0].id in ('prefix','mock')}
constants=s[s.index('#define A725_BUILD_ID'):s.index('struct a725_firmware_spec')]
sampler=s[s.index('struct a725_pll_sample {'):s.index('/* Same strict prerequisites')]
roots=s[s.index('static boolean_t\na725_root_parent_acquire'):s.index('static boolean_t\na725_enable_gmu_clocks')]
voted=s[s.index('static boolean_t\na725_voted_pll_ready'):s.index('static boolean_t\na725_root_stage_test(')]
mock=parts['mock'].replace('static unsigned writes, elapsed, updates;', 'static unsigned writes, elapsed, updates;\nstatic bool lose_on_gate;static unsigned lose_on_update;')
mock=mock.replace('if(!ignore_vote){gcc[off/4]=v;}', 'if(!ignore_vote){gcc[off/4]=v;}\n  if(lose_on_gate)gcc[A725_GPLL0_MODE/4]&=~(1u<<31);')
mock=mock.replace('updates++;if(updates!=fail_update)', 'updates++;if(updates==lose_on_update)gcc[A725_GPLL0_MODE/4]&=~(1u<<31);if(updates!=fail_update)')
stubs=r'''
static unsigned votes,rollbacks;static bool bad_after_cx;
static const char *a725_result_name(enum a725_rpmh_result r){(void)r;return "model";}
static int marble_rpmh_arc_vote(const char *n,bool on,uint32_t *h,uint16_t *v){
 (void)n;(void)on;*h=1;*v=1;votes++;return 0;
}
static int a725_aop_acd_enable(const struct marble_a725_resources *r){(void)r;return 0;}
static int a725_cx_enable_test(const struct marble_a725_resources *r,struct a725_power_results *q){
 (void)r;q->cx_touched=true;if(bad_after_cx)gcc[A725_GPLL0_L/4]=0x444400ff;return 0;
}
static void a725_cx_rollback(const struct marble_a725_resources *r,struct a725_power_results *q){
 (void)r;rollbacks++;q->cx_rollback=A725_ACKNOWLEDGED;
}
'''
main=r'''
static void setup(void){
 init();votes=rollbacks=0;bad_after_cx=lose_on_gate=false;lose_on_update=0;
 gcc[A725_GPLL0_MODE/4]=0x80000005;
 gcc[A725_GPLL0_OPMODE/4]=0;gcc[A725_GPLL0_L/4]=0x4444001f;
 gcc[A725_GPLL0_USER/4]=0x02000403;gcc[A725_GPLL0_VOTE/4]=1;
}
int main(void){
 struct marble_a725_resources r={.gcc=1,.gpucc=2};
 struct a725_power_results q;struct a725_pll_sample pre;
 // Physical 0106 state: old manual check refuses; isolated voted rule accepts.
 setup();memset(&q,0,sizeof(q));assert(!a725_root_parent_acquire(&r,&q)&&writes==0);
 memset(&q,0,sizeof(q));assert(a725_voted_parent_acquire(&r,&q));
 a725_root_cleanup(&r,&q);assert(q.root_cleanup==A725_ACKNOWLEDGED);
 assert(gcc[A725_GPLL0_VOTE/4]==1&&gcc[A725_GPLL0_OPMODE/4]==0);
 // All qualification failures must occur before any consumer gate write.
 for(unsigned bad=0;bad<9;bad++){
  setup();memset(&q,0,sizeof(q));
  if(bad==0)gcc[A725_GPLL0_MODE/4]&=~(1u<<31);
  if(bad==1)gcc[A725_GPLL0_USER/4]&=~(1u<<25);
  if(bad==2)gcc[A725_GPLL0_VOTE/4]=0;
  if(bad==3)gcc[A725_GPLL0_MODE/4]&=~1u;
  if(bad==4)gcc[A725_GPLL0_MODE/4]&=~4u;
  if(bad==5)gcc[A725_GPLL0_L/4]=0x444400ff;
  if(bad==6)gcc[A725_GPLL0_ALPHA/4]++;
  if(bad==7)gcc[A725_GPLL0_USER/4]&=~(1u<<10);
  if(bad==8)gcc[A725_GPLL0_OPMODE/4]=2;
  assert(!a725_voted_root_stage_test(&r,&q,&pre));
  assert(writes==0&&votes==0&&rollbacks==0&&elapsed<=100);
 }
 // Successful roots and reverse cleanup, inherited consumer gate preserved.
 for(unsigned inherited=0;inherited<2;inherited++){
  setup();memset(&q,0,sizeof(q));gcc[A725_GPU_GPLL0_VOTES/4]|=inherited*A725_GPU_GPLL0_DIV;
  assert(a725_voted_root_stage_test(&r,&q,&pre));
  assert(votes==4&&rollbacks==1&&updates==6);
  assert(gcc[A725_GPU_GPLL0_VOTES/4]==((1u<<15)|inherited*A725_GPU_GPLL0_DIV));
  for(unsigned i=0;i<3;i++)assert(cc[a725_roots[i].cmd/4]==0&&cc[(a725_roots[i].cmd+4)/4]==0);
 }
 // A previously observed post-CX L=ff must still refuse, with no clock writes.
 setup();memset(&q,0,sizeof(q));bad_after_cx=true;
 assert(!a725_voted_root_stage_test(&r,&q,&pre));
 assert(writes==0&&votes==4&&rollbacks==1);
 // Lock loss after gate acquisition quarantines gate and rails.
 setup();memset(&q,0,sizeof(q));lose_on_gate=true;
 assert(!a725_voted_root_stage_test(&r,&q,&pre));
 assert(q.root_uncertain&&votes==2&&rollbacks==0);
 assert(gcc[A725_GPU_GPLL0_VOTES/4]&A725_GPU_GPLL0_DIV);
 for(unsigned loss=1;loss<=3;loss++){
  setup();memset(&q,0,sizeof(q));lose_on_update=loss;
  assert(!a725_voted_root_stage_test(&r,&q,&pre));
  assert(q.root_uncertain&&votes==2&&rollbacks==0&&updates==loss);
 }
 // Every forward and reverse RCG update timeout retains resources, no retry.
 for(unsigned failure=1;failure<=6;failure++){
  setup();memset(&q,0,sizeof(q));fail_update=failure;
  assert(!a725_voted_root_stage_test(&r,&q,&pre));
  assert(q.root_uncertain&&votes==2&&rollbacks==0);
  assert(gcc[A725_GPU_GPLL0_VOTES/4]&A725_GPU_GPLL0_DIV);
 }
 puts("PASS voted parent: OPMODE0 FSM policy, strict failures, post-CX refusal, inherited-vote preservation, root restore, lock-loss/timeout quarantine");
}
'''
with tempfile.TemporaryDirectory(prefix='a725-voted-parent-') as directory:
 p=Path(directory);(p/'test.c').write_text(parts['prefix']+constants+mock+sampler+roots+stubs+voted+main)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-const-variable',str(p/'test.c'),'-o',str(p/'test')],check=True)
 result=subprocess.run([str(p/'test')],check=True,capture_output=True,text=True)
 print(result.stdout.splitlines()[-1])
