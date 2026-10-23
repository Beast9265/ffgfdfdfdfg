#!/usr/bin/env python3
"""Validate/package a MARBLE root generation, then retain raw+sparse+fallback.

Called automatically by mkiosroot.sh --board marble. Never runs for kernel builds.
MARBLE_KEEP_ROOTS=all disables pruning. See docs/MARBLE_ROOT_RETENTION.md.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

REPO = Path(__file__).resolve().parent.parent
DIRECTORY = REPO / 'shim/out/marble-xnu'
PATTERN = re.compile(r'ios16-root-marble-20H392-[A-Za-z0-9][A-Za-z0-9._-]*\.(?:img|simg)\Z')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as src:
        for block in iter(lambda: src.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def regular(directory, name):
    if not PATTERN.fullmatch(name) or Path(name).name != name:
        raise ValueError(f'not a root generation: {name}')
    path = directory / name
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.resolve() != path:
        raise ValueError(f'not a canonical regular file: {path}')
    return path, (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def checked_directory():
    # Reject symlinks in every output-directory component, even within the repo.
    for path in (REPO / 'shim', REPO / 'shim/out', DIRECTORY):
        if path.is_symlink():
            raise ValueError(f'symlink output directory: {path}')
    if DIRECTORY.resolve() != DIRECTORY or not DIRECTORY.is_dir():
        raise ValueError('root output directory is not canonical')
    return DIRECTORY


def journal(path):
    size = path.stat().st_size
    if size < 2048:
        raise ValueError('short HFS image')
    with path.open('rb') as src:
        headers = []
        for offset in (1024, size - 1024):
            src.seek(offset)
            headers.append(src.read(512))
    for header in headers:
        if header[:4] != b'HX\x00\x05' or not int.from_bytes(header[4:8], 'big') & (1 << 13):
            raise ValueError('HFSX journal flag/signature verification failed')
    if headers[0] != headers[1]:
        raise ValueError('primary/alternate HFS headers differ')
    print('PASS journal verification: both HFSX headers match, journal bit set', flush=True)


def prune(directory, records, keep_all=False):
    """Private fixture-testable planner; CLI always supplies checked_directory()."""
    candidates = {}
    for path in directory.iterdir():
        if PATTERN.fullmatch(path.name):
            # Abort before deleting anything if ANY matching entry is unsafe.
            candidates[path.name] = regular(directory, path.name)
    # Record order is successful validation order, never file mtime.
    newest = records[-1]
    current = {newest['raw'], newest['sparse']}
    for name in current:
        path, _ = candidates[name]
        if digest(path) != newest['sha256'][name]:
            raise ValueError(f'validated current generation changed: {name}')
    fallback = None
    for record in reversed(records[:-1]):
        name = record['sparse']
        if name != newest['sparse'] and name in candidates:
            path, _ = candidates[name]
            if digest(path) == record['sha256'][name]:
                fallback = name
                break
    # Bootstrap conservatively: no proof of a prior validated sparse => no pruning.
    if keep_all or fallback is None:
        for name in sorted(candidates):
            print(f'KEEP {directory / name}', flush=True)
        print('Pruning disabled: ' + ('MARBLE_KEEP_ROOTS=all' if keep_all else 'no recorded validated sparse fallback'), flush=True)
        return []
    keep = current | {fallback}
    deletes = []
    for name, (path, identity) in sorted(candidates.items()):
        print(f'{"KEEP" if name in keep else "DELETE"} {path}', flush=True)
        if name not in keep:
            deletes.append((name, path, identity))
    # Recheck the complete plan before the first unlink. No wildcard/rm recursion.
    for name, path, identity in deletes:
        if regular(directory, name) != (path, identity):
            raise ValueError(f'root changed during cleanup: {name}')
    for name, path, identity in deletes:
        if regular(directory, name) != (path, identity):
            raise ValueError(f'root changed during cleanup: {name}')
        subprocess.run(['rm', '--', str(path)], check=True)
    return [name for name, _, _ in deletes]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('--check-path', action='store_true', help='validate output naming/location only, before build')
    args = parser.parse_args()
    directory = checked_directory()
    raw = args.raw.absolute()
    if raw.parent != directory or not PATTERN.fullmatch(raw.name) or raw.suffix != '.img':
        raise ValueError(f'expected named MARBLE root generation directly inside {directory}')
    if args.check_path:
        if raw.exists() or raw.is_symlink():
            raise ValueError('output already exists')
        return
    raw, _ = regular(directory, raw.name)
    sparse = raw.with_suffix('.simg')
    if sparse.exists() or sparse.is_symlink():
        raise ValueError('refusing to replace sparse output')
    # Serialize packaging, validation record and pruning, including parallel builds.
    lockpath = directory / '.marble-root-finalize.lock'
    lockfd = os.open(lockpath, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(lockfd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run([os.environ.get('FSCK_HFSPLUS', 'fsck.hfsplus'), '-f', '-n', str(raw)], check=True)
        journal(raw)
        with tempfile.TemporaryDirectory(prefix='marble-root-verify-') as mount:
            subprocess.run(['sudo', 'mount', '-t', 'hfsplus', '-o', 'loop,ro', str(raw), mount], check=True)
            try:
                subprocess.run(['python3', str(REPO / 'tools/verify-iosroot.py'), mount], check=True)
            finally:
                subprocess.run(['sudo', 'umount', mount], check=True)
        # Existing helper expands the ENTIRE sparse file and cmp's every byte.
        subprocess.run(['bash', str(REPO / 'tools/iosroot-sparse.sh'), str(raw), str(sparse)], check=True)
        hashes = {path.name: digest(path) for path in (raw, sparse)}
        sums = raw.with_suffix('.sha256')
        with sums.open('x') as output:
            output.write(''.join(f'{value}  {name}\n' for name, value in hashes.items()))
        print(sums.read_text(), end='', flush=True)
        manifest = directory / '.marble-root-validations.json'
        if manifest.is_symlink():
            raise ValueError('symlink validation registry')
        records = json.loads(manifest.read_text()) if manifest.exists() else []
        records.append(dict(raw=raw.name, sparse=sparse.name, sha256=hashes, validated_ns=time.time_ns()))
        temp = manifest.with_suffix('.tmp')
        with temp.open('x') as output:
            json.dump(records, output, indent=2)
            output.flush()
            os.fsync(output.fileno())
        temp.replace(manifest)
        prune(directory, records, os.environ.get('MARBLE_KEEP_ROOTS') == 'all')


if __name__ == '__main__':
    main()
