#!/usr/bin/env python3
"""Make selected launchd jobs log to the console (SWEET bring-up debugging).

  patch-launchd-plist.py IN.plist OUT.plist [LABEL ...] [--disable LABEL]...

IN is /System/Library/xpc/launchd.plist (binary plist, read by launchd when
booted with launchd_unsecure_cache=1). For every job whose Label is given,
stdout/stderr go to /dev/console and diagnostic environment variables are added.
WARNING: historical SWEET testing proved these paths can prevent backboardd
from spawning (EACCES). Do not use this logging mode for GUI jobs. Prefer the
kernel /dev/null tee; clean-gui-launchd-plist.py restores the known debug cache.

Every job's _PanicOnCrash key is also renamed (_PanicOnCrasX), so a crashing
daemon does not panic the system during bring-up.

Repeat --disable LABEL to remove explicitly selected jobs by their Label,
including their MachServices registrations. No dependencies are disabled.
"""
import argparse
import plistlib
import sys

LOG_ENV = {'OS_ACTIVITY_DT_MODE': 'YES', 'CFLOG_FORCE_STDERR': '1'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('labels', nargs='*', help='job Labels for console logging')
    parser.add_argument('--disable', action='append', default=[], metavar='LABEL')
    args = parser.parse_args()
    src, dst, labels = args.src, args.dst, set(args.labels)
    disabled = set(args.disable)
    if labels & disabled:
        parser.error('cannot both log and disable: ' + ', '.join(sorted(labels & disabled)))
    with open(src, 'rb') as f:
        plist = plistlib.load(f)
    jobs = plist['LaunchDaemons']
    available = {job.get('Label') for job in jobs.values()}
    missing = (labels | disabled) - available
    if missing:
        sys.exit(f'jobs not found: {", ".join(sorted(missing))}')
    removed = []
    for key, job in list(jobs.items()):
        if job.get('Label') in disabled:
            removed.append((key, job['Label']))
            del jobs[key]
    found = set()
    for job in jobs.values():
        if '_PanicOnCrash' in job:
            job['_PanicOnCrasX'] = job.pop('_PanicOnCrash')
        label = job.get('Label')
        if label in labels:
            job['StandardOutPath'] = '/dev/console'
            job['StandardErrorPath'] = '/dev/console'
            job.setdefault('EnvironmentVariables', {}).update(LOG_ENV)
            found.add(label)
    with open(dst, 'wb') as f:
        plistlib.dump(plist, f, fmt=plistlib.FMT_BINARY)
    for key, label in removed:
        print(f'removed LaunchDaemons dictionary entry {key!r}, Label {label!r}')
    print(f'{dst}: console logging for {", ".join(sorted(found))}')


if __name__ == '__main__':
    main()
