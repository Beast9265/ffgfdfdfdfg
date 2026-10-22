# MARBLE migration-state root experiment

User physical result (2026-10-23): first real iOS pixels PASS, including Apple
logo and migration progress bar through CPU IOSurface/IOMFB/AppleCLCD. No panic
after more than two hours, but migration/Setup transition not observed and
fairplayd.H2/xpcproxy respawn flood persisted. Waiting longer is not progress.

## Proven source and isolated changes

Source is the preceding successful physical test's containers root:
`shim/out/marble-xnu/ios16-root-marble-20H392-containers.img`, SHA256
`e37661d455f97abd29c392c7cd41894d4aa70c8d49ff4872a630ab26426927bb`.
It retains journaled HFS, containers hierarchy, systembag, bluetoothd suppression
and gui-clean launchd state. It was hashed before use and after the experiment,
mounted read-only, and preserved. No older pre-container root was used.

A separate sparse-file clone was mounted normally as HFS loop,force. plistlib
parsed `/System/Library/xpc/launchd.plist`; executable-path discovery found
exactly one H2 job, printed before editing:

* Dictionary key `/System/Library/LaunchDaemons/com.apple.fairplayd.H2.plist`
* Label `com.apple.fairplayd.H2`
* Program `/usr/sbin/fairplayd.H2`; ProgramArguments absent

Only that LaunchDaemons entry was removed. Full plist semantic equality to the
source minus that entry was verified, including after fsck/remount. Bluetoothd
remains absent as in source; all other jobs are preserved. SpringBoard,
backboardd, runningboardd, securityd, chronod and watchdogd are present;
xpcproxy binary remains. Both GUI jobs have no /dev/console redirection.

The local base has NO plain migration plist: before keys `[]` (file absent),
after keys `[LastSystemVersion]`, value string `20H392`. No existing
DMUserDataDisposition was present to discard or manufacture. An existing plist
would be loaded and merged, preserving all previous keys. Plain path:
`/private/var/mobile/Library/Preferences/com.apple.migration.plist`,501:5010600.
No com.apple.DataMigration.plist was created.

ByHost directory501:5010755 contains both ordinary XML plist files501:5010600,
each exactly `{LastSystemVersion: "20H392"}`:

* `com.apple.migration.54D1C396-5FC8-5946-BBD5-9A3600F4085D.plist`
* `com.apple.migration.54d1c396-5fc8-5946-bbd5-9a3600f4085d.plist`

`/private/var/datamigrator/migrate` is absent in source and destination. No
sentinel or unrelated datamigrator state was deleted. No audio, activation,
installcoordination, Setup-skipping or additional daemon workaround was added.

## UUID and existing kernel audit

The actual boot-v4 wrapped payload's ADT was parsed without regeneration:
unique-chip-id raw bytes `0100454c4252414d` (ECID0x4d4152424c450001), chip-id
`15800000` (0x8015). Pinned XNU8796.141.3 arm generatePlatformUUID hashes raw
namespace A6DD4CCBB5E84AF5ACDDB6DC6A0542B8 +8 ECID bytes +4 chip bytes with
SHA1, sets version5/variant bits, takes first16 bytes. Linked namespace and
algorithm match. Reproducible calculation (also tests SWEET's known result):

```sh
python3 tools/ioplatform-uuid.py --ecid 0x4d4152424c450001 --chip-id 0x8015 \
  --xnu-source /tmp/marble-mmu-tree/xnu/iokit/Kernel/IOPlatformExpert.cpp
```

`MARBLE_IOPLATFORMUUID=54D1C396-5FC8-5946-BBD5-9A3600F4085D`.

MARBLE framebuffer throttle PASS. Final shared source and exact linked kernel
retain0056: SwapBegin allocates the swap id, SwapEnd/AppleCLCD::swap records the
latest1132-byte pending frame and dirty bit. vsyncFired gates present by dirty
and count modulo fFlushTicks. Start defaults sweetfb_hz to10, fFlushTicks=60/10=6;
timer16667us gives about10 panel copies/second. Override sweetfb_hz remains.
Existing payload has no override and keeps cpus=1. No kernel/ADT/boot rebuild,
CI or SMP work was performed.

SWEET history: v10 DataMigration.plist FAILED; v11 stable UUID+ByHost migration
preferences still migrated. The working v12 ALSO added LastSystemVersion20H392
to plain com.apple.migration.plist, preserving DMUserDataDisposition, and reached
Setup Hello despite Bluetooth/FairPlay crash loops. No unrelated v12 changes
were imported into this experiment.

## Validation and artifacts

Mounted audit plus post-fsck read-only remount PASS. fsck_hfs -f -n exit0,
volume appears OK. Primary/alternate HX0005 attributes0x2100, journal bit13 SET.
Containers ownership/modes preserved; systembag SHA256 unchanged. launchd,
dyld and xpcproxy bytes/metadata unchanged. All launchd and preference checks
above passed. All image mounts closed.

img2simg conversion PASS. Independent RAW/FILL/DONTCARE decoder expanded the
entire sparse stream and compared all17179869184 bytes with raw, byte-identical;
no additional16GiB expanded file was needed. Source image hash unchanged.

Paths relative to repository, SHA256:

```text
shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.img
7ca8c990f98875d892ffa38f769f4a8bb5af23bdbabb4ee50d69d2df13822798
shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.simg
cec3daf08e3236065d14c3939c48051430c7737f798c2b7d8affb475c3f4aa01
shim/out/marble-xnu/latest-marble-xnu.img (existing, unchanged)
7163db2431e89a3af433996b504f3b91597b3d5db5d3efddefc62c8b218793ce
```

Build/audit scripts and logs remain `/tmp/setup-fast-*`; no Apple binary/image
is committed. Expected outcome is migration skipped toward Setup, but this
root has NOT been physically tested. No fastboot/adb/device command executed.

Manual device commands only:

```sh
fastboot -S 512M flash userdata \
  ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.simg
fastboot boot \
  ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```
