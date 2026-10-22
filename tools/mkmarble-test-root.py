#!/usr/bin/env python3
"""Build a reproducible, unmounted 16 MiB HFSX MARBLE diagnostic RAMDisk.

Requires mkfs.hfsplus, fsck.hfsplus (hfsprogs), and hfsplus (libdmg-hfsplus).
Override their paths with MKFS_HFSPLUS, FSCK_HFSPLUS and HFSPLUS.
Only regular output files are accepted; no mounts or device access.
"""
import argparse
import hashlib
import os
from pathlib import Path
import stat
import struct
import subprocess
import tempfile


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def catalog(blob):
    """Read the tiny catalog leaf records; reject unexpected extents/tree layouts."""
    block = struct.unpack_from('>I', blob, 1024 + 40)[0]
    logical, _, blocks, start, count = struct.unpack_from('>QIIII', blob, 1024 + 272)
    assert count == blocks and logical <= count * block
    base = start * block
    node_size = struct.unpack_from('>H', blob, base + 14 + 18)[0]
    total_nodes = struct.unpack_from('>I', blob, base + 14 + 22)[0]
    assert total_nodes * node_size <= logical
    for node in range(total_nodes):
        off = base + node * node_size
        if struct.unpack_from('>b', blob, off + 8)[0] != -1:
            continue
        records = struct.unpack_from('>H', blob, off + 10)[0]
        for i in range(records):
            rec = off + struct.unpack_from('>H', blob, off + node_size - 2 * (i + 1))[0]
            keylen, parent, nchars = struct.unpack_from('>HIH', blob, rec)
            name = blob[rec + 8:rec + 8 + 2*nchars].decode('utf-16-be')
            yield parent, name, rec + 2 + keylen


def normalize_and_verify(path, init):
    blob = bytearray(path.read_bytes())
    assert blob[1024:1028] == b'HX\x00\x05'  # case-sensitive HFS+
    epoch = 2082844800 + 1700000000  # fixed Unix epoch converted to HFS time
    for vh in (1024, len(blob) - 1024):
        struct.pack_into('>4I', blob, vh + 16, epoch, epoch, 0, epoch)
        struct.pack_into('>I', blob, vh + 68, 1)  # writeCount
        blob[vh + 104:vh + 112] = hashlib.sha256(init).digest()[:8]  # volume ID
    found = {}
    for parent, name, rec in catalog(blob):
        kind = struct.unpack_from('>H', blob, rec)[0]
        if kind not in (1, 2):
            continue
        cnid = struct.unpack_from('>I', blob, rec + 8)[0]
        struct.pack_into('>5I', blob, rec + 12, epoch, epoch, epoch, epoch, 0)
        struct.pack_into('>II', blob, rec + 32, 0, 0)
        mode = struct.unpack_from('>H', blob, rec + 42)[0]
        assert mode == (stat.S_IFDIR if kind == 1 else stat.S_IFREG) | 0o755
        found[(parent, name)] = (cnid, kind, rec)
    assert set(found) == {(1, 'MarbleRoot'), (2, 'sbin'), (2, 'dev'), (found[(2, 'sbin')][0], 'launchd')}
    _, kind, rec = found[(found[(2, 'sbin')][0], 'launchd')]
    assert kind == 2
    length, _, blocks, start, count = struct.unpack_from('>QIIII', blob, rec + 88)
    block = struct.unpack_from('>I', blob, 1064)[0]
    assert blocks == count and length == len(init)
    assert blob[start*block:start*block + length] == init
    assert blob[:4] == b'\0'*4  # mockfs's Mach-O probe returns EINVAL
    path.write_bytes(blob)
    print('PASS: HFSX MarbleRoot; only /sbin/launchd and /dev; root:wheel 0755; exact init bytes')


def build(init_path, output):
    init = init_path.read_bytes()
    assert init[:4] == b'\xcf\xfa\xed\xfe'
    assert b'*** MARBLE USERSPACE: PID 1 RUNNING ***' in init
    assert not output.exists(), f'refusing to overwrite {output}'
    assert output.parent.is_dir()
    mkfs = os.environ.get('MKFS_HFSPLUS', 'mkfs.hfsplus')
    hfs = os.environ.get('HFSPLUS', 'hfsplus')
    fsck = os.environ.get('FSCK_HFSPLUS', 'fsck.hfsplus')
    with tempfile.TemporaryDirectory(prefix='marble-root-', dir=output.parent) as tmp:
        image = Path(tmp) / 'MarbleRoot.img'
        with image.open('xb') as f:
            f.truncate(16 * 1024 * 1024)
        run(mkfs, '-s', '-v', 'MarbleRoot', '-U', '0', '-G', '0', '-M', '755', image)
        for name in ('/sbin', '/dev'):
            run(hfs, image, 'mkdir', name)
        run(hfs, image, 'add', init_path, '/sbin/launchd')
        run(hfs, image, 'chmod', '755', '/sbin/launchd')
        normalize_and_verify(image, init)
        run(fsck, '-fn', image)
        extracted = Path(tmp) / 'launchd'
        run(hfs, image, 'extract', '/sbin/launchd', extracted)
        assert extracted.read_bytes() == init
        # The read-only extraction tool can update the volume header on close.
        normalize_and_verify(image, init)
        run(fsck, '-fn', image)
        os.link(image, output)  # atomic, refuses existing paths
    print(hashlib.sha256(output.read_bytes()).hexdigest(), output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('init', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.init.resolve(), args.output.resolve())
