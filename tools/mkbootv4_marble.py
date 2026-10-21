#!/usr/bin/env python3
"""Deterministic unsigned MARBLE boot-v4 packaging; never accesses a device.

Layout follows AOSP system/tools/mkbootimg: 1584-byte header, fixed 4096-byte
pages, kernel, generic ramdisk, optional signature, each page padded.
Only inspect supports signed inputs: changing a kernel invalidates a signature.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

PAGE = 4096
HEADER = 1584
MAX_OFFSET = (1 << 64) - 1
MAX_COMPONENT = (1 << 32) - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def add(a, b):
    require(0 <= a <= MAX_OFFSET and 0 <= b <= MAX_OFFSET - a,
            'offset overflow')
    return a + b


def align(value, alignment=PAGE):
    require(alignment > 0 and alignment & (alignment - 1) == 0,
            'alignment must be a positive power of two')
    return add(value, alignment - 1) & ~(alignment - 1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data):
    require(len(data) >= HEADER, 'truncated header')
    require(data[:8] == b'ANDROID!', 'invalid boot magic')
    kernel, ramdisk, os_field, header_size = struct.unpack_from('<4I', data, 8)
    version = struct.unpack_from('<I', data, 40)[0]
    signature = struct.unpack_from('<I', data, 1580)[0]
    require(version == 4, 'only header version 4 is supported')
    require(header_size == HEADER, 'invalid v4 header size')
    require(0 < kernel <= MAX_COMPONENT, 'invalid kernel size')
    require(0 <= ramdisk <= MAX_COMPONENT and 0 <= signature <= MAX_COMPONENT,
            'invalid component size')
    ko = align(header_size)
    ro = align(add(ko, kernel))
    so = align(add(ro, ramdisk))
    end = align(add(so, signature))
    require(HEADER <= ko <= add(ko, kernel) <= ro <= add(ro, ramdisk)
            <= so <= add(so, signature) <= end, 'overlapping components')
    require(end <= len(data), 'truncated component or required page padding')
    # Bounds against actual file length also reject implausible uint32 sizes.
    return dict(kernel_size=kernel, ramdisk_size=ramdisk,
                signature_size=signature, kernel_offset=ko, ramdisk_offset=ro,
                signature_offset=so, boot_image_end=end, os_field=os_field)


def report(path, data):
    p = parse(data)
    os_word = p['os_field']
    version = os_word >> 11
    patch = os_word & 2047
    result = dict(path=str(path), magic='ANDROID!', header_version=4,
                  header_size=HEADER, page_alignment=PAGE,
                  os_version=f'{version >> 14}.{(version >> 7) & 127}.{version & 127}',
                  os_patch_level=f'{2000 + (patch >> 4):04d}-{patch & 15:02d}',
                  cmdline=data[44:1580].split(b'\0', 1)[0].decode('utf-8', 'backslashreplace'),
                  **p, file_size=len(data), trailing_bytes=len(data)-p['boot_image_end'])
    for name in ('kernel', 'ramdisk'):
        start, size = p[name + '_offset'], p[name + '_size']
        result[name + '_sha256'] = sha(data[start:start + size])
    print(json.dumps(result, indent=2))
    return p


def independent_verify(data, header, kernel, ramdisk):
    """Secondary decoder uses byte slices and page counts, not parse/align."""
    word = lambda offset: int.from_bytes(data[offset:offset + 4], 'little')
    require(data[:8] == b'ANDROID!' and word(40) == 4 and word(20) == 1584,
            'secondary header verification failed')
    require(word(8) == len(kernel) and word(12) == len(ramdisk) and word(1580) == 0,
            'secondary component sizes failed')
    require(data[:HEADER] == header, 'header metadata changed')
    kstart = 4096
    rstart = 4096 * (1 + (len(kernel) + 4095) // 4096)
    end = rstart + 4096 * ((len(ramdisk) + 4095) // 4096)
    require(kstart + len(kernel) <= rstart and rstart + len(ramdisk) <= end,
            'secondary boundary verification failed')
    require(len(data) == end, 'unexpected trailing bytes')
    require(sha(data[kstart:kstart + len(kernel)]) == sha(kernel), 'kernel SHA256 mismatch')
    require(sha(data[rstart:rstart + len(ramdisk)]) == sha(ramdisk), 'ramdisk SHA256 mismatch')
    for start, stop in ((HEADER, kstart), (kstart + len(kernel), rstart),
                        (rstart + len(ramdisk), end)):
        require(not any(data[start:stop]), 'nonzero format padding')


def wrap_xnu(payload):
    require(payload.startswith(b'SWEETXNU'), 'XNU payload must start with SWEETXNU')
    wrapped = payload + b'MRBLXNU1' + struct.pack('<Q', len(payload))
    print('raw payload size:', len(payload), 'SHA256:', sha(payload))
    print('wrapped generic-ramdisk size:', len(wrapped), 'SHA256:', sha(wrapped))
    return wrapped


def pack(stock, kernel, output, control=False, replacement_ramdisk=None):
    src = stock.read_bytes()
    p = parse(src)
    require(p['signature_size'] == 0, 'signed source rejected: cannot reuse a boot signature')
    require(0 < len(kernel) <= MAX_COMPONENT, 'new kernel must be nonempty and fit uint32')
    ramdisk = src[p['ramdisk_offset']:p['ramdisk_offset'] + p['ramdisk_size']]
    if replacement_ramdisk is not None:
        require(not control, 'control cannot replace ramdisk')
        require(0 < len(replacement_ramdisk) <= MAX_COMPONENT,
                'replacement ramdisk must be nonempty and fit uint32')
        ramdisk = replacement_ramdisk
    header = bytearray(src[:HEADER])
    struct.pack_into('<2I', header, 8, len(kernel), len(ramdisk))
    # All other valid header bytes, including packed OS/patch and reserved, retained.
    data = bytearray(header)
    data.extend(bytes(align(len(data)) - len(data)))
    for component in (kernel, ramdisk):
        data.extend(component)
        data.extend(bytes(align(len(data)) - len(data)))
    independent_verify(data, header, kernel, ramdisk)
    if control:
        require(parse(data) == p and data[:HEADER] == src[:HEADER],
                'control fields/offsets differ')
        print('control actual-region byte equality:', data == src[:p['boot_image_end']])
        print('control padding normalized to zero; header/kernel/ramdisk must match')
    # Exclusive create avoids overwriting inputs, existing artifacts, or symlinks.
    with output.open('xb') as f:
        f.write(data)
    written = output.read_bytes()
    independent_verify(written, header, kernel, ramdisk)
    report(output, written)
    print('PASS: independent post-write header, boundaries, padding, kernel and ramdisk SHA256')


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('inspect')
    inspect.add_argument('stock', type=Path)
    control = sub.add_parser('control', help='repack original kernel and ramdisk')
    control.add_argument('stock', type=Path)
    control.add_argument('output', type=Path)
    repack = sub.add_parser('repack')
    repack.add_argument('stock', type=Path)
    repack.add_argument('kernel', type=Path)
    repack.add_argument('output', type=Path)
    replacement = repack.add_mutually_exclusive_group()
    replacement.add_argument('--ramdisk', type=Path, help='arbitrary replacement generic ramdisk')
    replacement.add_argument('--xnu-payload', type=Path, help='raw SWEETXNU payload; append MARBLE locator footer')
    args = cli.parse_args()
    if args.command == 'inspect':
        report(args.stock, args.stock.read_bytes())
    elif args.command == 'control':
        src = args.stock.read_bytes()
        p = parse(src)
        kernel = src[p['kernel_offset']:p['kernel_offset'] + p['kernel_size']]
        pack(args.stock, kernel, args.output, control=True)
    else:
        kernel = args.kernel.read_bytes()
        print('input kernel size:', len(kernel), 'SHA256:', sha(kernel))
        pack(args.stock, kernel, args.output, replacement_ramdisk=
             wrap_xnu(args.xnu_payload.read_bytes()) if args.xnu_payload else
             args.ramdisk.read_bytes() if args.ramdisk else None)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, struct.error) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
