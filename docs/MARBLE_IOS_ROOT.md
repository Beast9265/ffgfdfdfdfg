# MARBLE first real iOS root

MARBLE INTERNAL-UFS HFS PID1: PASS (user physical report, 2026-10-22).
Internal UFS, GPT, userdata, BSD ufsroot0, HFS mount, exec and sustained
EL0 PID1 are physically proven. This milestone used the test init.

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
tools/mkiosroot.sh --board marble \
  research/ios16-20H392/dmgs/087-86698-044.dmg \
  research/ios16-20H392/dmgs/087-86593-047.dmg \
  research/ios16-20H392/dmgs/087-86715-047.dmg \
  shim/out/marble-xnu/ios16-root-marble-20H392.img
bash tools/iosroot-sparse.sh \
  shim/out/marble-xnu/ios16-root-marble-20H392.img \
  shim/out/marble-xnu/ios16-root-marble-20H392.simg
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

Exact MARBLE CI/package pending; no new boot-image hash claimed yet.

No device commands executed. REAL IOS USERDATA FLASH NOT PERFORMED.
