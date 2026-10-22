# MARBLE HFS RAMDisk root

## Physical baseline — 2026-10-22

**MARBLE PHYSICAL PID1 SUCCESS** (user-reported physical observation):
`mockfs mount result 0`, `PID 1 codesigning result 0`,
`*** MARBLE USERSPACE: PID 1 RUNNING ***`, and PID 1 heartbeat sustained
indefinitely. RAMDisk discovery, md0, BSD root selection, missing-IOMedia
compatibility, mockfs mount, exec, code signing, EL0 and scheduling are proven.
This iteration changes the RAMDisk contents to HFS; its physical result is
pending a manual boot. No device commands or physical-storage changes.

## Shared implementation

Apple OSS **hfs-627.100.6**, immutable commit
`31d5ec238dfab485e78a9a30b8b92d13e8914f03`, paired with
xnu-8796.141.3 / macOS 13.5. Reuse `bsd/sweet_hfs`, its compatibility header,
40 files/config entries, registration and 0027 BearSSL MD5 implementation.
No second HFS source tree and no downloaded sources committed.

Audit found `0026-stage-hfs.sh` already accepted SWEET **and MARBLE** before
this task. Its only changes here clarify the shared purpose and report the
actual machine. Staging runs before all source patches: an 0082 source patch
cannot fetch/stage sources retroactively. Keep the existing early shared gate
and pinned revision. Fresh MARBLE staging was exercised successfully locally;
only xcrun's SDK-path lookup used a Linux test shim pointing at the existing
SDK TargetConditionals.h. CI uses real xcrun.

0082 now adds `sweet_hfs` to MARBLE FILESYS_BASE. Its earlier shared
Makefile.template guard already enables HFS per-file flags and portable
MD5/SHA/AES for MARBLE. No additional compatibility guard generalization is
necessary. SWEET-only dirty writable-volume and Linux hard-link exceptions
remain SWEET-only; neither is required for this clean read-only tiny root.
SWEET's config and preprocessed registration/mockfs behavior are unchanged.
A conditional MARBLE HFS registration breadcrumb identifies the shared driver.

0026's `mockfs_check_macho` is unconditional and already active for MARBLE.
It reads the first sector, accepts only Mach-O/fat magic, releases its buffer,
and returns EINVAL otherwise. This image has zero boot blocks and HFSX magic
at byte 1024. Mockfs declines it before allocating mount state; mountroot
continues to the dynamically registered HFS filesystem. MARBLE's existing
failure diagnostic now says `mockfs declined non-Mach-O root`.

`corecrypto_md5.c` already selects BearSSL for SWEET || MARBLE in 0082.
Local objects define MD5Init/Update/Final and import br_md5_init/update/out;
`sweet_md5.c` supplies these and the dec32le/enc32le objects supply its helpers.
No g_crypto_funcs dependency in that wrapper, no hardware crypto changes,
and SHA/AES code remains identical.

## Root builder

```
clang -target arm64-apple-ios16.0 -DMARBLE_INIT -c tools/sweet-init.S \
  -o shim/out/marble-xnu/marble-init.o
python3 tools/mkinit.py shim/out/marble-xnu/marble-init.o \
  shim/out/marble-xnu/marble-init
python3 tools/mkmarble-test-root.py shim/out/marble-xnu/marble-init \
  shim/out/marble-xnu/MarbleRoot.img
```

Requires hfsprogs `mkfs.hfsplus`, `fsck.hfsplus`, and libdmg-hfsplus `hfsplus`.
Override paths with `MKFS_HFSPLUS`, `FSCK_HFSPLUS`, `HFSPLUS`. Local validation
used rbrito/pkg-hfsprogs commit `1b7634dc22420d9e5b00b77962a58d29b851bfef`
with its Debian patch series, clang/fcommon and obsolete sys/sysctl.h include
removed (Linux calls are already excluded); and planetbeing/libdmg-hfsplus
commit `7ac55ec64c96f7800d9818ce64c79670e7f02b67`. Local tool paths are
`/tmp/marble-hfsprogs/{newfs_hfs.tproj/newfs_hfs,fsck_hfs.tproj/fsck_hfs}`
and `/tmp/marble-libdmg/build/hfs/hfsplus`. These are host utilities, separate
from the exact Apple kernel HFS revision above. No mount, sudo,
block device or Apple userland is required. Builder refuses existing output,
uses an exclusive temporary regular file and atomically installs the result.
The pipeline regenerates this image after rebuilding init following CI download.

16 MiB, case-sensitive HFS+ (HFSX), label MarbleRoot, clean/non-journaled for
read-only RAMDisk boot. Exact contents: `/`, `/sbin`, `/sbin/launchd`, `/dev`.
All owned by root:wheel, mode 0755. Init is the same signed static Mach-O as
the proven mockfs root. Its first instructions align SP via `mov x9,sp;
and x9,x9,#~15; mov sp,x9` before stack access, preserving the historical
0027 physical SIGBUS fix.

Builder normalizes catalog/header dates, volume ID and write count, checks
catalog contents/modes/owners and contiguous launchd extent bytes, extracts
launchd independently through hfsplus and compares bytes, and runs
`fsck.hfsplus -fn` before and after extraction. Two independent builds produced
identical SHA256 (same host tool versions):

- init: `f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b`
- root: `467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a`

## Validation and packaging

Local PASS: full reverse/replay 0001..0081 and strict `git apply
--whitespace=error` check/apply of 0082; all 40 HFS arm64 units using real
kernel headers; MD5 wrapper and three provider objects; SWEET registration
and mockfs preprocessing byte-identical; hardware/MMU/timer/GIC and crypto
sources unchanged; six existing MARBLE/package tests; shell syntax and diff
checks. Logs `/tmp/hfs-{compile,validation}.log`, objects `/tmp/hfs-objs`.
Preflight packing with the prior kernel passes exact image embedding,
RAMDisk/ADT placement, rd=md0, sparse aliases and the 160-page allocator arena
(`/tmp/hfs-preflight-map.txt`). New full kernel link and final audit results
are recorded in NOTES.md after the exact CI run.

Pipeline invocation (stage only intentional source/docs first):

```
tools/marble-ci-build.sh \
  --ramdisk shim/out/marble-xnu/MarbleRoot.img \
  --cmdline-extra 'rd=md0' 'xnu: enable HFS ramdisk root on marble'
```

Retains `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=md0`.
Uses exact commit's CI kernel, regenerated MARBLE ADT, `mkpayload.py --ramdisk`,
BOARD=marble-xnu, stock boot_a repack and boot-v4 inspection. No rootrw,
ufsrw, rd=ufsroot0, UFS driver changes or storage operations.

Expected manual physical result: BSD root md0; HFS mounts MarbleRoot;
`/sbin/launchd` executes; MARBLE PID 1 banner and sustained heartbeat.
A host build/audit is not proof of that physical result.

## Exact completed build

Build commit `00e9810ed9f6b44768c781f2c5e56af8fefe9c55`;
[Actions 39731873003](https://github.com/Beast9265/ios-marble/actions/runs/39731873003)
succeeded. CI log confirms all 40 HFS units compiled and exact pinned staging.
Linked kernel has zero undefined symbols and all HFS/MD5 provider symbols.
Executable instruction scan: four sections, zero physical CNTP instructions,
one CNTV_CTL MSR. Final exact map audit passes with RAMDisk
`[0x842128000,0x843128000)`, ADT `0x843128000`, boot_args `0x84312c000`,
top `0x843130000`, allocator `[0x843130000,0x8433b0000)`.
Post-CI root regenerated identically, fsck and extracted init checks passed.
Boot-v4 repack/inspect and independent post-write bytes/padding checks passed.

```
Kernel SHA256 721c31711460cebefc9dc0fca1adf9a02c78fce63c8b6aa7a267e3715168bd2a
Test init SHA256 f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
HFS root SHA256 467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a
Payload SHA256 871dfbfa40e96e9ac9d7453b1aaff973eeb5318ce16cd05c9aa9e70d0afb2f26
Boot SHA256 00dc9f0fd6af2891ef15ac4e8dc26ffe53702fbe4b5330f66fbe70400e21420a
```

Final image: `shim/out/marble-xnu/latest-marble-xnu.img`.
No device interaction; HFS physical result remains pending.

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```
