#!/usr/bin/env python3
"""Audit the linked image contract for MARBLE's sparse bootstrap mappings.

Run after linking with the exact ADT used for mkpayload.py. --reference permits
an older image without marble_boot_l3; its addresses cannot certify a new link.
No image, device or storage writes. All displayed intervals are half-open.
"""
import argparse
import struct
import subprocess
from pathlib import Path

from mkpayload import parse_macho

PAGE, BLOCK = 0x4000, 0x2000000
PHYS, SIZE = 0x840000000, 0x100000000
DEV_BLOCK, DEV_PAGE = 0x6000000000040d, 0x6000000000040f
WB_EXEC, WB_DATA, FB_PAGE = 0x40000000000703, 0x60000000000703, 0x60000000000607


def roundup(value):
    return (value + PAGE - 1) & -PAGE


def audit(kernel, adt_size, reference=False, allocator_pages=160, ramdisk_size=0):
    raw = Path(kernel).read_bytes()
    macho = parse_macho(raw)
    segments = []
    offset = 32
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        command, length = struct.unpack_from('<II', raw, offset)
        if command == 0x19:
            va, size = struct.unpack_from('<QQ', raw, offset + 24)
            prot = struct.unpack_from('<I', raw, offset + 60)[0]
            if size:
                segments.append((va, va + size, prot))
        offset += length
    header = macho['segs'][0]['vmaddr']
    base = header & -BLOCK
    delta = base - PHYS
    end = roundup(max(hi for _, hi, _ in segments)) - delta
    ba = roundup(end + roundup(ramdisk_size) + adt_size)
    top = ba + PAGE
    arena_end = top + allocator_pages * PAGE
    first = (header - delta) & -BLOCK
    count = (arena_end - first + BLOCK - 1) // BLOCK
    assert 0 < count <= 16
    assert (base - PHYS) % BLOCK == 0
    assert PHYS <= first < top <= arena_end <= PHYS + SIZE
    assert (base >> 36) == ((arena_end - 1 + delta) >> 36)
    pages = {}
    for lo, hi, prot in segments:
        assert header <= lo < hi <= end + delta
        for va in range(lo & -PAGE, roundup(hi), PAGE):
            pa = va - delta
            flags = WB_EXEC if prot & 4 else WB_DATA
            # A page shared by segments must remain executable if either needs it.
            if pages.get(pa) != WB_EXEC:
                pages[pa] = flags
    for pa in range(end, arena_end, PAGE):
        pages[pa] = WB_DATA
    assert all(pa % PAGE == 0 for pa in pages)
    for pa in range(top, arena_end, PAGE):
        assert pages[pa] == WB_DATA
    print(f'Allocator [{top:#x}, {arena_end:#x}): {allocator_pages} WB/XN pages in both aliases')
    if allocator_pages:
        print(f'invalid_tte PA={top:#x} VA={top+delta:#x}; cpu_tte PA={top+PAGE:#x} VA={top+PAGE+delta:#x}')
    output = subprocess.check_output(['llvm-nm', '-n', str(kernel)], text=True)
    symbols = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    required = {
        '__mh_execute_header': False, '__start': True,
        '_LowExceptionVectorBase': True, '_start_first_cpu': True,
        '_marble_post_mmu_isb': True, '_arm_init': True,
        '_bootstrap_pagetables': False, '_marble_fb_tables': False,
        '_intstack': False, '_excepstack': False,
    }
    if not reference:
        required['_marble_boot_l3'] = False
    for name, executable in required.items():
        pa = symbols[name] - delta
        expected = WB_EXEC if executable else WB_DATA
        assert pages[pa & -PAGE] == expected, (name, hex(pa), executable)
        print(f'{name}: PA={pa:#x} descriptor={(pa & -PAGE) | expected:#018x}')
    objects = [('_bootstrap_pagetables', 4 * PAGE)]
    if not reference:
        objects.append(('_marble_fb_tables', PAGE))
    elif (symbols['_marble_fb_tables'] - delta) % PAGE:
        print('REFERENCE WARNING: old framebuffer L3 is not 16KiB aligned')
    if not reference:
        objects.append(('_marble_boot_l3', 32 * PAGE))
    for name, size in objects:
        pa = symbols[name] - delta
        assert pa % PAGE == 0
        assert pa + size <= end
        assert all(pages[p] == WB_DATA for p in range(pa, pa + size, PAGE))
    for low, high in [('_intstack', '_intstack_top'), ('_excepstack', '_excepstack_top')]:
        lo, hi = symbols[low] - delta, symbols[high] - delta
        assert lo < hi <= end
        assert all(pages[p] == WB_DATA for p in range(lo & -PAGE, roundup(hi), PAGE))
        print(f'stack {low}: [{lo:#x}, {hi:#x}) WB/XN')
    old_count = (SIZE - (header - base)) // BLOCK
    print(f'OLD V=P VA=PA [{PHYS:#x}, {PHYS + old_count * BLOCK:#x}), {old_count} L2 WB blocks')
    print(f'OLD KVA [{base:#x}, {base + old_count * BLOCK:#x}) -> same PA interval')
    print(f'NEW owned tail [{end:#x}, {top:#x}); boot_args={ba:#x}')
    print(f'NEW 2 L1 + 2 L2 + {2 * count} RAM L3 + 1 framebuffer L3 pages')
    print(f'NEW V=P L2 RAM indices 1056..1183: {128-count} Device blocks + {count} L3 pointers')
    print(f'NEW KVA L1 index {(base >> 36) & 2047}, L2 indices {(first+delta)>>25 & 2047}..{(((first+delta)>>25) & 2047) + count - 1}')
    # Coalesce all physical pages by attribute; the Device complement is exact.
    cursor = PHYS
    ordered = sorted(pages)
    i = 0
    while i < len(ordered):
        lo = ordered[i]
        flags = pages[lo]
        hi = lo + PAGE
        i += 1
        while i < len(ordered) and ordered[i] == hi and pages[hi] == flags:
            hi += PAGE
            i += 1
        if cursor < lo:
            print(f'Device/XN V=P [{cursor:#x}, {lo:#x}); KVA invalid')
        print(f'Normal-WB {"EXEC" if flags == WB_EXEC else "XN"} PA [{lo:#x}, {hi:#x}); KVA [{lo+delta:#x}, {hi+delta:#x})')
        cursor = hi
    if cursor < PHYS + SIZE:
        print(f'Device/XN V=P [{cursor:#x}, {PHYS+SIZE:#x}); KVA invalid')
    print(f'Framebuffer [0xb8000000, 0xb89e4000): 633 Normal-NC/XN pages, first={0xb8000000 | FB_PAGE:#018x}')
    print('PASS: loaded segments, code, stacks, tables, owned tail, alias attributes and capacity')
    if reference:
        print('REFERENCE IMAGE ONLY: does not certify new linked addresses or marble_boot_l3 placement')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel')
    parser.add_argument('--adt-size', type=lambda n: int(n, 0), required=True)
    parser.add_argument('--ramdisk-size', type=lambda n: int(n, 0), default=0)
    parser.add_argument('--reference', action='store_true')
    parser.add_argument('--allocator-pages', type=int, choices=[0,160], default=160, help='0 reproduces the pre-arena policy; 160 audits the new policy')
    options = parser.parse_args()
    assert options.adt_size > 0
    audit(options.kernel, options.adt_size, options.reference, options.allocator_pages, options.ramdisk_size)
