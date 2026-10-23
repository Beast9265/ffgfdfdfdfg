#!/usr/bin/env python3
"""Disposable-fixture tests only: never invoke the real root finalizer."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
import sys

spec = importlib.util.spec_from_file_location('retention', Path(__file__).with_name('marble-root-finalize.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class RetentionTests(unittest.TestCase):
    def fixture(self, directory, count=3):
        records = []
        for n in range(count):
            names = [f'ios16-root-marble-20H392-v{n}.{ext}' for ext in ('img', 'simg')]
            for name in names:
                (directory / name).write_bytes(name.encode())
            records.append(dict(raw=names[0], sparse=names[1], sha256={name: r.digest(directory / name) for name in names}))
        for name in ['latest-marble-xnu.img', 'boot_a.img', 'other.simg', 'marble-xnu.payload']:
            (directory / name).write_bytes(b'protected')
        return records

    def test_plan_and_exact_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records = self.fixture(directory)
            deleted = r.prune(directory, records)
            self.assertEqual(set(deleted), {records[0]['raw'], records[0]['sparse'], records[1]['raw']})
            self.assertTrue((directory / records[1]['sparse']).exists())
            self.assertTrue((directory / records[2]['raw']).exists())
            self.assertTrue((directory / 'latest-marble-xnu.img').exists())
            self.assertTrue((directory / 'boot_a.img').exists())
            self.assertTrue((directory / 'other.simg').exists())

    def test_escape_and_bootstrap(self):
        for count, keep_all in [(1, False), (3, True)]:
            with tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                records = self.fixture(directory, count)
                before = set(directory.iterdir())
                self.assertEqual(r.prune(directory, records, keep_all), [])
                self.assertEqual(set(directory.iterdir()), before)

    def test_symlink_aborts_before_any_deletion(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            directory = Path(tmp)
            records = self.fixture(directory)
            target = Path(outside) / 'precious.img'
            target.write_bytes(b'precious')
            (directory / 'ios16-root-marble-20H392-link.img').symlink_to(target)
            before = set(directory.iterdir())
            with self.assertRaises(ValueError):
                r.prune(directory, records)
            self.assertEqual(set(directory.iterdir()), before)
            self.assertEqual(target.read_bytes(), b'precious')

    def test_current_hash_mismatch_never_deletes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records = self.fixture(directory)
            (directory / records[-1]['raw']).write_bytes(b'changed')
            before = set(directory.iterdir())
            with self.assertRaises(ValueError):
                r.prune(directory, records)
            self.assertEqual(set(directory.iterdir()), before)

    def test_corrupt_fallback_retains_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            records = self.fixture(directory, 2)
            (directory / records[0]['sparse']).write_bytes(b'bad')
            before = set(directory.iterdir())
            self.assertEqual(r.prune(directory, records), [])
            self.assertEqual(set(directory.iterdir()), before)

    def test_validation_failure_never_prunes(self):
        for failure in ('fsck', 'journal', 'root', 'sparse', 'hash'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                raw = directory / 'ios16-root-marble-20H392-new.img'
                raw.write_bytes(b'fixture')
                def run(cmd, **kwargs):
                    if ((failure == 'fsck' and '-f' in cmd) or
                        (failure == 'root' and any('verify-iosroot.py' in part for part in cmd)) or
                        (failure == 'sparse' and cmd[0] == 'bash')):
                        raise subprocess.CalledProcessError(1, cmd)
                    if cmd[0] == 'bash':
                        raw.with_suffix('.simg').write_bytes(b'sparse')
                def journal(path):
                    if failure == 'journal':
                        raise ValueError('fixture invalid journal')
                def digest(path):
                    if failure == 'hash':
                        raise OSError('fixture hash read failed')
                    return 'fixture'
                with patch.object(sys, 'argv', ['finalizer', str(raw)]), \
                     patch.object(r, 'checked_directory', return_value=directory), \
                     patch.object(r.subprocess, 'run', side_effect=run), \
                     patch.object(r, 'journal', side_effect=journal), \
                     patch.object(r, 'digest', side_effect=digest), \
                     patch.object(r, 'prune') as prune:
                    with self.assertRaises((ValueError, OSError, subprocess.CalledProcessError)):
                        r.main()
                    prune.assert_not_called()
                    self.assertFalse((directory / '.marble-root-validations.json').exists())
                    self.assertTrue(raw.exists())

    def test_journal_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'root.img'
            path.write_bytes(bytes(4096))
            with self.assertRaises(ValueError):
                r.journal(path)
            header = bytearray(512)
            header[:4] = b'HX\0\5'
            header[4:8] = (1 << 13).to_bytes(4, 'big')
            with path.open('r+b') as output:
                for offset in (1024, 3072):
                    output.seek(offset)
                    output.write(header)
            r.journal(path)


if __name__ == '__main__':
    unittest.main()
