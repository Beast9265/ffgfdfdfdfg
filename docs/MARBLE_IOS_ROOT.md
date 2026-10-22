# MARBLE first real iOS root

## Active handoff: MARBLE AppleKeyStore / launchd cache transition (2026-10-22)

User physical milestone on e5dc3809 / Actions39764011216:
writable internal UFS PASS; journaled HFS PASS; rootrw PASS; fsck PASS;
mount-phase-1/2 PASS; CoreCrypto userspace FIPS POST all tests PASSED;
keybag task entered PASS; AppleKeyStore MISSING; system bag load FAIL.
keybagd reported missing options entry and recovery reboot; HFS synced/unmounted.
This supersedes prior pending writable-root statements. User reports latest
journaled root freshly flashed; no root rebuild or device interaction needed.

Full reverse/replay0001..0081 and strict0082 PASS. Final SweetKeyStore.cpp
exists, files.arm64 includes it optional iokitcpp, but SWEET guard excluded
MARBLE; AppleKeyStore personality was also inside SWEET-only guard.
Later0043/0055 additions retained.0082 alone now extends the implementation
and ONLY its personality to SWEET || MARBLE; no watchdog or other service port.
Class names AppleKeyStore/AppleKeyStoreUserClient retained; shared implementation
uses board-specific diagnostic prefix. All enum selectors retained:
0,2,3,4,5,6,7,9,10,11,12,13,14,17,26,27,35,55,101,102,103.
Implemented selector cases unchanged:0 succeeds;14 with >=1 output scalar
returns system handle0 and success; unknown/unimplemented cases unsupported.
0039 default-off coredump guard extended only to MARBLE; sysctl retained.
MARBLE actual CI-header arm64 compiles PASS: SweetKeyStore.cpp,
KernelConfigTables.cpp, kern_core.c. SWEET/BCM2837/T8103 preprocessed tokens
unchanged (adjacent string literals normalized). Logs/objects /tmp/aks-*.
Generated /tmp/aks-marble.adt confirms /defaults/no-effaceable-storage u32(1).
mkiosroot.sh149..153 already installs root:root keybags directory0700 and
systembag.kb0600 with KeyBagKeys plist. Builder unchanged; root NOT rebuilt.
UFS/write safety/HFS/AMFI/hardware code unchanged by this experiment.

Final cmdline (NO RAMDisk):
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1
The last arg skips cache-loader dependency on missing AppleMobileFileIntegrity
IOService; built-in AMFI MAC policy retained. Expected, not physically proven:
AKS registration, keybagd selectors0/14, System Keybag loaded, cache loader
proceeds to LaunchDaemons. Watchdog remains a possible later wall.
Full kernel link/exact CI/artifact/package validation pending below.
Unrelated iosroot-sparse.sh mode change and bootstrap breadcrumbs preserved.
No fastboot/adb, root rebuild, userdata flash, or phone interaction.


## Active handoff: MARBLE guarded writable root (2026-10-22)

User's physical result on previous e541dfdc / Actions39761856910:
- Apple launchd PASS; ondemand mode PASS; fsck boot task PASS.
- CS_SIGNED / CS_PLATFORM_BINARY / platform binary policy PASS.
- mount-phase-1 entered PASS; root remount FAIL EROFS.
- boot-manifest-hash PASS (mount constructs /private/preboot/5CBE3601... path).
- bindfs compiled PASS (MASTER.arm64.marble); firmware lookup ENOENT2.
Do not patch bindfs: isolate successful writable root first. No
launchd_unsecure_cache, RAMDisk, new write implementation or HFS dirty-volume
bypass. The dirty NON-JOURNALED bypass in0031 remains SWEET-only.

0082 now reuses0030's WRITE10, payload direction, partial4096-byte RMW,
block/character write and cache-sync mechanics for MARBLE.0030/0031 unchanged;
0082 extends only0031's vfs_subr rootrw guard to SWEET || MARBLE.
MARBLE su.writable is static-zero initialized; only exact ufsrw=1 enables it,
after GPT header/entry CRC verification, valid userdata bounds and BSD device
setup. Failed discovery returns before enable. Writable ufsroot override to
anything except userdata is rejected; default read-only overrides preserved.
No writes during discovery. Every ufs_write_blocks checks writable/nblocks,
count1..256 (1MiB bounce), lba>=first, offset<nblocks, count<=remaining and
last LBA<=UINT32_MAX. GPT bounds already constrain selected partition to
usable device LBAs and32-bit range. ufs_scsi independently repeats these
bounds and requires LUN0,10-byte0x2a CDB, write direction and exact count*4096
length.0x2a is the only allowed data-output opcode. Cache sync allows only
exact10-byte0x35 CDB, zero payload, writable LUN0 with known partition;
read-only MARBLE sync continues returning EROFS. BSD devices expose only the
partition-relative range, so GPT is inaccessible for writes. Persistent logger
and extra SWEET input/USB drivers remain excluded. MARBLE ADT/MMIO/device-WLUN
ACTIVE/readiness/capacity/GPT/cache-maintenance code retained.

Local validation PASS: full reverse/replay0001..0081, strict0082;
real CI-header arm64 object builds sweet_ufs.c and vfs_subr.c;
SWEET/BCM2837/Apple T8103 before/after preprocessed tokens identical (line
numbers normalized). Default MARBLE root is MNT_RDONLY; rootrw guard now
includes MARBLE/SWEET only. Generic Apple code unchanged. ASan/UBSan actual
source host test tools/test-marble-ufs-writes.py checks CDB, UPIU/DD, cache
sync, partial RMW, aligned writes, default RO and partition/32-bit limits.
Existing initializing-sense regression and six unit tests PASS.
Validation scripts/logs/objects: /tmp/writes-compile.py, /tmp/writes-objects,
/tmp/writes-final-*.i. Full kernel link/CI/package pending below.

JOURNALED ROOT VERIFIED: old raw/sparse images were absent. User restored
all three20H392 DMGs; independently verified original source SHA256s match.
Rebuilt SAME default journaled --board marble recipe (no --no-journal), using
restricted host sudo for local filesystem images. New raw16GiB HFSX and
sparse12145180916 bytes at shim/out/marble-xnu/ios16-root-marble-20H392.{img,simg}.
Primary header1024 and alternate17179868160 both HX0005 / attributes0x2100;
JOURNAL BIT13 SET. fsck repair followed by -f -n: iOSRoot appears OK.
Mounted verification before fsck and again READ-ONLY after fsck: launchd/dyld
arm64 root:wheel0755; OS/App cryptex populated;44 arm64 shared-cache files,
root cache hard links match cryptex. All mounts unmounted. Sparse expansion
cmp PASS for all17179869184 bytes. New hashes (historical hashes superseded):
raw 1858df50781370014d3245473248a279adcbbede5ad41dd132013d4c3967c43e
sparse ba4b1dbceb3b2dba931320716601804bf5d7cccb9b2ab72268a4808023ffba76
Logs /tmp/marble-journal-{build,sparse}.log. Updated local ignored
.SHA256SUMS matches new artifacts. The journaled root MUST be reflashed
before testing the writable kernel; NEVER boot the current non-journaled
physical root writable. No phone interaction.

Exact new diagnostic cmdline:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1
Final intended path: shim/out/marble-xnu/latest-marble-xnu.img.
Unrelated tools/iosroot-sparse.sh mode change and untracked
 docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md preserved, not staged.

Automated kernel build/package COMPLETE: source commit
e5dc3809c29a20da5a816d91ce3ecb41a5cf4e36, exact Actions39764011216 SUCCESS;
headSha independently matches. Inputs13.5/DEVELOPMENT/MARBLE/keep_going=true.
CI confirms0082, sweet_ufs.c/vfs_subr.c compiles, full kernel link PASS.
Fresh xnu/out-marble-ci-39764011216 artifact SHA256SUMS PASS; zero undefined
symbols. Exact packaged cmdline above, all payload segments byte-match this
kernel after fixups; no RAMDisk/extra root segment. Boot-manifest-hash48,
asmb, UFS PA01d84000+3000 retained. Linked UFS submission checks0x2a/count
limit256; host-to-device flags0x20/DD1 retained. Writable diagnostic linked;
SWEET persistent logger absent. Sparse bootstrap160-page allocator,
code/stacks/tables/aliases PASS. Four executable sections: zero physical
CNTP instructions, one CNTV_CTL MSR. Shim build/repack/inspect and independent
boot-v4 headers/bounds/padding/payload locator/no-trailing-bytes PASS.
Kernel SHA256 52c8f900998f4788e9881c4e3d34a70b92182cb4f40837a93a99eb46cd615bfd
Payload SHA256 57e891476b33148e150d61eaf310bbcb93d1fde9ac712a4ea11389f57a665988
Boot SHA256 8c008908b4d8e9c3a994fb76615237dc38179a7b4e1fdfdd8c41d63b548948c2
Final shim/out/marble-xnu/latest-marble-xnu.img17137664 bytes.
Logs /tmp/marble-writes-{pipeline.log,ci.log,run.json,final-audit.txt,cntp.txt};
linked strategy/submission/root mount disassembly /tmp/writes-linked-*.txt.
Physical writable-root success remains PENDING user's later manual test.
Manual commands ONLY; journaled root replacement MUST precede boot:
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


## Active handoff: MARBLE real Apple userspace / AMFI registration (2026-10-22)

User physical evidence on the existing NON-JOURNALED iOS16.7.16/20H392
userdata root (supersedes earlier journal-failure handoff):
- REAL APPLE DYLD: PASS
- REAL APPLE LAUNCHD: PASS (Darwin Bootstrapper Version 7.0.0)
- launchd ondemand mode: PASS
- first boot task fsck spawned: PASS
- fsck platform-binary policy: FAIL (boot task is not a platform binary)

Root cause confirmed by full reverse/replay0001..0082 of pinned
xnu-8796.141.3; strict0082 application PASS. Final sweet_amfi.c and
SweetEntitlements.cpp compile for MARBLE. Existing signature MAC hook sets
CS_SIGNED unconditionally and CS_PLATFORM_BINARY for MNT_ROOTFS and attaches
entitlements only to a writable blob lacking them. However bsd_init.c called
sweet_amfi_policy_register() under a SWEET-only guard.0082 now extends only
that registration guard to SWEET || MARBLE; existing provider reused.
MARBLE-only registration diagnostic uses MARBLE AMFI prefix and prints status
and error (success: MARBLE AMFI: platform binary policy registered (0)).
No per-exec logging; existing SWEET Sandbox registration behavior retained.

Local real-header arm64 object compiles PASS: bsd_init.c, sweet_amfi.c,
SweetEntitlements.cpp. Final MARBLE preprocessing proves call, CS_SIGNED
0x20000000, rootfs CS_PLATFORM_BINARY0x04000000 and conditional entitlement
attachment. SWEET and generic BCM2837 before/after preprocessed tokens match
(normalized source line numbers). Hook body unchanged; code-directory/page-hash
validation and trust-cache policy unchanged. Logs/objects/source proofs:
/tmp/amfi-validate.py, /tmp/amfi-objects, /tmp/amfi-final-*.i.

Next SWEET blocker audit: config/MASTER.arm64.marble already includes bindfs;
tools/mkadt.py already emits /chosen/boot-manifest-hash (48-byte fixed SHA384
stand-in, not an authenticated manifest). No change required. Historical SWEET
mount -P 1 then remounted / via mount_hfs and failed EROFS on read-only root;
this is a prediction for MARBLE, not yet physically observed. No rootrw or UFS
write support added. Shared-cache trust-cache warnings remain untouched.

Existing physical userdata root is GOOD and preserved: no root rebuild, flash,
filesystem edits or phone interaction. MMU/GIC/timer/SGI/UFS/GPT/HFS/root-auth/
framebuffer/shared-cache ADT policy unchanged. Exact planned payload cmdline:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1
NO RAMDisk, ufsrw or rootrw. Expected manual next result: registration success,
Doing boot task, fsck progression without boot task is not a platform binary.
Physical success remains pending. Full link/exact CI/package results follow.
Unrelated tools/iosroot-sparse.sh and docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md preserved.

Automated build COMPLETE: source commit
e541dfdcdb9679cde301864d28d0fbb977932b3b pushed origin marble; exact Actions
39761856910 SUCCESS (headSha independently matches), inputs13.5/DEVELOPMENT/
MARBLE/keep_going=true. CI log confirms0082 and all three translation-unit
compiles; full link PASS, zero undefined symbols. Fresh artifact directory
xnu/out-marble-ci-39761856910; artifact SHA256SUMS verified.
Linked bsd_init at0xfffffe0007761c1c calls existing policy registration,
after vfsinit and before HFS/root mount/userspace exec. Linked hook contains
ORR CS_SIGNED0x20000000 and rootfs-gated CS_PLATFORM_BINARY0x04000000;
validated XML entitlement extraction/create/set remains. MARBLE registration
message linked. SWEET/BCM2837/Apple T8103 preprocessing unchanged.
UFS write/sync/persistent logger symbols absent; HFS/UFS retained. Four
executable sections: zero physical CNTP instructions, one CNTV_CTL MSR.
Exact payload segments byte-match this kernel, same full cmdline above;
no RAMDisk/extra root segment, chosen boot-manifest-hash48 and asmb retained.
Sparse bootstrap mappings,160-page allocator, stacks/tables/aliases PASS.
BOARD=marble-xnu build, stock boot_a repack/inspect and independent boot-v4
headers/bounds/padding/payload locator/no-trailing-bytes checks PASS.
Kernel SHA256 7c2bcf73921b8b0b36f290269196b0d2e1288caa0dfef1aaf416ae7e21541175
Payload SHA256 ed0faee7dd1bb5c229c347d957e53478f7a0fa106144ebd99e1b00b76ffd3de6
Boot SHA256 0bab7aeb5fc7f0ace58e574dcbf3f117c738d48ee858c8673c55f7f0ebedd50a
Final image shim/out/marble-xnu/latest-marble-xnu.img (17137664 bytes).
Logs /tmp/marble-amfi-{pipeline.log,ci.log,run.json,final-audit.txt,cntp.txt};
linked proofs /tmp/amfi-linked-{bsd_init,hook}.txt. Six existing tests PASS;
git diff/staged checks PASS. Physical AMFI/fsck result PENDING user's manual
test. No userdata/root rebuild or modification; no fastboot/adb executed.
Manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


MARBLE INTERNAL-UFS HFS PID1: PASS (user physical report, 2026-10-22).
Internal UFS, GPT, userdata, BSD ufsroot0, HFS mount, exec and sustained
EL0 PID1 are physically proven. This milestone used the test init.

## Physical result and next build: MARBLE fresh journal blocks real root (2026-10-22)

User physical report:
- REAL IOS ROOT UFS READ: PASS
- HFS filesystem detected: PASS
- HFS mount: blocked only by fresh journal initialization
- journal write: EROFS as designed (strategy error 0x1e, errno 30)
- Apple launchd: NOT REACHED YET

BSD root ufsroot0 major1/minor0 and setRootMedia complete; mockfs declines
non-Mach-O root with22. HFS detects journal offset0x82000/size0x800000,
but journal_create cannot write its initial header; late journal init returns22,
mountroot ultimately reports19 and retries. This is expected for fresh journaled
HFS over deliberately read-only UFS, not evidence of a UFS read, HFS parser,
or Apple userspace failure. SWEET initially used non-journaled HFS over read-only
UFS; journaling followed writable-root support. Next experiment keeps UFS
strictly read-only and disables filesystem journaling.

Builder now accepts --no-journal in either order with --board marble; default
SWEET invocation still supplies -J. Copy/link/keybag recipe unchanged; no
sweet-root-tweaks.py. bash syntax PASS. Actual parser/mkfs invocation exercised
on disposable32MiB volumes: default attributes0x2100; both no-journal option
orders attributes0x100, journal bit13 clear in matching primary/alternate volume
headers; fsck -f -n says iOSRoot appears OK for all three. These are builder
checks, NOT verification of a new real iOS root image.

Real16GiB rebuild attempted but BLOCKED by this execution sandbox: sudo reports
no-new-privileges and cannot become root for APFS/HFS mounts or metadata copies.
Log /tmp/marble-nojournal-build.log. No nojournal.img or nojournal.simg produced;
no real-root fsck/content checks, sparse round-trip or new hashes available.
Resume exact --board marble --no-journal command in docs/MARBLE_IOS_ROOT.md
from a host session with working sudo. Do not flash an unbuilt image.
Existing boot shim/out/marble-xnu/latest-marble-xnu.img rehashed unchanged:
fa05a9ea0e3a2e3ba96604a536862f5c9d70ae9431ce816c3b9c73165df6eeb4
No kernel/UFS/HFS/policy changes, no CI, no device commands. Unrelated untracked
docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md preserved. Changes committed locally;
push origin marble failed: sandbox cannot resolve github.com. Push still pending.

## Verified local sources

User-owned inputs under `research/ios16-20H392/dmgs/` (git-ignored):

| Role | Filename | Bytes | Verified type |
| --- | --- | --- | --- |
| OS | 087-86698-044.dmg | 4730814044 | UDIF/APFS |
| SystemOS | 087-86593-047.dmg | 2743074816 | Raw APFS |
| AppOS | 087-86715-047.dmg | 10485760 | Raw APFS |

Source SHA256 (OS, SystemOS, AppOS respectively):

```text
80f426d5b8fca8552f95be427434f1911dbb4c2c6d28aad94f2426ddd0c92483
9cd738f3b0169055549df84ad6d8d13e50a2da39af618ce0522ca4e06df86849
391f2df322c3172b021b2874f6da5c3e78b70b3df8f502e1a4af2b1d715c4608
```

Read-only APFS mounts confirm iPhone OS16.7.16, ProductBuildVersion20H392.
Host initially had56GiB free (sandbox view41GiB); images remain git-ignored.
No Apple downloads. Existing apfs-fuse source at
`/tmp/marble-apfs-host-unused` was built with its LZBITMAP path unchanged;
only its open-source LZFSE dependency was fetched. Host build requires
`-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_FLAGS='-include cstdint'`.

## Existing implementation audit

`tools/mkiosroot.sh` already creates a 16 GiB case-sensitive journaled HFS+
volume named iOSRoot, using apfs-fuse for LZBITMAP decompression and root
`rsync -aH --numeric-ids`. It copies both cryptex trees to
`/private/preboot/Cryptexes/{OS,App}`, hard-links the OS shared cache to
`/System/Library/Caches/com.apple.dyld`, and links missing cryptex files into
root paths (copies symlinks). It repairs HFS filename normalization then checks
with fsck. Extended attribute/ACL preservation is not explicitly requested by
its rsync flags; do not claim those are preserved without further verification.

The optional `--board marble` interface keeps SWEET as default and adds
`verify-iosroot.py` before unmount. Tool paths can be supplied through
APFS_FUSE, MKFS_HFSPLUS and FSCK_HFSPLUS. Copy/link/keybag logic is unchanged.
`tools/sweet-root-tweaks.py` is a separate, broader GUI/daemon preparation step;
it remains unchanged and is not applied for this minimal immutable-root attempt.

Build command (local files only; host mount/copy commands require sudo):

```sh
APFS_FUSE=/tmp/marble-apfs-host-unused/build/apfs-fuse \
MKFS_HFSPLUS=/tmp/marble-hfsprogs/newfs_hfs.tproj/newfs_hfs \
FSCK_HFSPLUS=/tmp/marble-hfsprogs/fsck_hfs.tproj/fsck_hfs \
tools/mkiosroot.sh --board marble --no-journal \
  research/ios16-20H392/dmgs/087-86698-044.dmg \
  research/ios16-20H392/dmgs/087-86593-047.dmg \
  research/ios16-20H392/dmgs/087-86715-047.dmg \
  shim/out/marble-xnu/ios16-root-marble-20H392-nojournal.img
bash tools/iosroot-sparse.sh \
  shim/out/marble-xnu/ios16-root-marble-20H392-nojournal.img \
  shim/out/marble-xnu/ios16-root-marble-20H392-nojournal.simg
```

The sparse helper runs img2simg, simg2img into a fresh temporary regular file,
and cmp over the entire16GiB image before printing hashes. No block-device
writes. It needs room for raw, sparse and temporary expansion together.

## First-boot configuration evidence

Required command line:

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1
```

SWEET physical history in NOTES.md on 2026-10-15/16 establishes:

- Native iOS launchd initially failed WRONG_PLATFORM; the DEVELOPMENT
  `unentitled_ios_sim_launch=1` setting allowed execution.
- Default ignition attempted a separate Preboot role mount and failed ENOTTY.
- Level0 skipped dyld-cache discovery and could not load libSystem.
- Level1 skipped Preboot/cryptex mount stages and searched the root cache
  directory. Cache hard-links made discovery succeed.
- The macOS shared-region path then rejected the cache as not SIP-protected.
  Existing `/chosen/asmb` policy allowed mapping; launchd proceeded.

`tools/mkadt.py` already emits the same common asmb node for MARBLE and SWEET:
`lp-sip0=u64(0x6f)`, `lp-sip1=u32(1)`. No added policy relaxation is needed.
No policy or XNU source changes were made. Keep UFS read-only; no RAMDisk,
`rd=md0`, `ufsrw=1`, `rootrw=1` or persistent log writes.

The likely next class of blocker is launchd/daemon initialization requiring
writable `/private/var` (SWEET encountered EROFS), plus unavailable platform
services. This is a prediction, not a MARBLE observation. SWEET's historical
post-cache SHA1 provider fault must not be assumed to recur on today's kernel.

## Local validation

Full0001..0081 patch replay plus strict0082 application PASS. MARBLE
preprocessed UFS excludes WRITE10, sync-cache, persistent logger and ufsrw
parser; exact Device-WLUN ACTIVE and cache maintenance retained. Existing6
unit tests and actual initializing-sense ASan/UBSan regression PASS. Recovered
CI flags compile bsd_init to arm64 successfully. No XNU units changed.
SWEET copy/link/keybag logic byte-identical; SWEET tweaks and ADT unchanged.

16GiB case-sensitive journaled HFSX iOSRoot built successfully. fsck repair
followed by `fsck_hfs -f -n` PASS. Post-fsck read-only remount verification PASS:
launchd/dyld arm64 Mach-O, root:wheel0755; build20H392; both populated cryptex
trees;44 arm64 cache files with root-directory hard links to OS cryptex.
Sparse img2simg/simg2img expansion matches all17179869184 bytes via cmp.

| Artifact | SHA256 |
| --- | --- |
| `shim/out/marble-xnu/ios16-root-marble-20H392.img` | `997010004d53fe9da60e966d0eb219fc9ba97977eee1f4bce3b060ee372498ae` |
| `shim/out/marble-xnu/ios16-root-marble-20H392.simg` | `4a919839c873dd3fbf287442aeded96f8bcc1bdc1fd41373e6440100cc8643c2` |

## Exact CI and packaged boot result

Build commit `3858504a05d377b1cd4c5df9e9487429524c8db9`;
[Actions39756141953](https://github.com/Beast9265/ios-marble/actions/runs/39756141953)
SUCCESS, headSha independently verified. Inputs13.5/DEVELOPMENT/MARBLE,
keep_going=true. Fresh exact artifact `xnu/out-marble-ci-39756141953`;
artifact SHA256SUMS PASS. Pinned HFS staging and0082 confirmed in CI log.

| Artifact | SHA256 |
| --- | --- |
| `xnu/out-marble-ci-39756141953/kernel.development.marble` | `abe7215eb0365976f32e4fafcb17792438fad16637d50bdbe6c977a8265de2f6` |
| `shim/out/marble-xnu/marble-xnu.payload` | `bec23d79a321d871f8e43e9bfe24abb80d20d1fd9e6ca2a94067566eaca38137` |
| `shim/out/marble-xnu/latest-marble-xnu.img` | `fa05a9ea0e3a2e3ba96604a536862f5c9d70ae9431ce816c3b9c73165df6eeb4` |

Exact payload cmdline matches the required line above; all segments match the
exact linked kernel. No RAMDisk node/extra segment, no rd=md0, ufsrw or rootrw.
Inherited asmb values verified, UFS PA0x01d84000,size0x3000.
Linked kernel has zero undefined symbols, HFS/UFS retained, no UFS write,
sync-cache or persistent logger symbols. Four executable sections contain
zero physical CNTP instructions and one CNTV_CTL MSR. Bootstrap code/stacks/
tables/aliases, sparse map and160-page allocator capacity PASS.
Stock boot_a repack, inspect and independent header/bounds/padding/content/
locator verification PASS; final image17137664 bytes, no trailing bytes.

Logs: `/tmp/marble-iosroot-{build,sparse}.log` and
`/tmp/marble-real-ios-{pipeline.log,ci.log,final-audit.txt,cntp.txt}`.
Documentation-only follow-up does not change the build provenance above.

No device commands executed by the agent. The user subsequently reported the
physical real-root boot above; earlier validation and hashes describe the journaled image.

## Manual device commands (not executed; pending successful new image verification)

The userdata command replaces its contents with the prepared iOS root; it
must be performed manually by the user. No GPT/bootloader/recovery/modem/
persist writes are part of this workflow.

```sh
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-nojournal.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```
