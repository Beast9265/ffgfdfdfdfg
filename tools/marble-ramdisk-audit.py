#!/usr/bin/env python3
"""Validate the exact MARBLE RAMDisk payload and its sparse-map/allocator contract."""
import importlib.util
import struct
import sys
from pathlib import Path

import adt
from mkpayload import parse_macho, PAGE, SEG_TABLE


def audit(kernel, payload, init):
    image = Path(init).read_bytes()
    if image[1024:1028] == b'HX\x00\x05':
        # Root builder independently checks catalog, ownership, modes and init bytes.
        assert image[:4] == b'\0' * 4
        print('PASS: HFSX RAMDisk; mockfs rejects non-Mach-O boot blocks')
    else:
        m = parse_macho(image)
        assert m['cputype'] == 0x100000c and m['cpusub'] == 0 and m['entry']
        commands, offset = [], 32
        for _ in range(struct.unpack_from('<I', image, 16)[0]):
            cmd, size = struct.unpack_from('<II', image, offset)
            commands.append(cmd)
            offset += size
        assert set(commands) == {0x19, 0x5, 0x1d}, commands
        assert b'*** MARBLE USERSPACE: PID 1 RUNNING ***' in image
        print('PASS: static arm64 LC_UNIXTHREAD, ad-hoc signature, no dylib/dyld commands')
    blob = Path(payload).read_bytes()
    magic, version, nsegs = struct.unpack_from('<8sII', blob)
    assert magic == b'SWEETXNU' and version == 1
    base, entry, adtoff, adtsize, end, phys, memsize = struct.unpack_from('<7Q', blob, 16)
    assert phys == 0x840000000
    cmdline = blob[0x48:SEG_TABLE].split(b'\0')[0].decode()
    assert cmdline == 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=md0'
    root, _ = adt.parse(blob[adtoff:adtoff + adtsize])
    chosen = next(c for c in root.children if c.name == 'chosen')
    mmap = next(c for c in chosen.children if c.name == 'memory-map')
    pa, size = struct.unpack('<QQ', mmap.prop('RAMDisk'))
    kernel_m = parse_macho(Path(kernel).read_bytes())
    kernel_end = max(s['vmaddr'] + s['vmsize'] for s in kernel_m['segs'])
    rounded = lambda n: (n + PAGE - 1) & -PAGE
    assert pa == phys + rounded(kernel_end) - base
    assert size == rounded(len(image)) and pa % PAGE == 0
    assert end == base + pa + size - phys
    segs = [struct.unpack_from('<4Q', blob, SEG_TABLE + 32*i) for i in range(nsegs)]
    va, vmsize, fileoff, filesize = segs[-1]
    assert (va, vmsize, filesize) == (pa - phys + base, size, len(image))
    assert blob[fileoff:fileoff + filesize] == image
    assert all(v + s <= va for v, s, _, _ in segs[:-1])
    adtpa = phys + end - base
    bootargs = rounded(adtpa + adtsize)
    top = bootargs + PAGE
    assert pa + size == adtpa <= bootargs < top <= phys + memsize
    print(f'PASS: RAMDisk [{pa:#x}, {pa+size:#x}); ADT={adtpa:#x}; boot_args={bootargs:#x}; top={top:#x}')
    print(f'PASS: RAMDisk bytes match source image; kernel segments/stacks/tables precede RAMDisk; cmdline={cmdline}')
    spec = importlib.util.spec_from_file_location('bootstrap', Path(__file__).with_name('marble-bootstrap-audit.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.audit(kernel, adtsize, ramdisk_size=len(image))


if __name__ == '__main__':
    audit(*sys.argv[1:])
