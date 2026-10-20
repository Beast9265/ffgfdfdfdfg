#!/usr/bin/env python3
"""Boot the diagnostic shim (BOARD=qemu shim/build.sh) on QEMU virt and save its screen.

The shim is entered like a Linux Image (EL1, x0 = DTB, initrd in /chosen),
as ABL does on the phone. Without a SWEETXNU payload it runs its
diagnostics; with --cpu cortex-a53 the ISA line must read lse=0 pan=0.

  qemu-shim.py shim/out/Image OUTDIR [--cpu cortex-a53] [--smp 8] [--secs 8] [--initrd FILE]
"""
import argparse, json, os, socket, struct, subprocess, sys, time, zlib

FB_BASE, FB_W, FB_H = 0x5c000000, 1080, 2340
FB_STRIDE = FB_W * 4


def write_png(path, raw):
    rows = []
    for y in range(FB_H):
        line = raw[y * FB_STRIDE:(y + 1) * FB_STRIDE]
        rgb = bytearray(FB_W * 3)  # a8r8g8b8 little endian = B G R A in memory
        rgb[0::3], rgb[1::3], rgb[2::3] = line[2::4], line[1::4], line[0::4]
        rows.append(b'\0' + bytes(rgb))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', FB_W, FB_H, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(b''.join(rows), 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def qmp(sock_path, *cmds):
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock_path)
    f = s.makefile('rw')
    f.readline()

    def call(execute, **args):
        f.write(json.dumps({'execute': execute, 'arguments': args}) + '\n')
        f.flush()
        while True:
            r = json.loads(f.readline())
            if 'return' in r or 'error' in r:
                return r

    call('qmp_capabilities')
    out = [call(c, **a) for c, a in cmds]
    s.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('image')
    ap.add_argument('outdir')
    ap.add_argument('--cpu', default='cortex-a53')
    ap.add_argument('--smp', type=int, default=8)
    ap.add_argument('--secs', type=float, default=8)
    ap.add_argument('--initrd', help='ramdisk (default: none; the shim then reports "no initrd")')
    a = ap.parse_args()

    out = os.path.abspath(a.outdir)
    os.makedirs(out, exist_ok=True)
    mon = f'{out}/qmp.sock'
    if os.path.exists(mon):
        os.unlink(mon)
    cmd = ['qemu-system-aarch64', '-M', 'virt,gic-version=3', '-cpu', a.cpu, '-smp', str(a.smp), '-m', '4G',
           '-nographic', '-serial', 'none', '-monitor', 'none', '-qmp', f'unix:{mon},server,nowait',
           '-d', 'int,guest_errors,unimp', '-D', f'{out}/qemu.log', '-no-reboot', '-kernel', a.image]
    if a.initrd:
        cmd += ['-initrd', a.initrd]
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while p.poll() is None and time.time() - t0 < a.secs:
            time.sleep(0.2)
        if p.poll() is not None:
            print(f'qemu exited early: {p.returncode}', file=sys.stderr)
            return 1
        _, regs, _ = qmp(mon, ('stop', {}), ('human-monitor-command', {'command-line': 'info registers'}),
                         ('pmemsave', {'val': FB_BASE, 'size': FB_STRIDE * FB_H, 'filename': f'{out}/fb.raw'}))
        open(f'{out}/regs.txt', 'w').write(regs.get('return', str(regs)))
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()
    write_png(f'{out}/fb.png', open(f'{out}/fb.raw', 'rb').read())
    os.unlink(f'{out}/fb.raw')
    print(f'{out}/fb.png  {out}/regs.txt  {out}/qemu.log', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
