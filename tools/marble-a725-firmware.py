#!/usr/bin/env python3
"""Inventory and validate user-supplied SM7475 Adreno 725 firmware.

This tool never modifies its input and never copies proprietary firmware into
the repository.  Point it at an extracted Android vendor firmware directory;
it recursively locates the three filenames required by the stock Gen7.4 KGSL
configuration and prints identities suitable for a bring-up handoff.
"""
import argparse
import hashlib
import json
import pathlib
import struct


NAMES = ('gmu_gen70000.bin', 'a730_sqe.fw', 'a730_zap.mdt')
GMU_RANGES = (
    (0x00000000, 0x00004000, 'ITCM'),
    (0x00004000, 0x01000000, 'CACHE'),
    (0x10004000, 0x10008000, 'DTCM'),
    (0x60000000, 0x80000000, 'NONCACHED'),
    (0xc0000000, 0xe0000000, 'NONCACHED_EXTENDED'),
)


def unique_file(root, name):
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise ValueError(f'{name}: expected one file below {root}, found {len(matches)}')
    return matches[0]


def validate_gmu(image):
    offset = 0
    blocks = []
    while offset < len(image):
        if len(image) - offset < 16:
            raise ValueError(f'GMU truncated header at {offset:#x}')
        address, size, kind, value = struct.unpack_from('<4I', image, offset)
        offset += 16
        if size > len(image) - offset:
            raise ValueError(f'GMU block at {offset - 16:#x} exceeds image')
        if size:
            end = address + size
            region = next((label for start, stop, label in GMU_RANGES
                           if address >= start and end <= stop), None)
            if end > 0xffffffff or region is None:
                raise ValueError(f'GMU block has invalid range {address:#x}+{size:#x}')
            blocks.append(dict(address=hex(address), size=hex(size), region=region))
            offset += size
        else:
            if kind > 7:
                raise ValueError(f'GMU metadata has unknown type {kind}')
            blocks.append(dict(address=hex(address), size='0x0', type=kind,
                               value=hex(value)))
    if not blocks or not any(int(block['size'], 16) for block in blocks):
        raise ValueError('GMU image contains no loadable block')
    return dict(format='qualcomm-gmu-blocks', blocks=len(blocks), layout=blocks)


def validate_sqe(image):
    if len(image) < 8 or len(image) % 4:
        raise ValueError('SQE firmware must be a nonempty dword stream')
    version, = struct.unpack_from('<I', image)
    if version in (0, 0xffffffff):
        raise ValueError('SQE firmware has an invalid version word')
    return dict(format='a7xx-sqe-dwords', version=hex(version), dwords=len(image) // 4)


def validate_mdt(image):
    if len(image) < 0x34 or image[:4] != b'\x7fELF' or image[4] != 1 or image[5] != 1:
        raise ValueError('zap MDT is not a little-endian ELF32 metadata image')
    phoff, = struct.unpack_from('<I', image, 0x1c)
    phentsize, phnum = struct.unpack_from('<HH', image, 0x2a)
    if phentsize < 0x20 or phoff + phentsize * phnum > len(image):
        raise ValueError('zap MDT program headers exceed the metadata image')
    return dict(format='elf32-mdt', program_headers=phnum)


VALIDATORS = {
    'gmu_gen70000.bin': validate_gmu,
    'a730_sqe.fw': validate_sqe,
    'a730_zap.mdt': validate_mdt,
}


def inventory(root):
    result = {'root': str(root.resolve()), 'firmware': {}}
    for name in NAMES:
        path = unique_file(root, name)
        image = path.read_bytes()
        details = VALIDATORS[name](image)
        result['firmware'][name] = {
            'path': str(path.resolve()),
            'size': len(image),
            'sha256': hashlib.sha256(image).hexdigest(),
            **details,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=pathlib.Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result = inventory(args.directory)
    except ValueError as error:
        raise SystemExit(f'FAIL: {error}')
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, info in result['firmware'].items():
            print(f"{name}: {info['size']} bytes SHA256={info['sha256']} path={info['path']}")
        print('PASS: exact A725 firmware set found and structurally validated')


if __name__ == '__main__':
    main()
