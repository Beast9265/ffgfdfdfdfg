#!/usr/bin/env python3
"""Restore two GUI jobs' logging fields from the original Apple cache.

Usage: clean-gui-launchd-plist.py ORIGINAL CURRENT OUTPUT
Requires the known GUI-debug transformation (bluetoothd removed, panic keys
suppressed, two console logging jobs). Rejects unrelated semantic differences.
Never redirects GUI jobs to /dev/console, which can prevent their spawn.
"""
import copy
import plistlib
import sys
from pathlib import Path

GUI = {'com.apple.backboardd', 'com.apple.SpringBoard'}
ENV = {'OS_ACTIVITY_DT_MODE': 'YES', 'CFLOG_FORCE_STDERR': '1'}


def clean(original, current):
    expected = copy.deepcopy(original)
    jobs = expected['LaunchDaemons']
    bluetooth = [key for key, job in jobs.items() if job.get('Label') == 'com.apple.bluetoothd']
    if len(bluetooth) != 1:
        raise ValueError('expected exactly one original bluetoothd job')
    del jobs[bluetooth[0]]
    restored = copy.deepcopy(expected)
    found = set()
    for key, job in jobs.items():
        if '_PanicOnCrash' in job:
            job['_PanicOnCrasX'] = job.pop('_PanicOnCrash')
        if job.get('Label') in GUI:
            found.add(job['Label'])
            job['StandardOutPath'] = job['StandardErrorPath'] = '/dev/console'
            job.setdefault('EnvironmentVariables', {}).update(ENV)
        # Keep the current deliberate panic suppression, including GUI jobs.
        target = restored['LaunchDaemons'][key]
        if '_PanicOnCrash' in target:
            target['_PanicOnCrasX'] = target.pop('_PanicOnCrash')
    if found != GUI or current != expected:
        raise ValueError('input is not the exact known GUI-debug cache transformation')
    # Original Apple GUI jobs must have normal descriptor handling.
    for job in restored['LaunchDaemons'].values():
        if job.get('Label') in GUI:
            if 'StandardOutPath' in job or 'StandardErrorPath' in job:
                raise ValueError('original GUI job has unexpected output overrides')
    return restored


def main():
    original, current, output = map(Path, sys.argv[1:])
    result = clean(plistlib.loads(original.read_bytes()), plistlib.loads(current.read_bytes()))
    output.write_bytes(plistlib.dumps(result, fmt=plistlib.FMT_BINARY, sort_keys=False))
    print('PASS exact semantics: only bluetoothd removal + existing panic suppression versus Apple original')
    print('PASS original GUI stdout/stderr and environment restored; all unrelated jobs unchanged')


if __name__ == '__main__':
    main()
