#!/usr/bin/env python3
"""Exercise the actual 0082 sense decoder/classifier, including physical response=1."""
from pathlib import Path
import subprocess, tempfile
patch = (Path(__file__).resolve().parents[1] / 'xnu/patches/0082-marble-onecpu-bringup.patch').read_text()
source = '\n'.join(line[1:] for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++'))
a = source.index('\t/* Same bounded fixed/descriptor')
b = source.index('\tif (ucd->resp[7] &&', a)
classifier = source[a:b]
h = r"""
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
struct { bool initializing; } su;
struct response { uint8_t resp[512]; };
struct descriptor { uint32_t dw2; };
static bool classify(unsigned ocs,unsigned tt,unsigned response,unsigned status,unsigned code,unsigned n,unsigned key,unsigned asc,unsigned ascq) {
struct response c={0}, *ucd=&c; struct descriptor d={ocs}, *utrd=&d;
c.resp[0]=tt;c.resp[6]=response;c.resp[7]=status;c.resp[32]=n>>8;c.resp[33]=n;
c.resp[34]=code;
if ((code&0x7f)==0x70 || (code&0x7f)==0x71) {c.resp[36]=key;c.resp[46]=asc;c.resp[47]=ascq;}
else {c.resp[35]=key;c.resp[36]=asc;c.resp[37]=ascq;}
{
"""
main = r"""
return su.initializing;
}
}
int main(void) {
for(unsigned code=0x70;code<=0x73;code++) {
unsigned n=code<0x72?14:4;
assert(classify(0,0x21,1,2,code,n,2,4,2));
assert(classify(0,0x21,0,2,code,n,2,4,2));
assert(!classify(0,0x21,1,2,code,n,2,4,1));
assert(!classify(0,0x21,1,2,code,n,5,0x24,0));
assert(!classify(1,0x21,1,2,code,n,2,4,2));
assert(!classify(0,0x20,1,2,code,n,2,4,2));
assert(!classify(0,0x21,1,0,code,n,2,4,2));
for(unsigned shortlen=0;shortlen<n;shortlen++) assert(!classify(0,0x21,1,2,code,shortlen,2,4,2));
assert(!classify(0,0x21,1,2,code,479,2,4,2));
}
assert(!classify(0,0x21,1,2,0x74,14,2,4,2));
puts("PASS physical tuple and nearby negative/malformed/short fixed and descriptor sense");
}
"""
with tempfile.TemporaryDirectory() as tmp:
    c=Path(tmp)/'test.c'; exe=Path(tmp)/'test'
    c.write_text(h+classifier+main)
    subprocess.run(['clang','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
