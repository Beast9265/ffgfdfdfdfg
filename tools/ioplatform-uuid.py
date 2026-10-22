#!/usr/bin/env python3
"""Reproduce pinned arm XNU generatePlatformUUID from raw ADT identity bytes."""
import argparse
import hashlib
from pathlib import Path
import re
import struct
import uuid

ARM_NAMESPACE = bytes.fromhex('A6DD4CCBB5E84AF5ACDDB6DC6A0542B8')


def platform_uuid(ecid_bytes, chip_bytes):
    if len(ecid_bytes) != 8 or len(chip_bytes) != 4:
        raise ValueError('XNU requires 8-byte unique-chip-id and 4-byte chip-id')
    digest = bytearray(hashlib.sha1(ARM_NAMESPACE + ecid_bytes + chip_bytes).digest())
    digest[6] = (digest[6] & 0x0f) | 0x50
    digest[8] = (digest[8] & 0x3f) | 0x80
    return str(uuid.UUID(bytes=bytes(digest[:16]))).upper()


def check_source(path):
    source = path.read_text().split('IOPlatformExpertDevice::generatePlatformUUID( void )', 1)[1]
    arm = source.split('#else /* !defined(__x86_64__) */', 1)[0]
    namespace = re.search(r'const uuid_t space = \{([^}]+)\}', arm)[1]
    assert bytes(int(x, 16) for x in re.findall(r'0x[0-9a-fA-F]+', namespace)) == ARM_NAMESPACE
    assert arm.index('SHA1Update( &context, space') < arm.index('SHA1Update( &context, data1') < arm.index('SHA1Update( &context, data2')
    for gate in ['data1->getLength() == 8', 'data2->getLength() == 4',
                 'digest[6] = (digest[6] & 0x0F) | 0x50;',
                 'digest[8] = (digest[8] & 0x3F) | 0x80;', 'uuid_unparse( digest, uuid )']:
        assert gate in arm, gate


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ecid', type=lambda x: int(x, 0), required=True)
    ap.add_argument('--chip-id', type=lambda x: int(x, 0), required=True)
    ap.add_argument('--xnu-source', type=Path)
    args = ap.parse_args()
    if args.xnu_source:
        check_source(args.xnu_source)
    # ADT generator serializes these properties little endian; XNU hashes raw bytes.
    assert platform_uuid(struct.pack('<Q', 0x5357454554000001), struct.pack('<I', 0x8015)) == 'A9683613-3704-53F2-95D0-98A8FB574E78'
    print(platform_uuid(struct.pack('<Q', args.ecid), struct.pack('<I', args.chip_id)))


if __name__ == '__main__':
    main()
