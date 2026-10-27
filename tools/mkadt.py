#!/usr/bin/env python3
"""Build the minimal Apple Device Tree that the SWEET xnu needs to boot.

Only what the early boot path actually reads (see NOTES.md); every MMIO
address comes from the sweet live FDT. Usage:  mkadt.py OUT.adt [--dump] [--qemu | --highmem | --marble]
"""
import argparse, hashlib, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adt  # noqa: E402

# Kernel-managed RAM: above every Qualcomm XPU carve-out (see NOTES.md)
PHYS_BASE = 0xb0000000
MEM_SIZE = 0x4d000000
# --highmem (phone only): the whole upper DDR bank. The live FDT memory node is
# <0x80000000 2G>, <0x1_00000000 0xfcc00000>; every fixed reserved-memory
# carve-out is in the low bank and the dynamic pools are limited below 4G.
HIGH_PHYS_BASE = 0x100000000
HIGH_MEM_SIZE = 0xfcc00000
# /arm-io children are relative to this; it must not be 0 (serial_init bails)
SOC_BASE = 0x01000000

GICD, GICD_SIZE = 0x17a00000, 0x10000
GICR, GICR_SIZE = 0x17a60000, 0x100000
FB, FB_SIZE = 0x9c000000, 0x1700000
SWEET_ECID = 0x5357454554000001  # 'SWEET' + 1, synthetic
FB_W, FB_H, FB_STRIDE = 1080, 2400, 1080 * 4
# Internal UFS host (ufshc@1d84000 "ufs_mem"); QEMU virt has none
UFS, UFS_SIZE = 0x01d84000, 0x3000
# MARBLE shim/board.h independently uses the same host PA. Keep explicit
# board values so future SWEET changes cannot silently relocate MARBLE.
# 0x3000 is the mapped UFSHCI register aperture; only offsets 0x00..0x60 used.
MARBLE_UFS, MARBLE_UFS_SIZE = 0x01d84000, 0x3000
TIMEBASE = 19200000
VTIMER_INTID = 19
# QEMU virt (-M virt,gic-version=3 -cpu cortex-a76): GICD/GICR and the generic timer's CNTFRQ
QEMU_GICD, QEMU_GICR, QEMU_TIMEBASE = 0x08000000, 0x080a0000, 62500000
QEMU_VTIMER_INTID = 27

BOOT_MANIFEST_HASH = hashlib.sha384(b'sweet boot manifest').digest()

# The iOS userland is the iPhone X (iPhone10,3 / D22AP) IPSW. MobileGestalt
# derives product type, device class, home-button-less UI, artwork etc. from
# the root identity and /product of the real D22AP device tree. That tree is
# an Apple artifact (kept out of git): extract it from the IPSW with
#   tools/remotezip.py URL DeviceTree.d22ap.im4p DIR
#   ipsw img4 im4p extract DIR/Firmware/all_flash/DeviceTree.d22ap.im4p -o d22ap.adt
D22AP_ADT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../research/ipsw-x/d22ap.adt')


def d22ap_product(path=D22AP_ADT):
    """/product properties of the real D22AP tree, without the syscfg
    placeholders iBoot would fill in (flag bit set) and the node bookkeeping."""
    if not os.path.exists(path):
        print(f'warning: {path} missing, no /product node', file=sys.stderr)
        return None
    with open(path, 'rb') as source:
        root, _ = adt.parse(source.read())
    for c in root.children:
        if dict((k, v) for k, f, v in c.props).get('name') == b'product\0':
            return [(k, v) for k, f, v in c.props if not f and k not in ('name', 'AAPL,phandle')]
    raise SystemExit(f'{path}: no /product node')

u32 = lambda *v: struct.pack('<%dI' % len(v), *v)
u64 = lambda *v: struct.pack('<%dQ' % len(v), *v)
cstr = lambda s: s.encode() + b'\0'


def node(name, props=(), children=()):
    n = adt.Node()
    n.props = [('name', 0, cstr(name))] + [(k, 0, v) for k, v in props]
    n.children = list(children)
    return n


MARBLE_GPU_FIRMWARE = ('gmu_gen70000.bin', 'a730_sqe.fw', 'a730_zap.mdt')


def load_marble_gpu_firmware(directory):
    """Return an ADT node containing an explicitly supplied stock firmware set.

    The generated ADT is an ephemeral boot artifact.  Firmware is never copied
    into the repository, and every blob carries its SHA-256 for kernel-side
    identity verification before a future loader may consume it.
    """
    if directory is None:
        return None
    props = [('chip-id', u32(0x07030002))]
    for filename in MARBLE_GPU_FIRMWARE:
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            raise ValueError(f'missing MARBLE GPU firmware: {path}')
        with open(path, 'rb') as source:
            image = source.read()
        if not image:
            raise ValueError(f'empty MARBLE GPU firmware: {path}')
        key = filename.replace('.', '-')
        props += [(key, image), (key + '-sha256', hashlib.sha256(image).digest())]
    return node('a725-firmware', props)


def build(seed=None, qemu=False, highmem=False, marble=False, marble_cpus=1,
          marble_gpu_firmware=None):
    """qemu=True: same tree, but with QEMU virt's GIC addresses and CNTFRQ (tools/qemu-sweet.py)."""
    phys_base, mem_size = (HIGH_PHYS_BASE, HIGH_MEM_SIZE) if highmem else (PHYS_BASE, MEM_SIZE)
    gicd, gicr, timebase = (QEMU_GICD, QEMU_GICR, QEMU_TIMEBASE) if qemu else (GICD, GICR, TIMEBASE)
    if marble:
        if qemu or highmem:
            raise ValueError('--marble cannot be combined with --qemu/--highmem')
        phys_base, mem_size = 0x840000000, 0x100000000
        gicd, gicr = 0x17100000, 0x17180000
        if marble_cpus not in (1, 4, 8):
            raise ValueError('MARBLE ADT CPU count must be 1, 4, or 8')
        gpu_firmware = load_marble_gpu_firmware(marble_gpu_firmware)
    elif marble_cpus != 1:
        raise ValueError('--marble-cpus requires --marble')
    elif marble_gpu_firmware is not None:
        raise ValueError('--marble-gpu-firmware requires --marble')
    else:
        gpu_firmware = None
    seed = seed if seed is not None else os.urandom(64)
    phandle = iter(range(1, 1000))
    ph = lambda: ('AAPL,phandle', u32(next(phandle)))

    chosen = node('chosen', [
        ph(),
        ('dram-base', u64(phys_base)),
        ('dram-size', u64(mem_size)),
        ('random-seed', seed),
        ('debug-enabled', u32(1)),
        ('firmware-version', cstr('marble-shim' if marble else 'sweet-shim')),
        ('system-firmware-version', cstr('marble-shim' if marble else 'sweet-shim')),
        # iBoot's SHA-384 of the boot manifest; /sbin/mount -P 1 exits unless
        # it exists (bind mounts /private/preboot/<hex>/usr/standalone/firmware,
        # tolerating a missing directory). Fixed stand-in value.
        ('boot-manifest-hash', BOOT_MANIFEST_HASH),
        # libimg4 (cryptexd) aborts "failed to get crypto algorithm" without
        # it; real A11+ device trees say sha2-384.
        ('crypto-hash-method', cstr('sha2-384')),
        # MobileGestalt's screen class: display-scale (u32, default 0) comes
        # from /chosen, the pixel size from IOMobileFramebuffer. Scale 0 makes
        # SpringBoard's FBSDisplayMode "infxinf@0x" invalid. 1080x2400 @3x =
        # 360x800 points (like iPhone X class devices).
        ('display-scale', u32(3)),
        # XNU derives IOPlatformUUID (gethostuuid) from these on arm; without
        # them CFPreferences cannot use kCFPreferencesCurrentHost (no ByHost
        # files), so e.g. DataMigration never records LastSystemVersion and
        # migrates on every boot. Synthetic ECID (not the phone's); chip-id
        # of the A11 that the iPhone X userland expects.
        ('unique-chip-id', struct.pack('<Q', 0x4d4152424c450001 if marble else SWEET_ECID)),
        ('chip-id', u32(0x8015)),
        # Security status as on a dev-fused, undemoted board (tuple 0,0,1,1):
        # MobileGestalt reads these from /chosen, and mobileactivationd's
        # DeviceType then takes its native "Hactivation" branch (state
        # Activated without an activation record; no SEP, no baseband here).
        ('certificate-production-status', u32(0)),
        ('effective-production-status-ap', u32(0)),
        ('certificate-security-mode', u32(1)),
        ('effective-security-mode-sep', u32(1)),
    ], [node('memory-map', [ph()]),
        # Local boot policy (kern_csr.c): SIP relaxed like `csrutil disable`
        # (lp-sip0: untrusted kexts, unrestricted FS, task_for_pid, kernel
        # debugger, dtrace, nvram), lp-sip1: unauthenticated (unsealed) root.
        # The iOS shared cache is in no trust cache, so dyld can only map it
        # with CSR_ALLOW_UNRESTRICTED_FS (vm_unix.c shared region checks).
        node('asmb', [ph(), ('lp-sip0', u64(0x6f)), ('lp-sip1', u32(1))])])

    # SWEET and MARBLE expose their physical cores in MPIDR order as one
    # homogeneous cluster. MARBLE keeps a one-core default for baseline builds
    # and requires an explicit four- or eight-node test topology.
    # QEMU retains its original single-CPU tree: its MPIDRs differ from sweet.
    if marble:
        cpu_table = [
            (0x000, 1804800000), (0x100, 1804800000),
            (0x200, 1804800000), (0x300, 1804800000),
            (0x400, 2496000000), (0x500, 2496000000),
            (0x600, 2496000000), (0x700, 2918400000),
        ][:marble_cpus]
    elif qemu:
        cpu_table = [(0, 1804800000)]
    else:
        cpu_table = [(core << 8, 2304000000 if core >= 6 else 1804800000)
                     for core in range(8)]
    cpu_nodes = []
    for core, (mpidr, clock) in enumerate(cpu_table):
        cpu_nodes.append(node(f'cpu{core}', [
            ph(),
            ('device_type', cstr('cpu')),
            ('compatible', cstr('qcom,marble-cpu' if marble else 'qcom,kryo470') + cstr('ARM,v8')),
            ('reg', u32(mpidr)),  # actual MPIDR Aff1:Aff0, NOT logical ID
            ('cpu-id', u32(core)),   # descriptive: XNU assigns IDs by DT order
            ('cluster-id', u32(0)),  # descriptive; see ml_parse_cpu_topology
            ('cluster-type', u32(0)),  # homogeneous CLUSTER_TYPE_SMP, not AMP
            ('die-cluster-id', u32(0)),
            ('cluster-core-id', u32(core)),
            ('l2-cache-id', u32(core)),  # distinct per-core L2 nodes in live FDT
            ('l3-cache-id', u32(0)),     # shared L3
            ('state', cstr('running' if core == 0 else 'stopped')),
            ('timebase-frequency', u32(timebase)),
            ('clock-frequency', u32(clock)),
            ('bus-frequency', u32(100000000)),
            ('memory-frequency', u32(1866000000)),
            ('peripheral-frequency', u32(timebase)),
            ('fixed-frequency', u32(timebase)),
        ]))
    cpus = node('cpus', [ph(), ('#address-cells', u32(1)),
                         ('#size-cells', u32(0))], cpu_nodes)

    gic = node('gic', [
        ph(),
        ('compatible', cstr('arm,gic-v3')),
        ('interrupt-controller', b''),
        ('virtual-timer-intid', u32(27 if marble else (QEMU_VTIMER_INTID if qemu else VTIMER_INTID))),
        ('reg', u64(gicd - SOC_BASE, GICD_SIZE, gicr - SOC_BASE, 0x200000 if marble else GICR_SIZE)),
    ])
    arm_io = node('arm-io', [
        ph(),
        ('device_type', cstr('sweet-io')),
        ('compatible', cstr('sweet-io') + cstr('arm-io')),
        ('#address-cells', u32(2)),
        ('#size-cells', u32(2)),
        ('ranges', u64(0, SOC_BASE, 0x100000000 - SOC_BASE)),
    ], [gic,
        # No hardware: watchdogd checks IODeviceTree:/arm-io/wdt for no-pmu and
        # otherwise crashes trying to set the PMU boot stage (customer builds
        # ignore the -wdt_no_pmu boot-arg).
        node('wdt', [ph(), ('no-pmu', u32(1))]),
        # Main display: IOMobileFramebuffer.framework counts /arm-io children
        # with this device_type and reads the canvas size from the node
        # (the presented iPhone X size, see SweetFramebuffer.cpp);
        # the kernel's AppleCLCD matches the compatible string.
        node('disp0', [
            ph(),
            ('device_type', cstr('display-subsystem')),
            ('compatible', cstr('sweet,display')),
            ('canvas-width', u32(1125)),
            ('canvas-height', u32(2436)),
        ])])

    if marble:
        # Retain only the GIC and shared AppleCLCD display nub on MARBLE.
        # No SWEET watchdog, input, or other hardware children.
        arm_io.children = [gic, arm_io.children[2]] + ([gpu_firmware] if gpu_firmware else [])

    fbcon = node('sweet-fbcon', [
        ph(),
        ('reg', u64(0xb8000000, 0x009e3400) if marble else u64(FB, FB_SIZE)),
        ('width', u32(FB_W)),
        ('height', u32(FB_H)),
        ('stride', u32(FB_STRIDE)),
    ])

    # bsd/dev/sweet_ufs.c: the UFS host ABL leaves running (absolute physical reg).
    ufs = node('marble-ufs' if marble else 'sweet-ufs', [
        ph(),
        ('compatible', cstr('qcom,ufshc')),
        ('reg', u64(MARBLE_UFS, MARBLE_UFS_SIZE) if marble else u64(UFS, UFS_SIZE)),
    ])

    # pmap_compute_max_asids requires the node even when no overrides are set.
    # An absent pmap-max-asids property selects XNU's own MAX_ASIDS default.
    # No effaceable storage: keybagd then reads /private/var/keybags/systembag.kb
    # as a plain plist instead of decrypting it with the effaceable key.
    defaults = node('defaults', [ph(), ('no-effaceable-storage', u32(1))])

    # MobileGestalt HomeButtonType = IODeviceTree:/buttons home-button-type
    # (D22AP: 2, no Home button; absent = 0 = Home-button device).
    buttons = node('buttons', [
        ph(),
        ('button-names', cstr('volup') + cstr('voldown') + cstr('hold')),
        ('home-button-type', u32(2)),
        ('opposed-power-vol-buttons', u32(1)),
    ])

    product_props = d22ap_product()
    if marble:
        # CoreUI dataWithName: gets ArtworkTraits from IODeviceTree:/product,
        # independently of the display geometry. Without its phone idiom,
        # the real iPhone X bounding-path DATA rendition cannot match.
        required = {
            'artwork-device-idiom': cstr('phone'),
            'artwork-device-subtype': u32(2436),
            'artwork-scale-factor': u32(3),
        }
        actual = dict(product_props or [])
        if any(actual.get(key) != value for key, value in required.items()):
            raise ValueError('MARBLE requires the original D22AP /product artwork metadata; '
                             f'restore {D22AP_ADT} from the pinned 20H392 DeviceTree')
    product = [node('product', [ph()] + product_props)] if product_props else []

    # Identity of the iPhone X whose userland runs here: compatible[0] is
    # hw.model/hw.target (D22AP), model is hw.machine/hw.product
    # (iPhone10,3). 'xiaomi,sweet' stays for SweetPlatformExpert matching.
    return node('device-tree', [
        ph(),
        ('compatible', cstr('D22AP') + cstr('iPhone10,3') + cstr('xiaomi,marble' if marble else 'xiaomi,sweet') + cstr('qcom,sm7475' if marble else 'qcom,sm7150') + cstr('AppleARM')),
        ('model', cstr('iPhone10,3')),
        ('target-type', cstr('D22')),
        ('target-sub-type', cstr('D22AP')),
        ('manufacturer', cstr('Apple Inc.')),
        ('#address-cells', u32(2)),
        ('#size-cells', u32(2)),
    ], [chosen, defaults, cpus, arm_io, fbcon, buttons] + product + ([] if qemu else [ufs]))


def cpu_topology(blob):
    root, _ = adt.parse(blob)
    cpus = next(child for child in root.children if child.prop('name') == b'cpus\0')
    return [(struct.unpack('<I', cpu.prop('reg'))[0],
             struct.unpack('<I', cpu.prop('clock-frequency'))[0])
            for cpu in cpus.children]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--dump', action='store_true')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--qemu', action='store_true')
    modes.add_argument('--highmem', action='store_true')
    modes.add_argument('--marble', action='store_true')
    parser.add_argument('--marble-cpus', type=int, choices=(1, 4, 8), default=1)
    parser.add_argument('--marble-gpu-firmware', metavar='DIR',
                        help='embed the three stock A725 firmware files from DIR')
    args = parser.parse_args()
    root = build(qemu=args.qemu, highmem=args.highmem, marble=args.marble,
                 marble_cpus=args.marble_cpus,
                 marble_gpu_firmware=args.marble_gpu_firmware)
    blob = adt.serialize(root)
    topology = cpu_topology(blob)
    expected = args.marble_cpus if args.marble else (1 if args.qemu else 8)
    if len(topology) != expected or [mpidr for mpidr, _ in topology] != [i << 8 for i in range(expected)]:
        raise SystemExit(f'invalid CPU topology: {topology!r}')
    with open(args.output, 'wb') as output:
        output.write(blob)
    print('CPU topology: ' + ', '.join(
        f'cpu{i}=MPIDR0x{mpidr:03x}@{clock}Hz'
        for i, (mpidr, clock) in enumerate(topology)), file=sys.stderr)
    if args.dump:
        adt.dump(adt.parse(blob)[0])
    print(f'{args.output}: {len(blob)} bytes', file=sys.stderr)
