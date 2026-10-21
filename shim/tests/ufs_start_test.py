"""Exercise actual device ACTIVE / LU0 readiness control flow with mocked SCSI completions."""
from pathlib import Path
import subprocess
import tempfile
s = (Path(__file__).resolve().parents[1] / 'ufs.c').read_text()
code = s[s.index('static int lun0_initializing'):s.index('\n#endif\n\nstatic uint32_t read_blocks')]
code = code.replace('__asm__ volatile("mrs %0, cntfrq_el0" : "=r"(freq));', 'freq = 100;')
header = str(Path(__file__).resolve().parents[1] / 'ufs_response.h')
prefix = r'''
#include <assert.h>
#include <string.h>
#include <stdint.h>
#include "HEADER"
static unsigned mode, calls, starts, polls;
static uint64_t clock_ticks;
static uint64_t ticks(void) { return clock_ticks++; }
static void con_str(const char *a,const char *b) {(void)a;(void)b;}
static void con_hex2(const char *a,const char *b,uint32_t c,const char *d,uint32_t e)
{(void)a;(void)b;(void)c;(void)d;(void)e;}
static void show_response(const struct ufs_response *d) {(void)d;}
static uint32_t scsi(uint8_t lun,const uint8_t *cdb,unsigned n,void *buf,uint32_t len,
 uint32_t *ocs,uint32_t *st,struct ufs_response *d) {
 assert(n==6 && !buf && !len); calls++;
 memset(d,0,sizeof(*d)); *ocs=0; *st=2;
 d->valid=d->has_key=d->has_asc=1; d->key=2; d->asc=4; d->ascq=2;
 if(cdb[0]==0x1b) {
  const uint8_t expected[]={0x1b,0,0,0,0x10,0};
  assert(lun==0xd0 && !memcmp(cdb,expected,6)); assert(++starts==1 && calls==2);
  if(mode==3) return 4;
  *st=0; return 0;
 }
 assert(lun==0 && cdb[0]==0);
 if(mode==0 || (mode==1 && starts && polls==3)) { *st=0; return 0; }
 if(mode==2) d->ascq=3;
 if(mode==4) *ocs=1;
 if(mode==5) d->valid=0;
 if(mode==7 && starts) d->ascq=1;
 return 4;
}
static uint32_t scsi_timed(uint8_t lun,const uint8_t *cdb,unsigned n,void *buf,uint32_t len,
 uint32_t *ocs,uint32_t *st,struct ufs_response *d,uint64_t begin,uint64_t budget) {
 assert(ticks()-begin<budget); polls++;
 return scsi(lun,cdb,n,buf,len,ocs,st,d);
}
'''.replace('HEADER', header)
suffix = r'''
int main(void) {
 for(mode=0;mode<8;mode++) {
  calls=starts=polls=0; clock_ticks=0;
  int ready=lun0_ready();
  assert(ready==(mode==0 || mode==1));
  assert(starts==((mode==1 || mode==3 || mode==6 || mode==7)?1:0));
  if(mode==3) assert(!polls);
  if(mode==6) {assert(polls==50); assert(clock_ticks>=500 && clock_ticks<550);}
  if(mode==7) assert(polls==1);
 }
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'test.c'; c.write_text(prefix+code+suffix)
    exe=Path(tmp)/'test'
    subprocess.run(['cc','-fsanitize=undefined','-g',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('DEVACT gate, exact CDB/LUN, single issue, CHECK CONDITION stop, polling/timeout passed')

# Check every current SCSI call site and CDB initializer: read-only opcode allowlist.
import re
assert 'scsi(0xd0, devact,' in s
assert len(re.findall(r'scsi\(0xd0,', s)) == 1
for line in s.splitlines():
    if re.search(r'\b(?:rc = |return )scsi(?:_timed)?\(', line):
        assert re.search(r'scsi(?:_timed)?\((?:0|0xd0|lun),', line), line
for name in ('cap10', 'rd10', 'cdb'):
    assert f'scsi(0, {name},' in s
initializers = re.findall(r'uint8_t \w+\[\d+\] = \{ (0x[0-9a-fA-F]+)', s)
assert set(map(lambda v: int(v, 16), initializers)) == {0, 0x1b, 0x25, 0x28}
assert 'start_lun0' not in s
print('All SCSI call-site LUNs and opcode allowlist passed')
assert 'ucd.cmd[2] = lun;' in s
assert 'ucd.cmd[1] = len ? 0x40 : 0x00;' in s
assert 'zero(&ucd, sizeof(ucd));' in s
assert 'if (len) {' in s
assert s.index('if (!ufs_complete_dev_init())') < s.index('if (!lun0_ready())')
