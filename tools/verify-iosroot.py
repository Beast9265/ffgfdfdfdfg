#!/usr/bin/env python3
"""Verify the mounted, flattened iPhone X 20H392 root; makes no changes."""
import os
from pathlib import Path
import plistlib
import stat
import struct
import sys


def verify(root):
    version = plistlib.loads((root / 'System/Library/CoreServices/SystemVersion.plist').read_bytes())
    assert version['ProductBuildVersion'] == '20H392', version
    for name in ('sbin/launchd', 'usr/lib/dyld'):
        p = root / name
        st = p.stat()
        assert stat.S_ISREG(st.st_mode), name
        assert (st.st_uid, st.st_gid, stat.S_IMODE(st.st_mode)) == (0, 0, 0o755), (name, st)
        with p.open('rb') as f:
            magic, cpu = struct.unpack('<II', f.read(8))
        assert (magic, cpu) == (0xfeedfacf, 0x100000c), (name, hex(magic), hex(cpu))
        print(f'PASS /{name}: arm64 Mach-O root:wheel 0755')
    cache = 'System/Library/Caches/com.apple.dyld'
    for kind in ('OS', 'App'):
        tree = root / 'private/preboot/Cryptexes' / kind
        assert tree.is_dir() and any(tree.iterdir()), tree
        print(f'PASS cryptex {kind}: populated')
    files = sorted((root / cache).glob('dyld_shared_cache_arm64*'))
    assert files and (root / cache / 'dyld_shared_cache_arm64').is_file(), 'missing cache'
    for p in files:
        assert p.is_file() and p.stat().st_size > 0, p
        source = root / 'private/preboot/Cryptexes/OS' / cache / p.name
        assert os.path.samefile(p, source), f'not a cache hard link: {p}'
    with (root / cache / 'dyld_shared_cache_arm64').open('rb') as f:
        header = f.read(16)
    assert header.startswith(b'dyld_v1') and b'arm64' in header, header
    print(f'PASS {len(files)} arm64 cache files, cryptex hard links; build 20H392')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: verify-iosroot.py MOUNTED_ROOT')
    verify(Path(sys.argv[1]).resolve())
