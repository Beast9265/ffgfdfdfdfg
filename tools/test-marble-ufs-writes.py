#!/usr/bin/env python3
"""Host-check actual replayed MARBLE write guards, CDB/UPIU and partial-block RMW.
Usage: test-marble-ufs-writes.py PATH/TO/REPLAYED/xnu
Hardware completion and durability still require a physical test.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / 'bsd/dev/sweet_ufs.c').read_text()

def function(name):
    start = source.index('\n' + name + '(') + 1
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

# Source-level lifecycle checks complement the executable transport tests.
init = function('sweet_ufs_init')
assert init.index('ufs_find_partition(want)') < init.index('su.writable = (rw == 1)')
assert 'if (error) {\n\t\treturn error;' in init
assert 'uint32_t rw = 0;' in init and 'PE_parse_boot_argn("ufsrw", &rw, sizeof(rw));' in init
assert 'rw == 1 && strcmp(want, "userdata") != 0' in init
assert source.count('su.writable =') == 2  # mutually exclusive MARBLE/SWEET branches
assert 'su.first_block = first;' in function('ufs_find_partition')
assert 'su.nblocks = last - first + 1;' in function('ufs_find_partition')
assert 'ufs_gpt_crc(b, nent * esz) != entries_crc' in function('ufs_find_partition')
assert 'ufs_gpt_crc(b, header_size) != header_crc' in function('ufs_find_partition')
print('PASS lifecycle: zero-initialized writable, exact MARBLE ufsrw=1, userdata-only, GPT CRCs/bounds before enable')

# Exercise the actual submission guard and descriptor construction, stopping
# before cache maintenance / hardware. No storage access in this harness.
scsi = function('ufs_scsi')
scsi = scsi[:scsi.index('\n\tif (su.cache)')] + '\n submissions++; return 0;\n}'
header = r'''
#include <assert.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <errno.h>
#define ARM64_BOARD_CONFIG_MARBLE 1
#define UFS_LOG "MARBLE UFS: "
#define MIN(a,b) ((a)<(b)?(a):(b))
#define B_READ 1
#define REG_UTRLBA 0x50
#define REG_UTRLBAU 0x54
#define REG_UTRLDBR 0x58
#define REG_UTRLRSR 0x60
'''
layout = source[source.index('#define UFS_BLOCK '):source.index('#define CMD_TIMEOUT_NS')]
layout += source[source.index('struct utrd {'):source.index('#ifdef ARM64_BOARD_CONFIG_MARBLE\n_Static_assert')]
stubs = r'''
struct { uintptr_t dma; uint64_t dma_pa, first_block, nblocks;
 uint32_t secsize; uint8_t lun, tag; bool writable, ready, failed, activate_allowed;
} su;
static unsigned submissions, reads;
static int sweet_ufs_lock;
static void lck_mtx_lock(int *p) {(void)p;}
static void lck_mtx_unlock(int *p) {(void)p;}
static uint32_t ufs_rd(unsigned r) {
 if(r==REG_UTRLBA) return (uint32_t)su.dma_pa;
 if(r==REG_UTRLBAU) return su.dma_pa>>32;
 return r==REG_UTRLRSR;
}
struct buffer { int64_t block; uint32_t count, flags, resid; int error; char *bytes; bool done; };
typedef struct buffer *buf_t;
typedef char *caddr_t;
static int64_t buf_blkno(buf_t b) {return b->block;}
static uint32_t buf_count(buf_t b) {return b->count;}
static uint32_t buf_flags(buf_t b) {return b->flags;}
static void buf_setresid(buf_t b, uint32_t n) {b->resid=n;}
static int buf_map(buf_t b, caddr_t *p) {*p=b->bytes;return 0;}
static void buf_unmap(buf_t b) {(void)b;}
static void buf_seterror(buf_t b,int e) {b->error=e;}
static void buf_biodone(buf_t b) {b->done=true;}
static int ufs_read_blocks(uint64_t lba, uint32_t count) {
 assert(lba>=su.first_block && count<=su.nblocks-(lba-su.first_block));
 memset((void *)(su.dma+DMA_BOUNCE),0x55,count*UFS_BLOCK);reads++;return 0;
}
'''
main = r'''
int main(void) {
 assert(!su.writable);
 su.dma=(uintptr_t)calloc(1,DMA_SIZE);assert(su.dma);su.dma_pa=0x843f44000;
 su.secsize=512;su.first_block=0x2f6a00;su.nblocks=1000;
 assert(ufs_write_blocks(su.first_block,1)==EPERM);
 assert(ufs_sync_cache()==EROFS);assert(submissions==0);
 su.writable=true;su.nblocks=0;
 assert(ufs_write_blocks(su.first_block,1)==EPERM);assert(ufs_sync_cache()==EROFS);
 su.nblocks=1000;
 assert(ufs_write_blocks(su.first_block-1,1)==EPERM);
 assert(ufs_write_blocks(su.first_block,0)==EPERM);
 assert(ufs_write_blocks(su.first_block,257)==EPERM);
 assert(ufs_write_blocks(su.first_block+999,2)==EPERM);
 assert(ufs_write_blocks(UINT64_MAX,2)==EPERM);
 assert(submissions==0);
 assert(!ufs_write_blocks(su.first_block,2));
 struct utrd *d=(void *)su.dma;struct ucd *c=(void *)(su.dma+DMA_UCD);
 assert(c->cmd[1]==0x20 && ((d->dw0>>25)&3)==1);
 uint8_t expected[10]={0x2a,0,0,0x2f,0x6a,0,0,0,2,0};
 assert(!memcmp(c->cmd+16,expected,10));
 assert(!ufs_sync_cache());assert(c->cmd[16]==0x35 && c->cmd[1]==0 && !d->prdt);
 uint8_t bad[10]={0x2a};assert(ufs_scsi(bad,10,4096,true)==EROFS);
 bad[0]=0x3b;assert(ufs_scsi(bad,10,4096,true)==EROFS);
 bad[0]=0x28;assert(ufs_scsi(bad,10,4096,true)==EROFS);
 bad[0]=0x35;assert(ufs_scsi(bad,10,4096,false)==EROFS);
 unsigned before=submissions;
 su.first_block=UINT32_MAX;su.nblocks=2;
 assert(ufs_write_blocks(UINT32_MAX,2)==EPERM);assert(submissions==before);
 su.first_block=0x2f6a00;su.nblocks=1000;
 char data[8192];memset(data,0xaa,sizeof(data));
 struct buffer b={.block=1,.count=512,.bytes=data};
 sweet_ufs_strategy(&b);assert(b.done && !b.error && !b.resid && reads==1);
 uint8_t *bounce=(void *)(su.dma+DMA_BOUNCE);
 for(unsigned i=0;i<4096;i++) assert(bounce[i]==(i>=512 && i<1024?0xaa:0x55));
 b=(struct buffer){.count=8192,.bytes=data};sweet_ufs_strategy(&b);
 assert(!b.error && reads==1); // aligned full blocks skip preread
 b=(struct buffer){.block=-1,.count=512,.bytes=data};sweet_ufs_strategy(&b);assert(b.error==EINVAL);
 b=(struct buffer){.block=7999,.count=1024,.bytes=data};sweet_ufs_strategy(&b);assert(b.error==EINVAL);
 su.writable=false;before=submissions;
 b=(struct buffer){.count=512,.bytes=data};sweet_ufs_strategy(&b);assert(b.error==EROFS);
 assert(submissions==before);free((void *)su.dma);
 puts("PASS default RO, partition guard, WRITE10 CDB/host-to-device UPIU, payload-free sync, partial 4K RMW, aligned write, BSD bounds");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp) / 'test.c'
    exe = Path(tmp) / 'test'
    c.write_text(header + layout + stubs + 'static int\n' + scsi +
                 '\nstatic int\n' + function('ufs_write_blocks') +
                 '\nstatic int\n' + function('ufs_sync_cache') +
                 '\nstatic void\n' + function('sweet_ufs_strategy') + main)
    subprocess.run(['clang', '-Wall', '-Wextra', '-Werror', '-Wno-format',
                    '-fsanitize=address,undefined', str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
