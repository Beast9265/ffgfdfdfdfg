#!/usr/bin/env python3
"""Regression tests for explicit cached launchd job removal."""
import copy
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

HELPER = Path(__file__).with_name('patch-launchd-plist.py')


class PatchLaunchdTests(unittest.TestCase):
    def test_explicit_removal_and_logging(self):
        original = {'Other': [b'opaque', 17], 'LaunchDaemons': {
            '/daemon/a.plist': {'Label': 'a', 'MachServices': {'demand.a': True}},
            '/daemon/b.plist': {'Label': 'b'},
            '/daemon/gui.plist': {'Label': 'gui', 'EnvironmentVariables': {'KEEP': 'yes'}},
            '/daemon/keep.plist': {'Label': 'keep', 'Unknown': [1, b'keep'], '_PanicOnCrash': True},
        }}
        with tempfile.TemporaryDirectory() as directory:
            src, dst = Path(directory)/'in', Path(directory)/'out'
            src.write_bytes(plistlib.dumps(original, fmt=plistlib.FMT_BINARY))
            result = subprocess.run([sys.executable, str(HELPER), str(src), str(dst),
                                     'gui', '--disable', 'a', '--disable', 'b'],
                                    check=True, capture_output=True, text=True)
            expected = copy.deepcopy(original)
            del expected['LaunchDaemons']['/daemon/a.plist']
            del expected['LaunchDaemons']['/daemon/b.plist']
            gui = expected['LaunchDaemons']['/daemon/gui.plist']
            gui.update(StandardOutPath='/dev/console', StandardErrorPath='/dev/console')
            gui['EnvironmentVariables'].update(OS_ACTIVITY_DT_MODE='YES', CFLOG_FORCE_STDERR='1')
            keep = expected['LaunchDaemons']['/daemon/keep.plist']
            keep['_PanicOnCrasX'] = keep.pop('_PanicOnCrash')
            self.assertEqual(plistlib.loads(dst.read_bytes()), expected)
            for key, label in (('/daemon/a.plist', 'a'), ('/daemon/b.plist', 'b')):
                self.assertIn(f'dictionary entry {key!r}, Label {label!r}', result.stdout)
            for args in (['--disable', 'missing'], ['missing'], ['gui', '--disable', 'gui']):
                before = dst.read_bytes()
                failed = subprocess.run([sys.executable, str(HELPER), str(src), str(dst), *args],
                                        capture_output=True)
                self.assertNotEqual(failed.returncode, 0)
                self.assertEqual(dst.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
