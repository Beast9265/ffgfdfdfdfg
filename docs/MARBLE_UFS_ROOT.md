# MARBLE read-only internal UFS root

## Physical baseline

The user reports the complete HFS RAMDisk userspace milestone on POCO F5:
RAMDisk property, md0/rmd0 creation, BSD root md0, IOMedia-less setRootMedia,
mockfs declining the non-Mach-O root, HFS mounting MarbleRoot, registered
hfs-627.100.6, /sbin/launchd exec, codesigning result 0, EL0 PID1 banner and
indefinite heartbeat. Kernel/scheduler/GIC/timer/SGI/BSD/root mount/exec/PID1
scheduling PASS. This supersedes older pending HFS observations in NOTES.md.
These are user physical observations, not an automated device test.

The user's later stage-0 UFS observation also supersedes the older unconfirmed
DEVACT entries: NOP OCS=0, READ_FLAG fDeviceInit=0, initial LUN0 TUR sense
02/04/02; DEVICE WLUN ACTIVE on LUN d0, CDB 1b0000001000 succeeds, LUN0
becomes ready, READ CAPACITY reports 4096-byte blocks, reads return valid MBR
AA55 / protective type EE, GPT header/entries and userdata discovery succeed.
No storage-sector writes occurred. Generic LUN0 START CDB 1b0100000100 was
rejected (05/24/00); it must never be retried by this driver.

## First physical XNU result

User-reported first physical XNU UFS boot (2026-10-22): no RAMDisk;
ADT PA 0x01d84000, register size 0x3000; MMIO 0xfffffe30062c0000;
contiguous DMA PA 0x843f44000 size 0x104000. CAP 0x1587031f,
VER 0x300, HCE 0x1, HCS 0x10f. NOP PASS; READ_FLAG fDeviceInit PASS,
value 0. Initial LUN0 TUR: OCS 0, transaction 0x21, response 0x01,
status 0x02, valid sense 02/04/02; result EIO (5). Device-WLUN ACTIVE
was NOT ATTEMPTED: the classifier incorrectly required response=0.
IOFindBSDRoot reported ufsroot0 unavailable: 5. These are user observations.

## Hardware audit against SWEET

The actual hardware source is shim/board.h plus shim/ufs.c and
shim/ufs_response.h, including its SHIM_MARBLE branches, rather than an assumed
SWEET controller state. Both boards use UFS_BASE=0x01d84000. The mapped register
aperture is 0x3000 bytes (same UFSHCI programming model); this is an MMIO mapping
extent, not a claim that all offsets were physically probed. Used offsets:
CAP 00, VER 08, IS 20, IE 24, HCS 30, HCE 34, UTRLBA/U 50/54, DBR 58,
CLR 5c, RSR 60. The physical MARBLE measurements are CAP=0x1587031f, VER=0x300.

ABL already enabled the host and established its link/device presence. The
shim verifies HCE.EN, HCS.DP and HCS.UTRLRDY, idle doorbell, stops the transfer
list, replaces its low/high physical base, runs it and checks readback before
submission. XNU uses that same model, additionally setting IE=0 for polling.
It does not reset/reinitialize PHY, clocks, regulators, link or UniPro.

MARBLE's proven data LUN is 0, blocks 4096 bytes. Only the gated whole-device
ACTIVE uses UPIU LUN d0. SWEET does not need this MARBLE readiness sequence.
MARBLE runs NOP, READ_FLAG fDeviceInit (must be zero), TUR; only a complete
valid decoded sense with OCS=0, transaction=0x21, CHECK CONDITION and exactly 02/04/02
permits one d0 ACTIVE. It then polls TUR for at most five seconds of command
budget; unexpected conditions stop. There is no generic LUN0 START fallback.
The physical response=1 is tolerated ONLY for this exact initializing condition,
matching stage-0's successful readiness path. ufs_scsi still returns EIO for it;
the readiness gate alone permits ACTIVE. ACTIVE, capacity, READ10, NOP and
READ_FLAG success validation remains unchanged. ACTIVE request and completion
fields are logged, with existing sense diagnostics; later reads gain no logs.

Stage-0 executes MMU-off with Device memory and DSB barriers, so it needs no
cache maintenance. XNU's cacheable DMA memory must be maintained explicitly;
no claim of hardware DMA coherency is made. MARBLE uses conservative PA-based
flush_dcache64 (clean+invalidate) on UTRL/UCD/data before and after transfers,
plus DSB SY. Optional SWEET cache/wait boot arguments are not parsed on MARBLE.

## Patch replay and ADT

Keep sweet_ufs.c and sweet_ufs_rootdev: both boards share the existing Qualcomm
transport, bounce/PRDT and BSD implementation. No marble_ufs.c copy exists.
All changes to generated XNU sources are appended in 0082, AFTER the unchanged
0028/0030/0034/0047/0054/0060/0069/0072/0077 patches. Replaying 0001..0081 and
strictly applying 0082 produces the final source. SWEET retains its original
write policy and services; preprocessing compares equal modulo whitespace,
concatenated string literals and __LINE__-derived names/diagnostics.

MARBLE ADT now has /marble-ufs:

- name = "marble-ufs" (NUL terminated)
- compatible = "qcom,ufshc" (NUL terminated)
- reg = two little-endian u64s: PA 0x01d84000, size 0x3000
- AAPL,phandle = generated u32

The node is an absolute physical mapping, outside /arm-io ranges. MARBLE
constants are explicit and tested against shim/board.h, even though they equal
SWEET today. The driver requires /marble-ufs/reg and uses ml_io_map; no fallback
SWEET address is hard-coded in the kernel. SWEET keeps /sweet-ufs, QEMU has no
UFS node. MARBLE's generated synthetic identity contains no device serial.

## Read-only guarantees

For MARBLE preprocessing removes ufs_write_blocks (WRITE10 opcode 2a),
ufs_sync_cache (35), the strategy write/merge branch, physio(B_WRITE),
ufsrw parsing/assignment and the entire SWEET persistent logging thread.
SWEET input/sample/touch/USB startup is also excluded from this MARBLE path.
A boot argument cannot enable writes. su.writable remains zero; FWRITE opens,
character writes and non-B_READ strategies return EROFS. Synchronization
ioctls return EROFS without a command. DKIOCISWRITABLE reports zero.

A second guard at SCSI submission permits only TUR 00, READ CAPACITY10 25,
READ10 28 on LUN0, plus the exact no-data gated d0 ACTIVE CDB above. There is
no WRITE10/SYNCHRONIZE CACHE command constructor compiled for MARBLE. The
separate management function constructs only NOP or READ_FLAG fDeviceInit;
there is no general query opcode argument and no SET/CLEAR/TOGGLE flag API.
MMIO/controller DMA writes are necessary to read storage; no path writes
filesystem or partition sectors. No rootrw=1 or ufsrw=1 is packaged.

All submissions verify the owned/running/idle transfer list before touching
shared descriptors. A timed-out command permanently poisons this boot's
transport, preventing reuse of DMA buffers even if cancellation is delayed.

DMA allocation: kmem_alloc_contig, PAGE_MASK alignment, size 0x104000;
UTRL offset 0, UCD 0x1000, 1 MiB bounce 0x4000. Compile-time assertions check
32-byte UTRDs, 1024-byte UTRL alignment, 128-byte UCD alignment, 4096-byte data
alignment and descriptor separation; runtime checks physical page alignment.
PRDT entries cover at most 256 KiB each (four entries). CAP.64AS is required
if any byte of the contiguous allocation exceeds 32-bit PA. Both base halves
and all PRDT address halves are programmed; never truncate high MARBLE RAM.

Capacity must report 4K and fit READ10. Reads reject zero/oversized counts,
READ10 LBA overflow and end-of-device crossing. GPT checks signature, header
size/current LBA/usable limits/header CRC, bounded entry count without integer
multiplication overflow, entry-array placement and CRC. Partition extent must
be ordered, within usable/device bounds and READ10-addressable. After selection,
every read is also constrained to that partition. BSD requests reject negative
or overflowing block numbers and partition-byte-range crossing before copying.
The BSD sector starts at 512 bytes (physical blocks 4096); supported block-size
ioctls retain existing behavior.

## Validation and expected physical result

Local: full 0001..0081 replay and strict 0082 check/apply; real generated-header
arm64 Mach-O compiles of sweet_ufs.c and IOKitBSDInit.cpp; SWEET preprocessing
equivalence; MARBLE preprocessing excludes all write/sync/log paths and ufsrw;
actual read/GPT host functions pass ASan/UBSan bounds/overflow/CRC/malformed-GPT
cases; actual readiness host function passes exact ACTIVE CDB/LUN, initial-ready
skip, unexpected-error stop, one activation only and five-second timeout.
The actual submission guard also passes 262,144 opcode/LUN/gate/direction
cases and rejects mutated ACTIVE CDBs and all WRITE10/SYNC requests.
Leak checking disabled because sandbox ptrace prevents LeakSanitizer; address
and undefined-behavior sanitizers remain enabled. Existing six MARBLE tests
pass including added UFS ADT assertions. git diff --check passes.
Local audit scripts/results: /tmp/ufs-{validate.py,static.py,host-check.py,
readiness-check.py,opcode-check.py,marble.i,preflight-map.txt}; compile objects/logs
/tmp/ufs-sweet_ufs.c.{o,log}, /tmp/ufs-IOKitBSDInit.cpp.{o,log}.

A full linked kernel cannot be built locally with the available Linux SDK;
the exact MARBLE Actions build supplies that validation before packaging.
Final linked-symbol/HFS/CNTP, actual sparse map and no-RAMDisk payload checks
are recorded in the active handoff after that exact run succeeds.
Old 0082 prefix is byte-identical: 16K/sparse MMU, allocator, CNTV-only/CNTP
skip, timer27/SGI1/GIC protections, CPU0/platform expert, HFS/MD5, missing-IOMedia
RAMDisk compatibility, codesigning/EL0 and framebuffer remain intact.

Final diagnostic command line:

    debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0

No --ramdisk, MarbleRoot, RAMDisk property or rd=md0. Default partition is
ufsroot=userdata. Expected new breadcrumbs include ADT/controller discovery,
MMIO, CAP/VER, readiness, UTRL allocation, NOP/query/TUR/ACTIVE if needed,
first READ10, validated GPT, "userdata", BSD devices and BSD root ufsroot0.
Major numbers are allocated by bdevsw_add, not hard-coded; normally major 1,
minor 0. HFS then attempts the actual existing partition. Unknown Volume
Signature/cannot mount root on Android/F2FS/encrypted userdata is EXPECTED.
Success for this test is userdata discovery and BSD root selection; no valid
HFS filesystem or userspace execution is required. Do not format/flash to fix it.

Automation stops after image verification. It never invokes fastboot or adb,
and never boots/reboots/writes the phone. The user manually boots the image.

## Verified diagnostic artifact

Build commit: `2ef4386a869373468ad31ac614206e7fb5367ecb`.
[Actions 39733746933](https://github.com/Beast9265/ios-marble/actions/runs/39733746933)
succeeded; exact head SHA and artifact checksum verified. Full linked kernel
has no undefined symbols, retains UFS/HFS, excludes write/sync/log functions.
Four executable sections contain zero CNTP instructions and one CNTV_CTL MSR.
Final payload segment-by-segment comparison, ADT UFS PA/no-RAMDisk checks,
160-page sparse-map audit and independent boot-v4 post-write checks all pass.
This original image produced the first physical XNU result above; stage-0 and HFS RAMDisk successes above
are user observations. No physical phone commands were run.

SHA256:

```text
kernel   46316df9660a03575cf70b71395ce7b830cf9ea012c8deefb19dc6b25f032912
payload  642f1064efbc302121fc2cfe907239116f8e050ea629c2f23e3bde92670efedf
boot     a94b786b5ecf634971697a47edb762672883cee75714e77903d19c06eee9b2bd
```

Final image: `shim/out/marble-xnu/latest-marble-xnu.img`.
The Android boot-v4 generic-ramdisk field transports only the kernel/ADT payload
and locator footer; it contains no XNU root RAMDisk or userspace image.
Documentation-only follow-up commits do not change this kernel provenance.

Manual command:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```
