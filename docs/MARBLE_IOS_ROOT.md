# MARBLE first real iOS root

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
