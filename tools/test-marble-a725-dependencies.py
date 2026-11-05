#!/usr/bin/env python3
"""Compile actual mode8 C against fault-injected root/branch MMIO."""
import ast, subprocess, sys, tempfile
from pathlib import Path
s=(Path(sys.argv[1])/'bsd/dev/marble_a725_probe.c').read_text()
def literals(file,names):
 t=ast.parse(Path(__file__).with_name(file).read_text())
 return {n.targets[0].id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names}
r=literals('test-marble-a725-roots.py',['prefix','mock'])
v=literals('test-marble-a725-voted-parent.py',['stubs'])
mock=r['mock'].replace('0x63000/4','0x82000/4')
mock=mock.replace('static unsigned writes, elapsed, updates;','static unsigned writes, elapsed, updates;\nstatic int branch_fail, restore_fail;static unsigned branches;')
mock=mock.replace('writes++;assert(!(off&3));', '''writes++;assert(!(off&3));
 for(unsigned i=0;i<A725_CLOCK_COUNT;i++){
  const struct a725_clock_spec *c=&a725_clocks[i];
  if(c->owner==A725_CLOCK_QDSS_OPTIONAL || base!=(c->gpucc?2u:1u) || off!=c->offset)continue;
  assert(c->owner==A725_CLOCK_REVERSIBLE);
  /* Every branch write, including unwind, must precede root restoration. */
  assert(updates==3);
  uint32_t *reg=base==1?gcc+off/4:cc+off/4;
  assert((v&~1u)==(*reg&~1u));branches++;
  if((int)i==branch_fail && (v&1))return;
  if((int)i==restore_fail && !(v&1))return;
  *reg=v;return;
 }
''')
clockhelpers=s[s.index('static vm_offset_t\na725_clock_base'):s.index('/* Read-only Cape Lucid')]
clockops=s[s.index('static boolean_t\na725_enable_gmu_clocks'):s.index('static boolean_t\na725_cx_stage_test')]
roots=s[s.index('static boolean_t\na725_root_parent_acquire'):s.index('static boolean_t\na725_enable_gmu_clocks')]
sampler=s[s.index('struct a725_pll_sample {'):s.index('/* Same strict prerequisites')]
voted=s[s.index('static boolean_t\na725_voted_pll_ready'):s.index('static boolean_t\na725_voted_root_stage_test')]
stage=s[s.index('static boolean_t\na725_dependency_stage_test'):s.index('static void\na725_show_dependency_results')]
stubs=v['stubs'].replace('static const char *a725_result_name(enum a725_rpmh_result r){(void)r;return "model";}','')
stubs=stubs.replace('static unsigned votes,rollbacks;', 'static unsigned votes,rollbacks;static bool rollback_fail;static unsigned vote_fail;')
stubs=stubs.replace('votes++;return 0;', 'votes++;return votes==vote_fail?ETIMEDOUT:0;')
stubs=stubs.replace('q->cx_rollback=A725_ACKNOWLEDGED;', 'q->cx_rollback=rollback_fail?A725_FAILED:A725_ACKNOWLEDGED;')
main=r'''
static void setup(void){
 init();votes=rollbacks=branches=vote_fail=0;branch_fail=restore_fail=-1;bad_after_cx=rollback_fail=false;
 gcc[A725_GPLL0_MODE/4]=0x80000005;gcc[A725_GPLL0_OPMODE/4]=0;
 gcc[A725_GPLL0_L/4]=0x4444001f;gcc[A725_GPLL0_USER/4]=0x02000403;gcc[A725_GPLL0_VOTE/4]=1;
 for(unsigned i=0;i<A725_CLOCK_COUNT;i++){
  const struct a725_clock_spec *c=&a725_clocks[i];if(c->owner==A725_CLOCK_QDSS_OPTIONAL)continue;
  uint32_t *reg=c->gpucc?cc+c->offset/4:gcc+c->offset/4;
  *reg=c->owner==A725_CLOCK_AON_INHERITED?1u:0x40000000u;
 }
}
int main(void){
 struct marble_a725_resources r={.gcc=1,.gpucc=2};struct a725_power_results q;struct a725_pll_sample pre;
 for(unsigned inherited=0;inherited<2;inherited++){
  setup();memset(&q,0,sizeof(q));
  if(inherited)for(unsigned i=0;i<A725_CLOCK_COUNT;i++){
   const struct a725_clock_spec *c=&a725_clocks[i];if(c->owner!=A725_CLOCK_REVERSIBLE)continue;
   *(c->gpucc?cc+c->offset/4:gcc+c->offset/4)|=1;
  }
  assert(a725_dependency_stage_test(&r,&q,&pre));assert(votes==4&&rollbacks==1&&updates==6);
  assert(branches==(inherited?0u:6u));assert(!q.root_uncertain);
  for(unsigned i=0;i<A725_CLOCK_COUNT;i++)if(a725_clocks[i].owner==A725_CLOCK_REVERSIBLE){
   const struct a725_clock_spec *c=&a725_clocks[i];
   assert(*(c->gpucc?cc+c->offset/4:gcc+c->offset/4)==(0x40000000u|inherited));
  }
 }
 // Every AON dependency refusal prevents dependent writes and parent teardown.
 for(unsigned i=0;i<A725_CLOCK_COUNT;i++)if(a725_clocks[i].owner==A725_CLOCK_AON_INHERITED){
  setup();memset(&q,0,sizeof(q));const struct a725_clock_spec *c=&a725_clocks[i];
  *(c->gpucc?cc+c->offset/4:gcc+c->offset/4)=0;
  assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&updates==3&&votes==2&&rollbacks==0);
 }
 for(int i=1;i<=4;i++)if(i!=2){
  setup();memset(&q,0,sizeof(q));branch_fail=i;
  assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&votes==2&&rollbacks==0&&updates==3);
  setup();memset(&q,0,sizeof(q));restore_fail=i;
  assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&votes==2&&rollbacks==0&&updates==3);
 }
 for(unsigned i=1;i<=6;i++){
  setup();memset(&q,0,sizeof(q));fail_update=i;
  assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&votes==2&&rollbacks==0);
  if(i<=3)assert(branches==0);
 }
 setup();memset(&q,0,sizeof(q));rollback_fail=true;
 assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&votes==2);
 for(unsigned i=1;i<=4;i++){
  setup();memset(&q,0,sizeof(q));vote_fail=i;
  assert(!a725_dependency_stage_test(&r,&q,&pre));assert(q.root_uncertain&&votes==i);
 }
 setup();memset(&q,0,sizeof(q));gcc[A725_GPLL0_L/4]++;
 assert(!a725_dependency_stage_test(&r,&q,&pre));assert(writes==0&&votes==0);
 puts("PASS mode8 real C: dependency leases, inherited branches, AON refusal, every branch/RCG timeout, failed cleanup/CX/release retention, bounded waits, write allowlist");
}
'''
code=r['prefix']+s[s.index('#define A725_BUILD_ID'):s.index('struct a725_firmware_spec')]+mock+clockhelpers+sampler+roots+clockops+stubs+voted+stage+main
with tempfile.TemporaryDirectory(prefix='a725-dependencies-') as d:
 p=Path(d);(p/'test.c').write_text(code)
 subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-const-variable',str(p/'test.c'),'-o',str(p/'test')],check=True)
 result=subprocess.run([str(p/'test')],capture_output=True,text=True)
 if result.returncode:print(result.stdout,result.stderr);raise SystemExit(result.returncode)
 print(result.stdout.splitlines()[-1])
