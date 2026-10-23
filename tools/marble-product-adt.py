#!/usr/bin/env python3
"""Restore the original D22AP /product in an existing MARBLE ADT only.

Preserves every existing node/property, including seed, UUID inputs, geometry,
CPU topology and boot metadata. Apple DeviceTree input remains outside git.
"""
import argparse
from pathlib import Path
import struct

import adt
import mkadt


def restore_product(blob, properties):
    root, end = adt.parse(blob)
    if end != len(blob) or b'xiaomi,marble\0' not in (root.prop('compatible') or b''):
        raise ValueError('expected a complete MARBLE ADT')
    if any(child.name == 'product' for child in root.children):
        raise ValueError('existing /product must be inspected, not overwritten')
    props = dict(properties or [])
    required = {'artwork-device-idiom': b'phone\0',
                'artwork-device-subtype': struct.pack('<I', 2436),
                'artwork-scale-factor': struct.pack('<I', 3)}
    if any(props.get(key) != value for key, value in required.items()):
        raise ValueError('original D22AP artwork properties required')
    if len(props) != len(properties) or any(key in props for key in ('name', 'AAPL,phandle')):
        raise ValueError('duplicate or reserved source properties')
    handles = []
    def collect(node):
        value = node.prop('AAPL,phandle')
        if value is not None:
            if len(value) != 4:
                raise ValueError('invalid phandle')
            handles.append(struct.unpack('<I', value)[0])
        for child in node.children:
            collect(child)
    collect(root)
    handle = max(handles, default=0) + 1
    if handle > 0xffffffff:
        raise ValueError('phandle overflow')
    root.children.append(mkadt.node('product', [('AAPL,phandle', mkadt.u32(handle)), *properties]))
    return adt.serialize(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--d22ap', type=Path, default=Path(mkadt.D22AP_ADT))
    args = parser.parse_args()
    properties = mkadt.d22ap_product(args.d22ap)
    result = restore_product(args.input.read_bytes(), properties)
    with args.output.open('xb') as target:
        target.write(result)
    print(f'PASS: added original D22AP /product ({len(properties)} properties); all prior nodes unchanged')


if __name__ == '__main__':
    main()
