#!/bin/sh
# Host-only receiver. Run manually with sudo; never boots or flashes a phone.
set -eu
if [ "${1:-}" = -h ] || [ "${1:-}" = --help ]; then
    echo "Usage: sudo $0 [--ping] [LOGFILE]"
    echo "Wait for Marble iOS USB debug CDC-ECM, configure 192.168.7.1/24, save UDP5140."
    echo "Requires Linux, Python3, iproute2, root; NetworkManager and ping are optional."
    exit 0
fi
command -v python3 >/dev/null
command -v ip >/dev/null
exec python3 - "$@" <<'PY'
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--ping', action='store_true')
parser.add_argument('logfile', nargs='?')
args = parser.parse_args()
if os.geteuid() != 0:
    parser.error('run with sudo: only the matched MARBLE USB interface is configured')
# Listen BEFORE link/address setup so first UDP backlog packets are retained.
receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver.bind(('0.0.0.0', 5140))
receiver.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
log = None
if args.logfile:
    path = Path(args.logfile).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    log = path.open('ab', buffering=0)
print('Waiting for MARBLE CDC-ECM (UDP5140 listener ready)...', file=sys.stderr, flush=True)

def matching_interfaces():
    result = []
    for interface in Path('/sys/class/net').iterdir():
        try:
            if interface.joinpath('address').read_text().strip().lower() != '02:00:5e:77:ee:01':
                continue
            device = interface.joinpath('device').resolve(strict=True)
            for parent in [device, *device.parents]:
                product = parent / 'product'
                manufacturer = parent / 'manufacturer'
                if product.exists() and manufacturer.exists():
                    if product.read_text().strip() == 'Marble iOS USB debug' and manufacturer.read_text().strip() == 'ios-marble':
                        result.append(interface.name)
                    break
        except (OSError, ValueError):
            continue
    return result

while True:
    matches = matching_interfaces()
    if len(matches) > 1:
        raise SystemExit('Multiple MARBLE USB interfaces: refusing ambiguous host configuration')
    if matches:
        interface = matches[0]
        break
    time.sleep(1)
if shutil.which('nmcli'):
    # Temporary per-device ownership; never changes other interfaces/profiles.
    subprocess.run(['nmcli', 'device', 'set', interface, 'managed', 'no'], check=False)
subprocess.run(['ip', 'address', 'replace', '192.168.7.1/24', 'dev', interface], check=True)
subprocess.run(['ip', 'link', 'set', interface, 'up'], check=True)
print(f'{interface}: 192.168.7.1/24 <-> 192.168.7.2; saving live UDP5140', file=sys.stderr, flush=True)
# Trigger ARP from the assigned IPv4 address. The kernel logger waits for it
# before consuming its backlog. No daemon/root change on the phone is needed.
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
    probe.bind(('192.168.7.1', 0))
    probe.sendto(b'', ('192.168.7.2', 9))
if args.ping:
    if shutil.which('ping'):
        subprocess.Popen(['ping', '-c', '3', '-W', '2', '192.168.7.2'], stdout=sys.stderr, stderr=sys.stderr)
    else:
        print('ping not installed; UDP capture continues', file=sys.stderr)
try:
    while True:
        data, peer = receiver.recvfrom(65535)
        if peer[0] != '192.168.7.2':
            continue
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        if log:
            log.write(data)
except KeyboardInterrupt:
    pass
finally:
    if log:
        log.close()
    receiver.close()
PY
