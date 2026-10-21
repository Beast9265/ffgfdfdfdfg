"""Exercise actual loader validation; stop at PHYS before any destination copy."""
from pathlib import Path
import os
import subprocess
import tempfile
root = Path(__file__).resolve().parents[1]
source = (root / 'loader.c').read_text().replace(
    '__asm__ volatile("dsb sy; ic iallu; dsb sy; isb" ::: "memory");', '(void)0;')
harness = r'''
#include <assert.h>
#include <setjmp.h>
#include <string.h>
#include <stdio.h>
_Alignas(8) static unsigned char image[4096];
static uint64_t lo, hi;
static jmp_buf valid;
int fdt_chosen_u64(uintptr_t dtb, const char *prop, uint64_t *out) {
    (void)dtb; *out = !strcmp(prop,"linux,initrd-start") ? lo : hi; return 1;
}
void con_hex(const char *s,uint64_t v) {(void)s;(void)v;}
void con_str(const char *s,const char *v) {(void)s;(void)v;}
void con_hex2(const char *s,const char *a,uint32_t x,const char *b,uint32_t y) {
    (void)a;(void)b;(void)x;(void)y;
    if (!strcmp(s,"PHYS")) longjmp(valid,1);
}
static struct payload *fixture(void) {
    memset(image,0,sizeof(image));
    struct payload h = { .magic={'S','W','E','E','T','X','N','U'}, .version=1, .nsegs=1,
      .virt_base=0xfffffe0000000000ULL, .entry_va=0xfffffe0000000000ULL,
      .adt_off=0x300, .adt_size=8, .kernel_end=0xfffffe0000004000ULL,
      .phys_base=0x840000000ULL, .mem_size=0x100000000ULL };
    memcpy(image+256,&h,sizeof(h));
    struct payload_seg seg={h.virt_base,0x4000,0x2c8,8};
    memcpy(image+256+sizeof(h),&seg,sizeof(seg));
    memcpy(image+256+0x310,"MRBLXNU1",8);
    uint64_t size=0x310; memcpy(image+256+0x318,&size,8);
    lo=(uintptr_t)image; hi=lo+256+0x320;
    return (struct payload *)(image+256);
}
static void accepted(void) {
    if (!setjmp(valid)) { const char *e=loader_boot(0); fprintf(stderr,"unexpected: %s\n",e); assert(0); }
}
static void rejected(void) {
    if (!setjmp(valid)) {assert(loader_boot(0)); return;}
    assert(!"invalid payload accepted");
}
int main(void) {
    fixture(); accepted();
    /* Deliberately unaligned combined vendor length. */
    memmove(image+257,image+256,0x320); hi++; accepted();
    struct payload *p;
#define BAD(field,value) do {p=fixture(); p->field=(value); rejected();} while(0)
    BAD(version,2); BAD(nsegs,0); BAD(nsegs,65); BAD(nsegs,64);
    BAD(adt_off,UINT64_MAX-7); BAD(adt_size,UINT64_MAX);
    BAD(phys_base,0); BAD(mem_size,UINT64_MAX);
    BAD(kernel_end,0); BAD(kernel_end,UINT64_MAX);
    BAD(adt_size,0x100000000ULL); BAD(entry_va,0);
    p=fixture(); p->kernel_end=p->virt_base+p->mem_size-8; rejected();
#define SEG_BAD(field,value) do {p=fixture(); p->segs[0].field=(value); rejected();} while(0)
    SEG_BAD(file_off,UINT64_MAX); SEG_BAD(file_size,UINT64_MAX);
    SEG_BAD(vmaddr,UINT64_MAX); SEG_BAD(vmsize,UINT64_MAX);
    SEG_BAD(vmaddr,p->virt_base-1); SEG_BAD(vmsize,0x100004000ULL);
    SEG_BAD(vmsize,1); SEG_BAD(vmsize,0x8000);
    fixture(); hi=lo; rejected();
    puts("PASS: actual loader bounds, no destination writes, unaligned concatenation");
}
'''
with tempfile.TemporaryDirectory() as tmp:
    c = Path(tmp) / 'test.c'
    c.write_text(source + harness)
    binary = Path(tmp) / 'test'
    subprocess.run(['cc', '-DSHIM_MARBLE', '-DSHIM_MARBLE_XNU', '-I'+str(root),
                    '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
                    str(c), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True,
                   env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
