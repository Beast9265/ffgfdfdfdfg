# MARBLE first real iOS root

MARBLE INTERNAL-UFS HFS PID1: PASS (user physical report, 2026-10-22).
Internal UFS, GPT, userdata, BSD ufsroot0, HFS mount, exec and sustained
EL0 PID1 are physically proven. This milestone used the test init.

## Source audit: blocked

No DMG or IPSW was found under `/home`, `/tmp`, `/mnt`, `/media`, or
`/run/media`. The historical external SSD directory is absent:

`/run/media/dipa/android/ios-sweet-ipsw/iPhone10,3_16.7.16_20H392/`

Required user-provided iPhone X iOS 16.7.16 (20H392) files:

| Role | Historical filename | Expected format from SWEET notes |
| --- | --- | --- |
| OS.dmg | 087-86698-044.dmg | UDIF containing APFS, 4,730,814,044 bytes |
| SystemOS.dmg | 087-86593-047.dmg | Raw APFS, 2,743,074,816 bytes |
| AppOS.dmg | 087-86715-047.dmg | Raw APFS, approximately 10 MB |

These are historical expectations, not verification of available files.
No Apple files downloaded. Work stops at the missing-source condition requested
by the user. Readability, filesystem type and build identity remain unverified.

## Existing implementation audit

`tools/mkiosroot.sh` already creates a 16 GiB case-sensitive journaled HFS+
volume named iOSRoot, using apfs-fuse for LZBITMAP decompression and root
`rsync -aH --numeric-ids`. It copies both cryptex trees to
`/private/preboot/Cryptexes/{OS,App}`, hard-links the OS shared cache to
`/System/Library/Caches/com.apple.dyld`, and links missing cryptex files into
root paths (copies symlinks). It repairs HFS filename normalization then checks
with fsck. Extended attribute/ACL preservation is not explicitly requested by
its rsync flags; do not claim those are preserved without further verification.

The builder's SWEET references are comments and its synthetic keybag payload.
`tools/sweet-root-tweaks.py` is a separate, broader GUI/daemon preparation step;
it edits launchd jobs, activation data, audio, migration and Setup preferences.
It is not invoked by mkiosroot.sh. No builder/tweak behavior was changed in this
blocked audit; board interface and minimum first-boot tweaks remain future work.

Planned outputs, both confirmed git-ignored:

- `shim/out/marble-xnu/ios16-root-marble-20H392.img`
- `shim/out/marble-xnu/ios16-root-marble-20H392.simg`

Workspace free space at audit: 28 GiB. Raw16GiB plus historical ~12GB sparse
output leaves little margin; a full round-trip expansion needs additional
space or streaming comparison. Recheck before building. `/tmp` is tmpfs with
13GiB free and cannot hold a full expanded image.

## First-boot configuration evidence

Planned command line (not packaged by this audit):

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

## Required work after sources are available

Verify source readability, image type and build identity; recheck space.
Generalize the existing builder without changing SWEET defaults. Build the
root and check fsck, arm64 Mach-O launchd, dyld, arm64 cache files, both cryptex
trees, critical ownership/modes and links. Generate sparse with img2simg and
verify its expansion against every byte of the source image. Record both hashes.

Complete full patch replay, strict0082, changed-unit compilation if needed,
SWEET regression and exact MARBLE CI link. Package the exact new kernel with
the above arguments, verify no RAMDisk/write arguments and record all hashes.
None of these build validations has been completed in this blocked audit.
The previous test-root kernel/payload/boot hashes are not real-iOS build results.

No device commands executed. REAL IOS USERDATA FLASH NOT PERFORMED.
