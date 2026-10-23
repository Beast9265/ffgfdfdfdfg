# iOS 16 on sweet (Redmi Note 10 Pro, SM7150) - working notes


## Active handoff: MARBLE diagnostic-first Setup investigation (2026-10-23)

USER PHYSICAL RESULT (overnight, supersedes all pending setup-fast claims):
setup-fast root flashed and booted successfully PASS. First real iOS pixels
PASS; migration progress UI PASS historically. fairplayd.H2 suppression FIXED:
old FairPlay/xpcproxy flood gone. Old migration progress UI no longer remains
on screen: setup-fast changed/bypassed the previous visible migration wall;
this does NOT prove migration definitely completed. Later userspace reached.
Overnight: exec xpcproxy, nanotimekitcompaniond and maintenanced continuously;
repeated MARBLE AKS: ReportCrash sel 17 arg0 0 in 1/0 out 0/4096 -> 0x0;
occasional coreduetd/other AKS users. No panic/reboot observed. No Setup/Hello
UI, and no further visible progress overnight: Setup FAIL, blocker UNKNOWN.
Daemon relaunches and ReportCrash AKS traffic are observations, not proof that
those daemons block Setup or that ReportCrash itself is crashing.

Diagnostic-only work in progress. Keep current setup-fast userdata, cpus=1,
marbleguidiag=1, 1125x2436 presentation and 10 Hz throttle. No daemon disabling,
audio/activation/root/migration/graphics/UFS/SMP change or phone interaction.
No new root and no cleanup of existing root artifacts in this task.

SWEET v12 audit: MARBLE FILESYS_BASE already lacks config_ext_resolver (0057);
AKS35 shares17 device-state DER,101 succeeds;0056 pending-swap10Hz throttle,
container hierarchy/personas/ACL compatibility,RENAME_SWAP and Sandbox policy
all retained. VirtualAudio move targeted a mediaserverd fault, its effect at
Hello unverified; no proof it gates MARBLE GUI, no audio change. SWEET Hello
coexisted with mobileactivationd/~100 boot and other daemon loops. No specific
nanotimekitcompaniond/maintenanced/ReportCrash v12 record in available handoff;
external historical raw logs/reports unavailable locally, no invented results.

0082 changes ONLY kern_exit.c,mem.c,exception.c diagnostic sections. Nine full
p_name/proc_selfname matches: SpringBoard,backboardd,Setup,nanotimekitcompaniond,
maintenanced,ReportCrash,mobileactivationd,installcoordinationd,mediaserverd.
Opt-in abnormal-exit hook precedes crash-report eligibility; normal critical-exit,
signal/corpse decisions recovered byte-identically after removing diagnostics.
Crash32 events/boot,4/name,max64 lines,reason512chars;stderr64x256B/name and
512x256B/boot(16KiB/name,128KiB/boot). Saturating atomic reservations.
Heap SIGABRT/TRAP only,ReportCrash excluded,4 scans/boot,1/name,4096 regions,
16MiB attempted bytes/scan(strict clamp,failed copies counted),64MiB/boot,
64 strings/scan,159chars each,64KiB buffer;filtered exception/failure text.
Existing short full-name exec logger retained; no Setup launch gate established
before next physical evidence. Sampler NOT ported: mature SWEET holds task_lock
while vm_map_read_user can page-fault,unbounded thread count; lowering schedule
alone cannot guarantee bounded CPU0 latency. SWEET sampler remains unchanged.
Details/interpretation docs/MARBLE_SETUP_DIAGNOSTICS.md.

Local validation PASS: full0001..0082 reverse/replay,strict0082 whitespace apply,
all3 changed units actual-CI-header arm64 compile;SWEET/BCM2837/T8103 preprocessed
tokens unchanged(__LINE__ normalized). All other0082 sections byte-identical.
Actual extracted helper ASan/UBSan tests pass full/truncated/unknown names,
normal/noncurrent/disabled exits,32-event/64-line cap,atomic concurrent saturation,
512 stderr chunks,heap4 scans/4096 regions/16MiB success+failed-copy/64 strings,
zero-size and overflow termination. tools/test-marble-gui-diag.py TREE.
Temporary scripts/logs /tmp/setup-diag-{validate.py,equivalence.py,replay.log,
ci.log};objects /tmp/setup-diag-objects;source /tmp/setup-diag-build/xnu.

Future root cleanup: mkiosroot.sh --board marble invokes new finalizer AFTER
fsck;independent fsck+journal+readonly root validation+sparse/full expansion cmp+
SHA256+atomic registry gates deletion. Retain latest raw+sparse and previous
recorded validated sparse;bootstrap keeps all until verified fallback exists.
Exact canonical output directory/name scope,symlinks rejected,KEEP/DELETE plan,
locked exact rm -- paths;MARBLE_KEEP_ROOTS=all escape. Nonjournaled historical
build path cannot pass journal gate and skips automatic finalization/cleanup.
7 disposable fixture tests PASS including every validation-stage failure,
symlinks/hash failures and protected files. docs/MARBLE_ROOT_RETENTION.md.
No cleanup/registry access to current artifact set performed;no root creation.

Existing tool suite initially exposed stale pre-graphics test expecting gic-only
MARBLE ADT. Updated that test to assert existing gic+disp0,1125x2436 and scale3;
no generator change. Seven existing tests now PASS.

Next: commit/push exact diagnostic source,normal MARBLE Actions build and local
boot-v4 packaging,then linked/hash verification. Physical blocker NOT fixed.
No phone operations. Pre-existing iosroot-sparse.sh executable-mode change and
untracked MARBLE_BOOTSTRAP_BREADCRUMBS.md preserved,not staged.

## Previous handoff: MARBLE root-only migration experiment (2026-10-23)

USER PHYSICAL MILESTONE: FIRST REAL iOS PIXELS ON MARBLE PASS; IOSurface CPU
rendering/IOMobileFramebuffer presentation/AppleCLCD panel copy/data migration
UI PASS. Apple logo + progress bar rendered. After >TWO HOURS, alive/no panic,
fairplayd.H2/xpcproxy respawn flood; migration completion FAIL/stalled, Setup
transition NOT observed. This is no longer useful forward progress.

Exact local known-good root base from preceding manual test handoff:
shim/out/marble-xnu/ios16-root-marble-20H392-containers.img, independently
rehashed e37661d455f97abd29c392c7cd41894d4aa70c8d49ff4872a630ab26426927bb.
Read-only HFS mount confirms all four containers, no migration plain/ByHost
preferences, no datamigrator/migrate sentinel. Exact executable-discovered job:
key /System/Library/LaunchDaemons/com.apple.fairplayd.H2.plist,
Label com.apple.fairplayd.H2, Program /usr/sbin/fairplayd.H2,
ProgramArguments absent. Printed full job before any edits.

Current packaged boot SHA7163db2431e89a3af433996b504f3b91597b3d5db5d3efddefc62c8b218793ce
contains raw chosen ECID0100454c4252414d/chip15800000, scale3 and cpus=1.
Pinned XNU8796.141.3 generatePlatformUUID SHA1(namespace A6DD4CCBB5E84AF5ACDDB6DC6A0542B8
+raw8-byte ECID+raw4-byte chip),version5/variant bits yields
MARBLE_IOPLATFORMUUID=54D1C396-5FC8-5946-BBD5-9A3600F4085D.
Repro tools/ioplatform-uuid.py checks exact pinned source and SWEET known UUID.
Source/linked0056 throttle PASS: swap stores latest1132-byte pending record,
vsyncFired dirty+modulo fFlushTicks -> present, default60/10=6 ticks,16667us
vsync (~10Hz copy); sweetfb_hz remains. No kernel/ADT rebuild or CI required.

Historical correction: v10 com.apple.DataMigration.plist FAILED. v11 stable
IOPlatformUUID+ByHost com.apple.migration still migrated. Working SWEET v12
ALSO merged LastSystemVersion=20H392 into plain com.apple.migration.plist,
preserving DMUserDataDisposition. It reached Setup Hello despite FairPlay/
Bluetooth loops. MARBLE local base plain plist is ABSENT, so before keys=[];
no existing DMUserDataDisposition to replace/manufacture.

Next: separate setup-fast raw/sparse clone, remove ONLY exact H2 job, add plain
migration LastSystemVersion and both UUID case ByHost variants501:5010600;
ByHost501:5010755. Preserve bluetooth suppression, gui-clean/container/keybag
state. Focused mounted audits BEFORE unmount and AFTER fsck/read-only remount PASS.
fsck_hfs -f -n exit0 "iOSRoot appears OK"; both HX0005 headers attr0x2100,
journal bit13 SET. Entire launchd plist semantically equals source minus ONLY
identified H2 entry; no ambiguity. SpringBoard/backboardd/watchdogd/runningboardd/
securityd/chronod retained; no GUI stdout/stderr /dev/console. Bluetoothd still
absent intentionally; xpcproxy binary retained. Containers exact owners/modes
and unchanged systembag SHA b04160a5...931604d verified; source hash unchanged.
launchd/dyld/xpcproxy bytes and metadata unchanged. Plain migration keys before
[] (absent) -> [LastSystemVersion], value20H392; no prior state discarded.
ByHost upper/lower UUID variants and plain file501:5010600; directory501:5010755.
Sentinel absent in both source/destination; no datamigrator deletion. No new
com.apple.DataMigration.plist or unrelated daemon/audio/activation edits.
img2simg PASS; independent RAW/FILL/DONTCARE decoder compared ALL17179869184
expanded bytes directly against raw (no extra16GiB materialized image), PASS.
Raw shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.img SHA256
 7ca8c990f98875d892ffa38f769f4a8bb5af23bdbabb4ee50d69d2df13822798
Sparse shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.simg SHA256
 cec3daf08e3236065d14c3939c48051430c7737f798c2b7d8affb475c3f4aa01
Existing boot shim/out/marble-xnu/latest-marble-xnu.img rehashed unchanged:
 7163db2431e89a3af433996b504f3b91597b3d5db5d3efddefc62c8b218793ce
No XNU/ADT/shim build, CI, boot-arg/SMP change. All HFS mounts closed.
Evidence /tmp/setup-fast-{source.log,root.py,root.log,root-report.json,sparse.py,
sparse.log,linked-throttle.txt,linked-uuid.txt}; docs/MARBLE_SETUP_FAST.md.
Linked UUID namespace and SHA1/order/length/version/variant matched pinned
source; existing kernel SHAeda492ac...b8edf6f unchanged. Throttle start default10
atfffffe0007a6506c,60/hz at50a8; timer dirty/modulo at65308..31c -> present653a4;
swap pending1132 bytes at65c7c..90 (all fffffe0007a prefixes where shortened).
Next MANUAL experiment only: flash setup-fast sparse then boot existing image.
Expected no H2 flood and migration skipped toward Setup; NOT physically tested.
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-setup-fast.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
No phone commands, SMP, activation/audio/installcoordination changes.

## Previous handoff: MARBLE missing native display provider (2026-10-23)

LATEST USER PHYSICAL RESULT: SpringBoard throws NSInternalInconsistencyException,
"We expect a valid bounds for configuration:" for Wireless / wireless0,
Main-External, bounds/pixelSize0x0, currentMode0x0@0Hz, preferredScale1.
Containers hierarchy PASS; pre-display container wall PASSED; SpringBoard FBS
path PASS; configuration constructed PASS; Wireless INVALID; SpringBoard
stable FAIL; visible GUI FAIL. Swap compatibility installed/validated; no direct
physical VNOP_EXCHANGE invocation inferred from this exception alone.

Source-backed diagnosis: 20H392 IOMFB installs userspace virtual type2 wireless0
through MediaToolbox/FigInstallVirtualDisplay. QuartzCore names it Wireless;
first display can receive FBS Main identity independently of external status.
It is NOT an AppleCLCD property classification. AppleCLCD explicitly external=false,
no AppleTV/dfr properties or personality overrides -> native type0.
CRITICAL missing prerequisite: MARBLE platform expert never publishes arm-io/disp0.
Working SWEET0046 publishes arm-io children; MARBLE only CPU/root children.
Detailed addresses, source/linked evidence and limits: docs/MARBLE_WIRELESS_DISPLAY.md.

Minimal fix in0082: publish ONLY disp0 nub under MarblePlatformExpert. No mode
ABI/root/AirPlay/scale/surface/swap/copy/vsync changes. MARBLE marbleguidiag
adds32 actual service-property/provider/canvas notes and96 copied selector8/18/28
notes for backboardd/SpringBoard/MobileGestaltHelper, plus one nub note.
Source expected1125x2436,1,458; actual physical outputs still UNMEASURED.
Full replay/strict0082 PASS, both changedunit arm64 compiles PASS; SWEET/BCM2837/
T8103 normalized preprocessing unchanged. Source audit confirms framebuffer
minus diagnostics byte-identical; all other0082 sections byte-identical.
Source commit0eb04bb90ed1fa36be6270aee38209ae4b362dd0 pushed; exact Actions
39796176138 SUCCESS, headSha independently matches,13.5/DEVELOPMENT/MARBLE/
keep_going=true. Exact fresh artifact checksum PASS, full link zero undefined.
Actual CI log applies0082 and compiles both changed C++ units. Full package
and independent audit PASS (all exact kernel segments after fixups, boot-v4
header/bounds/padding, ADT, boot args, bootstrap aliases/stacks160-page arena).
Linked PE atfffffe0007a71dd4: path literal arm-io/disp0 atfffffe00071417c3;
createNub/attach/register vtable calls at1ecc/1ee4/1f00 after childFromPath1eb0
(all addresses prefixedfffffe0007a7). Linked AppleCLCD external property at
fffffe0007058265, Boolean false atfffffe0007a650f8. Personality no overrides.
Linked value-note budget96 (cmp95) and service budget32, process allowlist,
boot-arg gate present. Existing UFS/HFS/AKS/WDT/AMFI/IOSurface/IOKit/crash/
personas/swap compatibility preserved. PhysicalCNTP scan zero, CNTV_CTL1.
Logs /tmp/marble-display-{pipeline.log,ci.log,run.json,final-audit.log,cntp-audit.log};
source/compile/linked evidence scripts in /tmp/marble-display-re/.
Counter at0x1dcdf81a8 starts0;
first CA display gets id1. Type2 virtual GetDisplaySize has its own1080x1920
fallback; physical zero CADisplay mode is not native selector8 output.
Existing containers root remains the manual test root; no root rebuild needed.
Kernel xnu/out-marble-ci-39796176138/kernel.development.marble SHA256
 eda492ac958e06bfd47c539cb139e4211636fdba3a125b6d8699379d7b8edf6f
Payload shim/out/marble-xnu/marble-xnu.payload SHA256
 1dad6cd9c96b55b2d08cbbb07840141012914f942a8dc76bfaec861d95add4c4
Boot shim/out/marble-xnu/latest-marble-xnu.img SHA256
 7163db2431e89a3af433996b504f3b91597b3d5db5d3efddefc62c8b218793ce
ADT048e2e41...b3145175; shim586713d3...1715ee05 unchanged.
Exact existing real-iOS args preserved including marbleguidiag=1.
Manual next command (keep existing containers root):
 fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Expected new proof: MARBLE DISPLAY disp0 published; registered AppleCLCD,
external=false AppleTV/dfr absent,iomfb-type0,provider disp0 canvas1125x2436;
IOK backboardd matching IOMobileFramebuffer/open AppleCLCD/IOCoreSurfaceRoot;
actual sel8=1125,2436,sel18=1,sel28=458 from named callers. These are expected,
NOT physical observations. Check whether native primary displaces Wireless as
main and whether SpringBoard stays alive; GUI remains UNTESTED for this build.
No fastboot/adb or other phone commands executed.

## Previous handoff: MARBLE container prerequisites (2026-10-23)

LATEST USER PHYSICAL RESULT: clean GUI root + bounded diagnostic kernel reaches
backboardd, AppleKeyStore open success and HID/accessory lookups, but NO lookup
or open of IOMobileFramebuffer/AppleCLCD/IOCoreSurfaceRoot during observed
lifetime. This is before display discovery, not evidence of a broken graphics
ABI. Graphics remains frozen; no phone/fastboot/adb commands executed.

0082 ONLY extends 0052 kpi_vfs.c guard to SWEET || MARBLE. Exact fallback body
unchanged: ENOTSUP, flags exactly VFS_RENAME_SWAP, non-null destination,
two regular files, same mount -> VNOP_EXCHANGE. No cross-volume/other flags.
Existing bounded GUI IOKit/null/exit diagnostics unchanged. Historical0051/0053
heap-string helper safely shared ONLY for MARBLE current exiting backboardd or
SpringBoard on SIGABRT/SIGTRAP, marbleguidiag=1; four scans/boot,4096 region
queries/scan,96MiB attempted-copy threshold (failed copies count; final chunk
can add up to65535 bytes),700 strings/scan,
64KiB buffer,159-character strings. Zero-size/overflow stops traversal. No
sampler/stack helper port. Single CPU config retained. SWEET behavior unchanged.

Local PASS: complete0001..0082 reverse/replay, strict0082 check/application;
actual CI-header arm64 compiles kpi_vfs.c,exception.c,kern_exit.c; normalized
preprocessing SWEET/BCM2837/T8103 unchanged. Actual fallback ASan/UBSan harness
passes51200 guard/return cases. Actual heap helper ASan/UBSan passes GUI-only,
opt-in,four scans,96MiB success/failure-copy bounds,700 lines,4096 regions,
zero-size/overflow cases. All0082 graphics/hardware/UFS/HFS/AKS/WDT/AMFI/IOKit
sections byte-identical to HEAD. git diff --check uses historical patch-context
whitespace settings; strict git apply --whitespace=error validates source adds.
Scripts/logs /tmp/containers-{compile.py,source-proof.py,scan-test.py}.

Root COMPLETE: cloned independently hash-verified JOURNALED gui-clean root,
only mkdir/chown/chmod for four requested directories and necessary parents.
No wholesale sweet-root-tweaks, activation/audio/telephony/migration changes.
Exact tools/sweet-root-tweaks.py ownership/modes:
/private/var/containers/Bundle 33:33 0755
/private/var/containers/Data/System 0:0 0755
/private/var/containers/Shared/SystemGroup 0:0 0755
/private/var/containers/Temp 0:0 0755
Bluetoothd absent,backboardd/SpringBoard present,no stdout/stderr overrides;
launchd cache byte-identical to gui-clean. launchd/dyld SHA256 unchanged:
12370e5ee35bf28ae479b6c4b4455f4f4693ab803e37c5eb3032537c18cac61c
5806834564fe6462ae981d0915d612b1eb2f6f168822b5d278bee56254933757
keybags root:wheel0700; systembag.kb root:wheel0600,227B,unchanged SHA256
b04160a5b4f84f6318549fd420d1d2efa591af6df08f3c9b1abba587e931604d.
usersession.kb/persona.kb absent,not manufactured. Existing kernel personas
confirmed config_personas plus linked persona_alloc/find/init/kpersona syscalls.
Independent read-only mounted audit + fsck_hfs -f -n exit0: iOSRoot appears OK.
Both primary/alternate HX0005 attributes0x2100,journal bit13 SET.
Full sparse expansion compared all17179869184 bytes with independent decoder:
PASS byte-identical; no exhaustive Unicode full-tree traversal repeated.
Raw shim/out/marble-xnu/ios16-root-marble-20H392-containers.img SHA256
 e37661d455f97abd29c392c7cd41894d4aa70c8d49ff4872a630ab26426927bb
Sparse shim/out/marble-xnu/ios16-root-marble-20H392-containers.simg SHA256
 01f6cac2653379c35fb4b1043c7031fd1cf4e044e2a8d7e1862556ef356f54f0
Logs /tmp/containers-{root.log,root-recheck.log,sparse-audit.txt}; mounts closed.

Automated CI/package COMPLETE: kernel source commit
818444bdb02c9c417cc1aaf7a9b1ec92e7da338c, exact Actions39790623310 SUCCESS;
headSha independently matches,13.5/DEVELOPMENT/MARBLE/keep_going=true.
Fresh xnu/out-marble-ci-39790623310 artifact SHA256SUMS PASS. Exact CI log
confirms0082 application and all3 changed C compiles; full link PASS with zero
undefined symbols. Linked vn_rename atfffffe000753d4b4 has flags2/errno45
checks atfffffe000753d820/d828, destination null check d840, VREG1 checks
d84c/d858, mount pointers+d8 equality d864..d870; equality branches dcc4 and
VNOP_EXCHANGE call atfffffe000753dccc. Proves fallback active for MARBLE with
all original safety gates. Linked GUI heap scanner atfffffe00073274d0 retains
allowlist,boot-arg gate,four-scan/4096-region/700-line/copy-budget bounds;
SWEET stack and sampler helpers absent. Existing bounded IOKit/null/exit hooks
and personas linked. Source graphics/hardware sections unchanged.

Exact payload segments independently match this CI kernel after fixups; no
RAMDisk/extra root segment. Existing args retained verbatim:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1
BOARD=marble-xnu shim SHA256 unchanged586713d3...1715ee05,clean stock boot_a
repack/inspect and independent header/bounds/padding/payload-locator proof PASS.
Sparse bootstrap160-page arena/aliases/stacks/tables PASS; four executable
sections zero physical CNTP instructions,one CNTV_CTL MSR. UFS/HFS/AMFI/AKS/WDT,
IOSurface/AppleCLCD clients and personalities,ADT gic+disp0 only,physical
1080x2400 stride4320/canvas1125x2436/scale3,console/short-exec logs retained.
Kernel SHA256 8c138cacc95e273b74d82c992da4ac6dcff4355dd18de46f6fd86fdf9e5c6cf7
Payload SHA256 cc92cfffb98306a8781ab658346a35fa1f27eb2666b820069f8b4400a7ec2030
Boot SHA256 bf1a3d28596705d173fa8da5592db47ccc150d078e6ad38b34b6f6131b182947
Final shim/out/marble-xnu/latest-marble-xnu.img.
Logs /tmp/marble-containers-{pipeline.log,ci.log,run.json,final-audit.txt,cntp.txt};
linked proof /tmp/containers-linked-swap-scan.txt. Root raw/sparse hashes above.
All local image mounts closed. No fastboot/adb/physical device operations.

NEXT USER MANUAL TEST (userdata replacement,no GPT changes):
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-containers.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Expected success indicator: IOK backboardd matching IOMobileFramebuffer,
open AppleCLCD/IOCoreSurfaceRoot,then MARBLE FB: backboardd activity. If still
pre-display,record STR exception text and CRASH reason. GUI/physical display
discovery remains UNPROVEN until user reports the next boot.


## Active handoff: MARBLE clean GUI startup / bounded diagnostics (2026-10-22)

LATEST PHYSICAL USER OBSERVATION supersedes earlier display-MISSING wording:
graphics-enabled e32e5d7235950c356c7742ef3ae3794b41dac844 / Actions39777337402
booted on POCO F5; broad real userspace, repeated SpringBoard exec and chronod
for minutes. Stable SpringBoard and visible GUI FAIL. Current GUI-debug root
may prevent backboardd startup because its launchd stdout/stderr point to
/dev/console. SWEET history CONFIRMED posix_spawn backboardd EACCES0xd with
these properties, fixed by removing them. MARBLE display failure NOT confirmed.
No phone/fastboot/adb commands executed. No hardware or graphics driver edits.

Input artifacts independently rehashed: graphics boot
f11a12254baa43dcce58d9ab9bef8c8fd2ef361d2fbe9e239421784e41ec8387;
gui-debug raw41ebe2c0d48718359ead4fecaae86128bbbc0cb0454d15ad7f0b83fe41e6eaf4;
gui-debug sparsecbc95746991ed2883999ec7a86a8a9b5befab4f31059410780d8aec267eb0bf4.
Existing exact linked-kernel/payload/ADT/boot graphics audit rerun PASS
(/tmp/gui-original-graphics-audit.txt). All four graphics classes linked.
Final shared SweetSurface.cpp IOCoreSurfaceRoot::start logs MARBLE SURF:
IOCoreSurfaceRoot registered AFTER registerService() at lines402/403.
SweetFramebuffer.cpp AppleCLCD::start logs MARBLE FB: AppleCLCD geometry
AFTER registerService() at208/209, after surface/workloop/timer setup; setup
failure paths already print. ADT gic+disp0 only, framebuffer0xb8000000,
1080x2400 stride4320 visible0x009e3400, canvas1125x2436 scale3 retained.
These are registration expectations, NOT physical registration proof.

NEW gui-clean cloned from verified debug raw. Only mounted launchd cache
changed through HFS filesystem. clean-gui-launchd-plist.py checks the ENTIRE
input against the exact known transformation of original Apple plist, then
restores only GUI job output/environment fields from Apple original. Bluetoothd
absent, both GUI jobs present, all7 existing _PanicOnCrasX suppressions retained.
No stdout/stderr overrides on either GUI job. Original Apple backboardd has no
EnvironmentVariables; SpringBoard retains CA_ASSERT_MAIN_THREAD_TRANSACTIONS=1.
OS_ACTIVITY_DT_MODE/CFLOG_FORCE_STDERR absent originally and now removed.
All unrelated jobs semantically unchanged versus debug root. Mounted and
post-fsck read-only comparisons PASS, extracted final plist byte-match PASS.
plist root:80 0644; launchd/dyld root:wheel0755 unchanged SHA256s from prior
handoff; xpcproxy also unchanged. fsck_hfs -f -n exit0: iOSRoot appears OK.
No exhaustive Unicode tree traversal repeated. Sparse/hash validation below.

0044 final reason printing is SWEET-only in kern_exit.c; its full stack/heap
helpers in exception.c also SWEET-only.0082 adds ONLY a MARBLE branch at same
crash-exit site: target names backboardd/SpringBoard, first32 crash reports,
signal/exception/subcode and exit namespace/code/reason text (max512 chars).
No sampler/heap scanner imported, no exit/corpse semantics changed.
0048 final mem.c tee SWEET-only: shared existing selected-write path; MARBLE
has fixed backboardd/SpringBoard allowlist, max256 chunks of256B per boot.
0049 final IOUserClient.cpp tracing SWEET-only;0054 expanded default to both
GUI processes.0082 shares existing matching/matching1/notifications/path/
children/open probes with MARBLE, same400-line limit. MARBLE fixed GUI allowlist.
All three MARBLE diagnostics require marbleguidiag=1, default OFF. SWEET args,
defaults and limits unchanged. No global /dev/null tee or console plist logging.

Local PASS: full0001..0081 reverse/replay then strict0082; real CI-header arm64
compiles kern_exit.c, mem.c, IOUserClient.cpp; SWEET/BCM2837/T8103 preprocessed
tokens identical with __LINE__ normalized at preprocessing (diagnostic line
numbers naturally shift). ASan/UBSan actual MARBLE helper tests PASS: disabled,
other process rejection, exact two names, null256/IOK400 exhaustion. Old0082
prefix unchanged; graphics source and all hardware/root/AMFI/AKS/WDT unchanged.
Artifacts /tmp/gui-diag-edit.py, diag-compile.py, diag-bound-test.py, diag-objects.
Exact old args retained plus ONE bounded arg marbleguidiag=1:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1
Root milestone COMPLETE: full17179869184-byte sparse expansion compared to raw
using independent RAW/FILL/DONTCARE decoder (no extra16GiB disk copy), PASS.
Primary/alternate HX0005 attributes0x2100, journal bit13 SET.
Raw shim/out/marble-xnu/ios16-root-marble-20H392-gui-clean.img SHA256
5d61c497f1d025afb9abb10152230bfe838bd549c104fc8d2390a27eddb283aa
Sparse shim/out/marble-xnu/ios16-root-marble-20H392-gui-clean.simg SHA256
cf5d9c434166aefb99f0d4d2d951c1cee4a16fbd911adb74010557b0915e75cd
Validation /tmp/gui-clean-sparse-audit.txt, gui-sparse-check.py; all mounts closed.
Automated CI/package COMPLETE: source commit
4aa216d1bf59fe69992ec151f24324a1fdae47bb, exact Actions39780521219 SUCCESS;
headSha independently matches;13.5/DEVELOPMENT/MARBLE/keep_going=true.
Fresh xnu/out-marble-ci-39780521219 artifact SHA256SUMS PASS; full MARBLE
link PASS, zero undefined symbols. Linked crash hook compares32, null tee
compares256 and caps each chunk256B; IOUserClient open trace compares400.
Opt-in PE_parse_boot_argn and both name comparisons confirmed in disassembly.
No SWEET stack/heap/sample helpers linked. SWEET/generic source paths retained.
Exact old0082 remains byte-identical prefix; only three diagnostic files appended.

Full linked/payload/boot audit PASS: all payload segments match this exact
CI kernel after fixups, no RAMDisk/extra root segment, exact cmdline above.
Boot BOARD=marble-xnu, clean stock boot_a repack/inspect, independent header/
bounds/padding/locator and content proof PASS. Sparse bootstrap160-page arena/
aliases/stacks/tables PASS. Four executable sections: zero physical CNTP
instructions, one CNTV_CTL MSR. Existing UFS/HFS/rootrw, AMFI/platform policy,
AKS/keybag and IOWatchdog linked proofs PASS. Graphics linked starts:
IOCoreSurfaceRoot0xfffffe0007a62788; AppleCLCD0xfffffe0007a64d84.
IOSurfaceRootUserClient::externalMethod0xfffffe0007a63cbc;
IOMobileFramebufferUserClient::externalMethod0xfffffe0007a659a0.
Both personalities and registration diagnostics retained. Packaged ADT exact
framebuffer/canvas/scale and gic+disp0 only PASS; short exec and console retained.
Kernel SHA256155b8f9e321aefe018d3aaf5f20dc745ec55bd1e32069ed35b6b9f466b9498b6
Payload SHA256ab096607c92857b8583b2b190f5b22b25525ebbeaac4c71643bb215b132cc487
Boot SHA2569f8791a65c9ae94a51abcb995f4b0d1175718446185e99902c798c06e1a8c0fc
Final shim/out/marble-xnu/latest-marble-xnu.img17244160 bytes.
Previous graphics boot preserved privately as marble-graphics-e32e5d7.img
in same directory, independently rehashed f11a1225...ec8387 (full hash above).

Standard simg2img expansion + cmp ALSO PASS for all17179869184 bytes; temporary
expanded image removed. All local image mounts unmounted. Root input/debug
images preserved. No full-tree Unicode traversal or unrelated root job changes.
Logs /tmp/marble-gui-clean-{pipeline.log,ci.log,final-audit.txt,cntp.txt}; audit
script /tmp/marble-gui-clean-final-audit.py; bounded linked hooks /tmp/gui-linked-*.
Interpretation and limits: docs/MARBLE_GUI_DIAGNOSTICS.md. git diff --check,
staged whitespace/stat review PASS. Unrelated sparse helper mode/breadcrumb doc
preserved. No fastboot/adb or physical-phone interaction performed.

NEXT PHYSICAL RESULT PENDING: user manually installs clean sparse then boots
new diagnostic image. Capture early SURF/FB registration, exec backboardd,
IOK matching/open lines, |backboardd|/|SpringBoard| exception text and CRASH
reason namespace/code. Limits apply per boot, so record early output. Do not
assume missing display or ABI mismatch until those observations establish it.
Manual commands ONLY (userdata replacement, no GPT changes):
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-gui-clean.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img



## Active handoff: MARBLE IOSurface / framebuffer (2026-10-22)

User physical milestone: SpringBoard exec PASS; SpringBoard stable FAIL / respawn
loop for 10+ minutes; display service MISSING. backboardd, securityd, chronod,
fairplayd.H2 and xpcproxy execute. AppleKeyStore/keybag/watchdogd, writable UFS,
journaled HFS, dyld/launchd and broad LaunchDaemons PASS (user observation).

0082 alone shares FINAL SweetSurface.cpp/.h and SweetFramebuffer.cpp with MARBLE,
plus only IOCoreSurfaceRoot/AppleCLCD personalities. files.arm64 already builds
both optional iokitcpp units. No new Marble graphics implementation or unrelated
driver enabled. Shared sweet,display compatible retained: MARBLE /arm-io has
ONLY gic and disp0; no SWEET wdt/input nodes restored. Identity unchanged.

Audited final0001..0081:0046 ABI includes create/lookup/lock/map, default surface,
SwapBegin/End, layer IDs, vsync, CPU copies, bounds, async-reference bzero,
reference/mapping cleanup.0056 throttles presents (default10Hz);0061 iPhone X
1125x2436 canvas/center crop;0067 opt-in console mute;0068 cached same-client
lookup lifetime fix;0079 power/fade behavior preserved.0054/0058/0062 touch
adjacent configuration; final personalities/files list retained. No rollback to
original0046. MARBLE SURF/FB diagnostic prefixes added; SWEET strings unchanged.
AppleCLCD uses PE_current_console, not a SWEET PA constant. Existing MARBLE ADT:
PA0xb8000000,1080x2400,stride4320,visible0x009e3400; canvas1125x2436 @3x.
MARBLE console stays enabled even if sweetfb_noconsole supplied (first test);
SWEET opt-in mute unchanged; no SWEET persistent logger imported.
0042 short exec log guard extended only to MARBLE; authorization/code-signing
control flow byte-identical. All existing root/AMFI/AKS/WDT/CPU/timer code retained.

Local validation PASS: reverse/replay0001..0081, strict0082 whitespace apply;
actual CI-header arm64 compiles SweetSurface.cpp, SweetFramebuffer.cpp,
KernelConfigTables.cpp and kern_exec.c. Normalized preprocessed SWEET/BCM2837/
T8103 tokens unchanged for all four files. Fixed-seed SWEET ADT byte-identical;
MARBLE exact framebuffer/canvas/minimal children and personalities checks PASS.
Scripts/logs /tmp/graphics-{edit.py,compile.py,compile.log,proof.py}.
Patch context whitespace checked using core.whitespace=-blank-at-eol,-space-before-tab;
strict git apply --whitespace=error independently checks added source.

Exact boot args retained (NO RAMDisk):
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1
No userdata/root rebuild or phone operation. Unrelated iosroot-sparse.sh mode
and bootstrap breadcrumbs preserved. Full CI link/package/linked proofs completed below.
Next physical test: observe MARBLE SURF registration, MARBLE FB AppleCLCD geometry,
backboardd/SpringBoard selectors; stable SpringBoard/UI remains unproven.


Automated CI/package COMPLETE: source commit
e32e5d7235950c356c7742ef3ae3794b41dac844, exact Actions39777337402 SUCCESS;
headSha independently matches.13.5/DEVELOPMENT/MARBLE/keep_going=true.
Full kernel link PASS; fresh exact artifact SHA256SUMS PASS; zero undefined symbols.
Linked IOCoreSurfaceRoot::start0xfffffe0007a61df4;
IOSurfaceRootUserClient::externalMethod0xfffffe0007a63328;
AppleCLCD::start0xfffffe0007a643f0;
IOMobileFramebufferUserClient::externalMethod0xfffffe0007a6500c.
Both graphics personalities and MARBLE SURF/FB diagnostics present in binary.
Unrelated SWEET HID personalities absent; historical unguarded HID class symbols
already exist in files.arm64 builds, unchanged by this port.
Packaged ADT confirms only gic/disp0, PA0xb8000000,1080x2400,stride4320,
visible0x009e3400, canvas1125x2436, display-scale3. Shim Boot_Video uses these
same MARBLE constants; AppleCLCD reads PE_current_console. No SWEET PA constant
in shared graphics sources. Console-mute symbol absent from linked MARBLE kernel;
short exec string present and old entitlement/boot-arg verbose string absent.
All payload segments match exact CI kernel after fixups; no extra root segment,
no RAMDisk property; exact requested cmdline verified. BOARD=marble-xnu build,
stock boot_a repack, inspect, independent boot-v4 byte/header/bounds/padding/
locator checks and sparse bootstrap audit PASS. Existing UFS/HFS, AMFI platform
policy/entitlement attachment, AKS/WDT, boot-manifest-hash48 proofs PASS.
Kernel SHA256 bae253009a0d9eb4b2b84b9b9a589ec357312ddf9805b84b0c8421396264ba6e
Payload SHA256 fa62c211686cc6caaf02a36d88926c9cb0a5e7f097f5a6b5771777fa4975cbb6
Boot SHA256 f11a12254baa43dcce58d9ab9bef8c8fd2ef361d2fbe9e239421784e41ec8387
Final shim/out/marble-xnu/latest-marble-xnu.img.
Logs /tmp/marble-graphics-{pipeline.log,ci.log,run.json,final-audit.py,final-audit.txt}.
Physical graphics registration, client activity, stable SpringBoard/UI PENDING.
No root/userdata change or fastboot/adb/phone operation performed.
Manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


## Active handoff: MARBLE GUI diagnostic root (2026-10-22, COMPLETE)

Helper/test/artifact handoff commit397686b (root-only; no new CI).

User reports latest physical watchdog kernel alive for 15+ minutes, repeatedly
spawning bluetoothd through xpcproxy while other services occasionally progress.
No XNU/graphics change requested. Existing d73336bb / Actions39768601240 kernel,
AppleKeyStore, IOWatchdog, writable UFS, launchd_unsecure_cache=1 retained.
No fastboot/adb or other physical-device command executed.

Actual original journaled20H392 cache inspected read-only via libdmg extraction:
Label com.apple.bluetoothd, dictionary key
/System/Library/LaunchDaemons/com.apple.bluetoothd.plist.
Helper now accepts repeatable --disable, removes entries by Label, prints each
key/Label and fails missing/conflicting requests before output. Console logging
and existing global _PanicOnCrash->_PanicOnCrasX behavior retained (7 original
panic keys). Exact semantic comparison on real plist and synthetic regression
PASS. BluetoothUIService and bluetoothuserd remain; no dependency pruning.

Original image copied to ios16-root-marble-20H392-gui-debug.img; original mounted
read-only /tmp/marble-gui-source, debug mounted loop,force /tmp/marble-gui-debug.
Validated plist copied through HFS mount with sudo cp (no raw-offset writes).
Only bluetoothd removed; com.apple.backboardd/com.apple.SpringBoard console logs.
Mounted cache parses; both GUI jobs, runningboardd/watchdogd retained.
xpcproxy is not a cached job in the original: /usr/libexec/xpcproxy binary remains
byte-identical. launchd/dyld SHA256 also identical to original mounted files.

Focused validation PASS (user explicitly substituted this for exhaustive audit):
full source/destination plist semantic equality after ONLY bluetoothd removal,
two GUI logging edits, and existing7 panic-key renames. Both GUI jobs retain
StandardOutPath/StandardErrorPath=/dev/console and OS_ACTIVITY_DT_MODE=YES,
CFLOG_FORCE_STDERR=1; SpringBoard's existing CA_ASSERT_MAIN_THREAD_TRANSACTIONS
retained. All other plist data semantically unchanged.
launchd SHA25612370e5ee35bf28ae479b6c4b4455f4f4693ab803e37c5eb3032537c18cac61c
dyld SHA2565806834564fe6462ae981d0915d612b1eb2f6f168822b5d278bee56254933757
xpcproxy SHA256a97bc59d024c3b7fcf293aa6ef2fa75b60ef7220b2546ab4382adcbe78ddbfec
All three byte-identical to source. No xpcproxy Label/job in original cache;
/usr/libexec/xpcproxy remains. OS/App cryptexes,44 cache files,logd dirs present.
systembag.kb extracted read-only from both images:227 bytes, cmp PASS; HFS catalog
root:root0600. Patched plist retains root:80(group)0644, matching source.
No broad tweaks script used; no other file intentionally changed.

Host full-tree audit limitation: user reports Linux HFS+/Unicode traversal
FileNotFoundError at localized WorkflowKit.framework/th.lproj/DefaultShortcuts/
Thai shortcut filename. Per user, do NOT rerun exhaustive audit or alter file.
No full-tree content/metadata proof claimed; only focused verification performed.
Both mounts unmounted. fsck_hfs -f -n exit0: iOSRoot appears OK.
Primary1024 and alternate17179868160:HX0005,attributes0x2100,journal bit13 SET.
Post-unmount extracted plist byte-matches validated diagnostic plist.
Original raw verified1858df50781370014d3245473248a279adcbbede5ad41dd132013d4c3967c43e
before later disappearing externally; original sparse remains. No agent command
removed original raw. Debug clone preserved. First /tmp expansion ENOSPC;
incomplete temporary expansion removed; retry on disk with sparse temporarily
in /tmp. Final simg2img expansion on disk + cmp PASS for all17179869184 bytes (exit0).
Temporary expanded raw removed; sparse returned to final requested path.

Raw debug SHA25641ebe2c0d48718359ead4fecaae86128bbbc0cb0454d15ad7f0b83fe41e6eaf4
Sparse debug SHA256cbc95746991ed2883999ec7a86a8a9b5befab4f31059410780d8aec267eb0bf4
Existing boot SHA256e9fd2e541aabbd0f48d186b3b448587913a8bf1b7881aac2f25b3702e0dec196.
No new kernel build/CI for this root-only experiment. Regression test PASS;
git diff --check and staged checks PASS. Final artifacts (ignored, not staged):
shim/out/marble-xnu/ios16-root-marble-20H392-gui-debug.img
shim/out/marble-xnu/ios16-root-marble-20H392-gui-debug.simg
Existing boot:shim/out/marble-xnu/latest-marble-xnu.img.
Next: user manually flashes debug sparse and boots existing watchdog kernel;
observe backboardd/SpringBoard/CAWindowServer/FBSDisplayMonitor/IOSurface/
IOMobileFramebuffer diagnostics. No graphics port or physical success claimed.
Manual commands ONLY:
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392-gui-debug.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


## Active handoff: MARBLE watchdog discovery (2026-10-22)

Physical milestone reported by user on previous AKS kernel:
AppleKeyStore PASS; keybag PASS; launchd cache PASS; LaunchDaemons PASS;
watchdogd started PASS; IOWatchdog discovery FAIL. watchdogd pid140 exits
namespace2/subcode0x5 after missing watchdog KEXT service, triggering panic.
Current journaled writable 20H392 userdata root preserved; kernel-only test.

Replayed0001..0081 and strict0082 PASS. Final mature SweetWatchdog.cpp has
IOWatchdog/IOWatchdogUserClient, user-client property, IOPMUPrimary u32(1),
setProperties success, scalar/direct/descriptor output zeroing and success
for all selectors. Historical0/1/2/3/4/5/9 log once each (selectors>=64 retain
historical per-call logging). No hardware MMIO, timers, timeout or reset path.
0082 alone extends watchdog implementation/personality to MARBLE, retaining
SWEET-only unrelated services; board-specific MARBLE WDT prefix, shared code.
HFS limiter guard extended only: OSIncrementAtomic returns original value,
so notes0..7 print; subsequent notes suppressed; all attribute repairs remain
outside logging conditions. UFS write safety and all other source unchanged.
Real CI-header arm64 compiles PASS: SweetWatchdog.cpp, KernelConfigTables.cpp,
hfs_catalog.c. SWEET/BCM2837/T8103 normalized preprocessed tokens unchanged.
Actual externalMethod ASan/UBSan harness PASS: listed selectors success,
scalar/direct/descriptor zeroing including partial8-byte writes; once logs.
Logs/scripts /tmp/wdt-{replay.log,compile.py,compile.log,abi.py,abi.cpp}.
Patch context whitespace checked with patch-aware git whitespace settings;
strict git apply --whitespace=error independently validates added source.

Exact unchanged cmdline (NO RAMDisk):
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1
No root rebuild, userdata write, fastboot, adb or physical-phone operation.
Full CI kernel link/package and linked proofs completed below. Physical watchdog
success remains pending manual boot; no display/GPU/IOSurface port attempted.
Unrelated iosroot-sparse.sh mode and bootstrap breadcrumbs preserved.

Automated build/package COMPLETE: kernel source commit
 d73336bbe09abbcd7f71cef07304201cc5716ab4; exact Actions39768601240 SUCCESS,
headSha independently matches;13.5/DEVELOPMENT/MARBLE/keep_going=true.
Exact fresh artifact SHA256SUMS PASS; full kernel link, zero undefined symbols.
Linked IOWatchdog::start0xfffffe0007a5ce58, setProperties0xfffffe0007a5ce50
(mov w0,0; ret), IOWatchdogUserClient::externalMethod0xfffffe0007a5d100.
IOClass=IOWatchdog / IOProviderClass=IOResources personality verified in kernel.
start disassembly passes IOPMUPrimary string, value1, width32; user-client
class property retained. Mature zeroing/selector implementation retained;
source contains no real watchdog/PMU MMIO, timer or reset operation.
Linked HFS cat_lookupbykey contains OSIncrementAtomic and compare8 (inlined
sweet_hfs_link_note); attribute repair remains unconditional after log guard.
All payload segments match exact CI kernel after fixups; no RAMDisk or extra
root segment; exact cmdline above verified. ADT, sparse bootstrap mappings,
shim BOARD=marble-xnu, stock boot_a repack/inspect and independent boot-v4
bounds/header/padding/payload-locator checks PASS. UFS write guards unchanged.
Kernel SHA256 44c14838a2badba184f0f6c918d68f24ff69cc1b2a6f18fe932f0d551bf91ea1
Payload SHA256 936b21f5928f33cb8b85eb37a3249ca2b041a0bb17d152ab6042424ebce3bbed
Boot SHA256 e9fd2e541aabbd0f48d186b3b448587913a8bf1b7881aac2f25b3702e0dec196
Final shim/out/marble-xnu/latest-marble-xnu.img.
Logs /tmp/marble-wdt-{pipeline.log,ci.log,run.json,final-audit.txt};
proofs /tmp/wdt-{source-proof.py,linked-methods.txt,linked-hfs.txt}.
No phone operation or root/userdata rebuild. Next: user manual boot, observe
MARBLE WDT registration/selectors and actual next wall; physical discovery
success NOT claimed. No preemptive display/GPU/IOSurface changes.
Manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


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

Automated build/package COMPLETE: source commit
c1116d6c987f1df1442aebe7a7843e59358cd244, exact Actions39766822009 SUCCESS;
headSha independently matches. Inputs13.5/DEVELOPMENT/MARBLE/keep_going=true.
CI confirms0082 and SweetKeyStore/KernelConfigTables compiles; full link PASS.
Fresh xnu/out-marble-ci-39766822009 artifact SHA256SUMS PASS; no undefined symbols.
Linked AppleKeyStore::start at0xfffffe0007a585d8 and
AppleKeyStoreUserClient::externalMethod at0xfffffe0007a58860; both metaclasses
present. Linked personality IOClass=AppleKeyStore / IOProviderClass=IOResources
verified; MARBLE AKS diagnostic linked. Source enum/dispatch byte-identical;
extracted actual dispatch ASan/UBSan checks0/14 success, handle0, invalid output
and unsupported selector PASS (LeakSanitizer disabled for sandbox ptrace).
Packaged ADT /defaults/no-effaceable-storage u32(1) PASS. Existing builder
systembag recipe already satisfied, not rebuilt or mounted in this experiment.
All payload segments byte-match exact CI kernel after fixups; full cmdline
above verified; no RAMDisk property or extra root segment. BOARD=marble-xnu,
stock boot_a repack/inspect and independent boot-v4 bounds/padding/content/
locator checks PASS. Sparse bootstrap mappings/allocator/stacks/tables PASS.
Four executable sections: zero physical CNTP instructions, one CNTV_CTL MSR.
Linked built-in AMFI signed/platform policy, unsealed-root exception, writable
UFS/HFS diagnostics and boot-manifest-hash48 retained; persistent logger absent.
Kernel SHA256 073343099a5f3adb0bd6cc25150aca49ce6fb676413494b1fcb0a3c6c294205d
Payload SHA256 bd761b7d1f80aeb5d8244a77e91169645e87574c36ad99eea1fa6890304967a1
Boot SHA256 01f8e52e1fb809ac80251ab7470be591e6f1e3c128ab7f22cd23e4ef04bd408b
Final shim/out/marble-xnu/latest-marble-xnu.img (17145856 bytes).
Logs /tmp/marble-aks-{pipeline.log,ci.log,run.json,final-audit.txt,cntp.txt};
linked methods /tmp/aks-linked-methods.txt. Physical AKS/keybag/cache transition
PENDING user's manual boot. No phone operation or userdata rebuild performed.
Manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img


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

## Active handoff: MARBLE fresh journal blocks real root (2026-10-22)

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

## Active handoff: MARBLE real iOS root and boot image verified (2026-10-22)

MARBLE INTERNAL-UFS HFS PID1: PASS (user physical evidence).
Local source research/ios16-20H392/dmgs now present and readable:
087-86698-044.dmg OS UDIF4730814044 bytes SHA256
80f426d5b8fca8552f95be427434f1911dbb4c2c6d28aad94f2426ddd0c92483
087-86593-047.dmg SystemOS APFS2743074816 bytes SHA256
9cd738f3b0169055549df84ad6d8d13e50a2da39af618ce0522ca4e06df86849
087-86715-047.dmg AppOS APFS10485760 bytes SHA256
391f2df322c3172b021b2874f6da5c3e78b70b3df8f502e1a4af2b1d715c4608
Host free56GiB; sandbox reports41GiB. Outputs/source ignored.
Read-only user FUSE mounts /tmp/marble-ios-source-{os,system,app} verify
OS SystemVersion iOS16.7.16/20H392, launchd/dyld arm64 root:wheel0755.
Built existing /tmp/marble-apfs-host-unused/build/apfs-fuse with existing
LZBITMAP support; fetched only open-source LZFSE submodule. Modern host build
uses CMAKE_POLICY_VERSION_MINIMUM=3.5 and CXX_FLAGS=-include cstdint.
HFS tools /tmp/marble-hfsprogs/{newfs_hfs.tproj/newfs_hfs,fsck_hfs.tproj/fsck_hfs}.

Full patch reverse/replay0001..0081 + strict0082 PASS; preprocessed MARBLE
no WRITE10/sync/persistent log/ufsrw parser PASS;6 existing tests and actual
initializing-sense ASan/UBSan regression PASS. Recovered actual CI flags
bsd_init real-header arm64 compile PASS. No XNU/policy/hardware changes.
New --board marble builder option only adds mounted-root verification;
SWEET default and copy/link/keybag/tweak behavior unchanged.

Real16GiB HFSX iOSRoot build PASS using --board marble; sourceOS build
20H392 verified. Mounted launchd/dyld arm64 root:wheel0755, populated OS/App
cryptexes,44 arm64 cache files hard-linked into root cache path PASS.
fsck repair and final -f -n PASS; post-fsck read-only remount verification PASS.
Android sparse img2simg/simg2img full17179869184-byte cmp PASS.
Raw shim/out/marble-xnu/ios16-root-marble-20H392.img SHA256
997010004d53fe9da60e966d0eb219fc9ba97977eee1f4bce3b060ee372498ae
Sparse shim/out/marble-xnu/ios16-root-marble-20H392.simg SHA256
4a919839c873dd3fbf287442aeded96f8bcc1bdc1fd41373e6440100cc8643c2
Source/read-only verification mounts unmounted. Broader SWEET GUI/daemon
root-tweaks deliberately unapplied for minimal first immutable-root attempt.
No XNU/policy/hardware change. UFS stays strictly read-only.
Logs /tmp/marble-iosroot-{build,sparse}.log. Build commit
3858504a05d377b1cd4c5df9e9487429524c8db9 pushed origin marble;
exact Actions39756141953 SUCCESS, independently verified headSha matches.
Inputs13.5/DEVELOPMENT/MARBLE/keep_going=true; full link PASS. Fresh artifact
xnu/out-marble-ci-39756141953, SHA256SUMS PASS. CI log confirms pinned
hfs-627.100.6 staging31d5ec238dfab485e78a9a30b8b92d13e8914f03 and0082.
Kernel SHA256 abe7215eb0365976f32e4fafcb17792438fad16637d50bdbe6c977a8265de2f6
Payload SHA256 bec23d79a321d871f8e43e9bfe24abb80d20d1fd9e6ca2a94067566eaca38137
Boot SHA256 fa05a9ea0e3a2e3ba96604a536862f5c9d70ae9431ce816c3b9c73165df6eeb4
Final shim/out/marble-xnu/latest-marble-xnu.img17137664 bytes.
Exact cmdline:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1
All payload segments match exact linked kernel; no extra root segment or
RAMDisk property; inherited asmb0x6f/u32(1) verified; UFS PA01d84000+3000.
No rd=md0, ufsrw/rootrw. Link zero undefined symbols; HFS/UFS retained;
write/sync/persistent logger symbols absent.4 executable sections zero physical
CNTP instructions and1 CNTV_CTL MSR. Sparse mappings,160-page allocator,
code/stacks/tables/aliases/capacity PASS. Boot-v4 stock-boot repack/inspect,
independent header/bounds/padding/content/locator PASS; no trailing bytes.
Logs /tmp/marble-real-ios-{pipeline.log,ci.log,final-audit.txt,cntp.txt}.
Expected next blocker class (prediction): launchd/daemon writable /private/var
state (SWEET saw EROFS) or absent platform services; no MARBLE Apple userspace
physical result yet. SWEET ignition-level1 evidence documented in guide.
No device commands. REAL IOS USERDATA FLASH NOT PERFORMED.
Manual commands only (userdata replaced; no GPT changes):
fastboot -S 512M flash userdata ~/ios-marble/shim/out/marble-xnu/ios16-root-marble-20H392.simg
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Documentation follow-up does not change above build/kernel provenance.

## Active handoff: MARBLE real iOS root source audit blocked (2026-10-22)

MARBLE INTERNAL-UFS HFS PID1: PASS.
User physically observed Device-WLUN ACTIVE, LUN0 ready, capacity4096,
GPT/userdata, BSD ufsroot0 major1 minor0, HFS MarbleRoot mount, unsealed-root
continuation, codesigning0 and sustained EL0 PID1 heartbeat. This supersedes
all pending internal-HFS physical statements below. User evidence; no device
commands executed by this agent.

Next objective: real iPhone X iOS16.7.16/20H392 HFSX root using existing
mkiosroot.sh apfs-fuse/LZBITMAP workflow. BLOCKED at task1: no DMG/IPSW files
found under /home,/tmp,/mnt,/media,/run/media; historical external SSD path
/run/media/dipa/android/ios-sweet-ipsw is absent. Required source directory:
/run/media/dipa/android/ios-sweet-ipsw/iPhone10,3_16.7.16_20H392/
OS=087-86698-044.dmg; SystemOS=087-86593-047.dmg;
AppOS=087-86715-047.dmg. OS.dmg/SystemOS.dmg/AppOS.dmg are role aliases.
No Apple downloads. User explicitly requires stopping if DMGs absent;
no builder/kernel changes, patch replay, compilation, CI or new images done.
See docs/MARBLE_IOS_ROOT.md for audit and remaining validation.

Existing mkadt.py chosen/asmb is common to MARBLE/SWEET already:
lp-sip0 u64(0x6f), lp-sip1 u32(1). No policy change needed or made.
SWEET physical history supports ignition_level=1 (level0 skips cache stage;
default tries unavailable Preboot; level1 uses root cache hardlinks).
Planned, NOT yet packaged/verified real-iOS cmdline:
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1
No RAMDisk, rd=md0, ufsrw/rootrw or UFS writes. Existing boot image is still
prior test-root build2c1db665 / Actions39751769521; do not represent it as
real-iOS payload. New artifact hashes/run unavailable.
Destination shim/out/marble-xnu/ios16-root-marble-20H392.{img,simg} verified
git-ignored. Workspace free28GiB: space for raw16GiB plus expected sparse
~12GB is tight; reassess actual space before building. /tmp tmpfs13GiB free
is unsuitable for full raw expansion. Source readability/type not verifiable.
Preserve unrelated untracked docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md.
REAL IOS USERDATA FLASH NOT PERFORMED.

## Active handoff: MARBLE first internal HFS test root (2026-10-22)

MARBLE INTERNAL UFS READ PATH: PASS (user physical observation).
ACTIVE PASS; LUN0 READY; capacity PASS (4096-byte blocks); READ10 PASS;
GPT PASS; userdata PASS (LUN0 first block0x2f6a00,229581MiB);
ufsroot0 PASS (BSD root major1 minor0). Controller PA01d84000,size3000,
CAP1587031f,VER300,HCE1,HCS10f; DMA843f44000,size104000.
No RAMDisk; initial sense02/04/02 then exact d0 ACTIVE succeeded.
HFS failure on current Android userdata is expected (signature81c3,
mountfs22,cannot mount root19). NO STORAGE SECTOR WRITES OCCURRED.
This supersedes prior pending physical-readiness statements below.

0029 now shares ONLY mount-time unsealed-root compatibility with MARBLE;
MARBLE ROOT log; SWEET log/behavior unchanged; generic panic and pivot_root
semantics unchanged.0082 and UFS/HFS/hardware source patches unchanged.
Full replay0001..0081 + strict0082 PASS. MARBLE bsd_init real-header arm64
object compile PASS (local reused flags need DRIVER_PRIVATE; modern host
clang pointer diagnostic downgraded for existing mbuf_t header mismatch).
Follow-up local compile using actual recovered CI flags PASS without diagnostic
workaround: /tmp/internal-real-cc.py and internal-objects/bsd__kern__bsd_init.c.o.
SWEET/BCM2837 preprocessed behavior identical before/after; generic panic
retained. MARBLE adds only intended log/continue. UFS preprocessed read-only
exclusions PASS; no WRITE10/sync/parser enabled. Exact CI compile pending.

Local16MiB HFSX built twice deterministically using existing mkmarble-test-root.py;
MarbleRoot root:wheel0755 /sbin/launchd and /dev; static arm64 NOUNDEFS init
f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b matches
proven init. Raw hash467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a
matches proven RAMDisk HFS. fsck -fn PASS (both builds twice and sparse expansion).
HX0005 signature; extracted launchd exact. img2simg + simg2img roundtrip
byte-identical (all16MiB); sparse SHA256
697789be8b0aaaa27dbaa6e85d282a2ca5d9aa9d379a3606e55b0351161f0e6a.
Artifacts shim/out/marble-xnu/marble-internal-root.{img,simg}; untracked/ignored.
Validation /tmp/internal-validate.py, internal-compile.log, internal-bsd_init.o,
internal-second.img, internal-roundtrip.img, internal-launchd.
Automated pipeline next: NO RAMDisk, rd=ufsroot0, no ufsrw/rootrw.
No phone commands; destructive userdata flash requires user's later manual
approval/action. DESTRUCTIVE USERDATA FLASH NOT PERFORMED.
Preserve unrelated untracked docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md.

Exact build2c1db6651ae096df992ced36cd923b31d08c1036 / Actions39751769521
SUCCESS; headSha independently verified. Fresh xnu/out-marble-ci-39751769521;
artifact SHA256SUMS matches. Full CI bsd_init compile and link PASS. Pinned
HFS retained. Full linked kernel zero undefined symbols; UFS/HFS linked;
write/sync/persistent-log symbols absent. MARBLE unsealed-root string present,
mount-time root-auth panic string absent.4 executable sections: zero physical
CNTP instructions,one CNTV_CTL MSR. Exact payload all segments match kernel;
no extra root segment/RAMDisk ADT property; PA01d84000; exact cmdline
 debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0
No rootrw/ufsrw. Sparse bootstrap map/160-page allocator/aliases/stacks/tables
PASS. Shim build, stock boot_a repack, inspect, independent header/bounds/
padding/content/locator PASS. Boot17137664 bytes,no trailing bytes.
Hashes independently reread:
Kernel 031e0b79c9cb3f88bf5675d30cbb9ac22eb2b31b37d1059d381af6ee33f20205
Payload dcf90a7ec79cb24368e01c2dcac312ffd02234c43b179aacb9e2a20f3237de78
Boot 2b8450f3096c0f77a8512b59c557b82acca2747f6318356a953cfca1b99f0c17
Root 467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a
Sparse 697789be8b0aaaa27dbaa6e85d282a2ca5d9aa9d379a3606e55b0351161f0e6a
Final boot shim/out/marble-xnu/latest-marble-xnu.img; root/sparse paths above.
Logs /tmp/marble-internal-{pipeline,ci}.log, /tmp/internal-final-audit.txt,
/tmp/internal-linked-cntp.txt. Existing6 tests and UFS sense regression PASS
(ASan/UBSan; leak detection off due sandbox ptrace limitation). diff checks PASS.
No device commands. Internal HFS physical boot is pending later manual userdata
placement; current Android userdata will still fail HFS as expected.
DESTRUCTIVE USERDATA FLASH NOT PERFORMED.
Documentation-only follow-up records results; kernel provenance stays above.
Manual boot (after the user separately handles root placement):
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img

## Active handoff: MARBLE UFS readiness classifier correction (2026-10-22)

User-reported first physical XNU UFS boot (2026-10-22): no RAMDisk;
ADT PA 0x01d84000, register size 0x3000; MMIO 0xfffffe30062c0000;
contiguous DMA PA 0x843f44000 size 0x104000. CAP 0x1587031f,
VER 0x300, HCE 0x1, HCS 0x10f. NOP PASS; READ_FLAG fDeviceInit PASS,
value 0. Initial LUN0 TUR: OCS 0, transaction 0x21, response 0x01,
status 0x02, valid sense 02/04/02; result EIO (5). Device-WLUN ACTIVE
was NOT ATTEMPTED: the classifier incorrectly required response=0.
IOFindBSDRoot reported ufsroot0 unavailable: 5. These are user observations.

0082 removes response==0 only from the exact bounded initializing-sense
classifier, matching stage-0. Generic SCSI/query success stays strict.
Exact d0/1b0000001000 ACTIVE is unchanged; request TT/flags/LUN/length/PRDT/
CDB and completion OCS/TT/response/status diagnostics added only for ACTIVE.
No write routes added. HFS/timer/GIC/CNTP protections unchanged.
Local PASS: full0001..0081 replay + strict0082, real-header arm64 compile,
SWEET equivalent preprocessing, exact physical tuple + fixed/descriptor malformed/
short/negative sense ASan/UBSan regression; actual readiness single-ACTIVE/error/
timeout tests;262144 submission whitelist cases + mutated ACTIVE rejection;
read/GPT ASan/UBSan; MARBLE preprocessed write-route exclusions; six existing
tests. Old0082 hardware/HFS/CNTP/GIC/timer prefix byte-identical. diff check PASS.
Automated exact CI/package completed below; no RAMDisk, rd=ufsroot0, no rootrw/ufsrw.
No phone commands. Preserve unrelated untracked breadcrumb document.

Exact build 8ffd2c8f1be4f60557c6ceb178a1c794758b8ac0 / Actions39749948026
SUCCESS, exact headSha independently verified; fresh xnu/out-marble-ci-39749948026.
Artifact SHA256SUMS PASS. Actual ACTIVE construction host test PASS: TT01 flags00,
LUNd0, expected length0, CDB1b0000001000, no data, no PRDT. Full linked kernel
zero undefined symbols, HFS/UFS retained, write/sync/logger symbols absent.
Four executable sections: zero physical CNTP instructions, one CNTV_CTL MSR.
Independent payload exact-segment/no-RAMDisk/rd=ufsroot0, sparse-map/160-page
allocator/aliases/stacks/tables and boot-v4 header/padding/content audits PASS.
BOARD=marble-xnu + stock boot_a repack/inspect PASS. No rootrw/ufsrw.
SHA256 independently reread:
Kernel  2ab790b36885bb2d52b0813133d3ea8fcafcf271d5b4904a7dcd55fbb353eff6
Payload e62944520fe5093e870b9c443ec9232189bd2a9bf56dcb2a04c3707ef53da336
Boot    16c78dd824e69cabd8580a77133c99f27e855c0a2b8625dbe241c245cd0b9761
Final image: shim/out/marble-xnu/latest-marble-xnu.img.
Logs /tmp/marble-ready-pipeline.log, /tmp/ready-final-audit.txt,
/tmp/ready-linked-cntp.txt. Corrected XNU physical result pending user's test.
Expected next: TUR sense02/04/02 failure, device-WLUN ACTIVE LUN d0
CDB1b0000001000, request/completion/result, then TUR polling if ACTIVE succeeds.
ACTIVE success remains stage-0 evidence only. No phone commands executed.
Documentation follow-up does not change kernel provenance.
Manual: fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img

## Previous handoff: MARBLE read-only UFS root (2026-10-22)

USER PHYSICAL MILESTONE: HFS RAMDisk fully successful: mockfs declines non-Mach-O,
hfs mounts MarbleRoot; hfs-627.100.6 registered, launchd exec/codesigning0,
EL0 PID1 and indefinite heartbeat. All kernel/scheduler/GIC/timer/SGI/BSD/MD/HFS/
root/exec/PID1 scheduling PASS. Supersedes older pending HFS statements below.
User also confirms later stage0: NOP/READ_FLAG0, initial TUR02/04/02, correct
DEVICE WLUN d0 ACTIVE1b0000001000 succeeds, LUN0 ready, capacity4096, data/MBR/
GPT/entries/userdata reads PASS, no sector writes. Supersedes older DEVACT
untested entries. Numeric MARBLE values are now recorded in the newer handoff above.

Reuse sweet_ufs.c via appended0082 after unchanged0001..0081. MARBLE reads
/marble-ufs/reg PA01d84000+3000 from ADT (base matches actual shim/board.h).
Same UFSHCI descriptors/ownership/polling/DMA model as SWEET; MARBLE adds proven
NOP/read-flag/TUR/exact gated d0 ACTIVE readiness, runtime capacity4096 check,
CAP/VER logs, CRC-checked GPT and stronger read bounds. Compile out all MARBLE
WRITE10/sync/log/ufsrw/physio-write paths; FWRITE/strategy/raw write EROFS,
submission whitelist, timeout poisoning, high-DMA CAP64 check and cache flushes.
SWEET behavior unchanged modulo preprocessor line numbers/string formatting.
HFS/MD5/hardware/MMU/timer27/SGI1/GIC/CPU0/EL0 old0082 prefix byte-identical.

Local PASS: full replay0001..0081 + strict0082; both changed units real-header
arm64 compile; SWEET preprocessed equivalence; no preprocessed MARBLE write
constructors/parser/log thread; host actual read/GPT and readiness functions
ASan/UBSan PASS incl CRC/overflow/bounds/gate/single ACTIVE/timeout;6 existing
MARBLE tests PASS incl ADT UFS assertions; old-kernel sparse map preflight PASS
(reference only); diff check PASS. /tmp/ufs-* holds scripts/objects/audits.
Full link validated in exact Actions run below (Linux has no full XNU SDK).
Details docs/MARBLE_UFS_ROOT.md. Pipeline completed with
--cmdline-extra rd=ufsroot0, NO --ramdisk. No rootrw/ufsrw. No phone commands.
Do not modify userdata; mount failure after ufsroot0 discovery is expected.

Exact build2ef4386a869373468ad31ac614206e7fb5367ecb / Actions39733746933
SUCCESS (4m1s); headSha independently verified. Fresh exact artifact directory
xnu/out-marble-ci-39733746933; kernel SHA256SUMS independently matches.
CI logs verify pinned hfs-627.100.6 staging31d5ec238dfab485e78a9a30b8b92d13e8914f03
and both changed units compiled. Full link zero undefined symbols; UFS root and
HFS registration/mount symbols present; UFS write/sync/persistent-log symbols absent.
Linked4 executable sections: zero physical CNTP instructions,1 CNTV_CTL MSR.
Additional actual submission-guard ASan/UBSan test passes262144 opcode/LUN/gate/
direction cases and mutated ACTIVE rejection. No change after build to source.
Exact payload has command line debug=0xc serial=3 cpus=1 keepsyms=1
-enable_kprintf_spam rd=ufsroot0; ramdisk None, no RAMDisk ADT property, no extra
root segment, every segment byte matches exact CI kernel. ADT UFS PA01d84000.
ADT842128000 size3956, boot_args84212c000, top842130000;160-page allocator
ends8423b0000. Exact sparse loaded-segment/stack/table/alias/arena/capacity PASS.
BOARD=marble-xnu build/stock boot_a repack/inspect and independent post-write
header/bounds/padding/shim/payload/MRBLXNU1 locator checks PASS, no trailing bytes.
Kernel SHA256 46316df9660a03575cf70b71395ce7b830cf9ea012c8deefb19dc6b25f032912
Payload SHA256 642f1064efbc302121fc2cfe907239116f8e050ea629c2f23e3bde92670efedf
Boot SHA256 a94b786b5ecf634971697a47edb762672883cee75714e77903d19c06eee9b2bd
Final image shim/out/marble-xnu/latest-marble-xnu.img; hashes independently reread.
Logs /tmp/marble-ufs-{pipeline,ci}.log, /tmp/ufs-{final-audit,linked-cntp,
static-audit,host-audit,readiness-audit,opcode-audit}.txt. Documentation-only
follow-up records results without changing kernel provenance. No phone commands.
Physical XNU result superseded by the newer handoff above. Success boundary: userdata discovery + BSD root
ufsroot0; existing Android/encrypted/non-HFS mount failure is expected.
Next user manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Do not write/format/flash userdata. Preserve untracked breadcrumb doc.

Earlier handoffs below are historical.

## Active handoff: MARBLE HFS RAMDisk root (2026-10-22)

**MARBLE PHYSICAL PID1 SUCCESS**: user reports physical latest mockfs boot:
mockfs mount result 0; codesigning result 0; PID 1 heartbeat sustained
indefinitely. RAMDisk/md0/BSD root/missing-IOMedia/exec/EL0/liveness PASS.
This supersedes the pending physical results below. No independent device test.

Port shared SWEET HFS to MARBLE with smallest config delta in0082:
FILESYS_BASE adds sweet_hfs; MARBLE registration/decline diagnostics only.
0026 staging already accepts MARBLE and retains pinned hfs-627.100.6 commit
31d5ec238dfab485e78a9a30b8b92d13e8914f03; only comments/status clarified.
0082 already shares Makefile flags and portable MD5. No new crypto or UFS work.
New deterministic tools/mkmarble-test-root.py builds16MiB HFSX MarbleRoot,
root:wheel0755 /sbin/launchd and /dev; init byte-identical to proven mockfs.
Pipeline regenerates init/HFS after exact CI artifact download, rd=md0.
Details docs/MARBLE_HFS_RAMDISK_ROOT.md.

Local PASS: full replay0001..0081 + strict0082;40 HFS units and4 MD5 objects
compile with real headers; SWEET preprocessing byte-identical; hardware/timer/
MMU/GIC/crypto source unchanged. fsck.hfsplus -fn PASS twice per image;
independent extraction exact; two builds byte-identical; mode/owner verified.
Init f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
HFS467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a
Preflight old-kernel HFS payload sparse-map/160-page arena/ADT/rd=md0 PASS.
Existing6 tests PASS; shell syntax/diff checks PASS. /tmp/hfs-* holds audits.
Build commit00e9810ed9f6b44768c781f2c5e56af8fefe9c55 pushed origin marble.
Exact Actions39731873003 completed SUCCESS with13.5/DEVELOPMENT/MARBLE/keep_going=true.
Final link/package audits and hashes recorded below.
No phone commands. HFS physical boot remains pending user's manual test.

Exact build00e9810ed9f6b44768c781f2c5e56af8fefe9c55 / Actions39731873003
SUCCESS, headSha independently verified; fresh artifact xnu/out-marble-ci-39731873003.
CI log verifies pinned staging and all40 HFS compile commands; full kernel has
zero undefined symbols, linked HFS registration/getvoluuid and portable MD5.
Four executable sections: zero physical CNTP instructions, one CNTV_CTL MSR.
Post-CI init rebuilt unchanged;16MiB HFSX rebuilt same hash, fsck -fn twice OK,
independent launchd extraction exact, catalog root:wheel0755 verified.
Exact payload/map PASS: RAMDisk[842128000,843128000), ADT843128000,
boot_args84312c000, top843130000;160-page arena ends8433b0000. Sparse map,
owned tail, aliases, stacks, tables and allocator capacity PASS. No hardware
source changes; timer27/SGI1/GIC/MMU protections retained.
BOARD=marble-xnu and stock boot_a repack/inspect PASS; independent post-write
header/boundary/padding/shim/payload verification PASS, no trailing bytes.
Kernel SHA256 721c31711460cebefc9dc0fca1adf9a02c78fce63c8b6aa7a267e3715168bd2a
Test init SHA256 f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
HFS root SHA256 467df791de4da04e157ac074852d82371d158d95ba45977b4bea9ede75feab7a
Payload SHA256 871dfbfa40e96e9ac9d7453b1aaff973eeb5318ce16cd05c9aa9e70d0afb2f26
Boot SHA256 00dc9f0fd6af2891ef15ac4e8dc26ffe53702fbe4b5330f66fbe70400e21420a
Final image shim/out/marble-xnu/latest-marble-xnu.img; hashes independently reread
and CI kernel SHA256SUMS verified. Logs /tmp/marble-hfs-{pipeline,ci}.log,
/tmp/hfs-{final-map,linked-cntp,linked-symbols,linked-undefined}.txt.
No phone/device commands, UFS/physical-storage changes or real iOS userspace.
HFS physical mount/PID1 is pending manual observation; only mockfs PID1 has
physical proof. Documentation follow-up does not change kernel provenance.
Next manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Expected: mockfs declines non-Mach-O, hfs mounts MarbleRoot, /sbin/launchd,
MARBLE PID1 banner and sustained heartbeat. Preserve unrelated breadcrumb doc.

Earlier handoffs below are historical.

## Active handoff: MARBLE missing IOMedia correction (2026-10-22)

User physical run899bfb1f59c66e9091d5bd16376899ac66aec219 / Actions39728864936:
RAMDisk discovery PASS; md0 creation PASS; BSD root md0 PASS;
setRootMedia entered PASS; publishHiddenMedia FAIL: missing IOMedia class
assertion IOService.cpp:5130. Exact hashes recorded in docs/MARBLE_RAMDISK_ROOT.md
and prior handoff below. This is user evidence, not an independent device test.

0082 adds only MARBLE early missing-IOMedia log/return before assertion.
Existing missing IOBlockStorageDriver handling retained: root NULL, unhide,
publishHiddenMedia(NULL), safe return. Immediate root/vfs/mockfs audit found no
further required storage-class assertion. No hardware/UFS/mockfs/init changes.
Helper now rebuilds known MARBLE static init after exact CI download.
Local PASS: full replay0001..0081 + strict0082, real-header MARBLE IOService.cpp
compile, preprocessing/object null branch log/return before assertion; SWEET
preprocessing equivalent except __LINE__, existing non-MARBLE assertion intact.
Other generated XNU source unchanged; timer27/SGI1/GIC protections unchanged.
Artifacts /tmp/iomedia-*; exact linked CNTP/map/root audits pending new CI.
Build commit fde3aa2f4036218de4f2c0fac2dfa9158eef8f80 pushed to origin marble.
Exact Actions39730114255 running; helper will package with rd=md0.
Next: verify exact linked kernel and payload, then record final hashes. No phone commands. Physical mockfs/PID1 remains unproven.


Exact build fde3aa2f4036218de4f2c0fac2dfa9158eef8f80 / Actions39730114255
SUCCESS; headSha independently verified. Fresh artifact xnu/out-marble-ci-39730114255.
Helper rebuilt static init after CI; root hash unchanged. Linked publishHiddenMedia
CBZ at fffffe000795159c branches to log/return at fffffe0007951808.
Four executable sections: zero physical timer instructions, one CNTV_CTL MSR.
Final exact payload audit PASS: root bytes, rd=md0, RAMDisk[8420ac000,8420b4000),
ADT8420b4000, boot_args8420b8000, top8420bc000,160-page arena ends84233c000.
Timer27/SGI1/GIC protections unchanged (no changes outside the requested guard).
Boot-v4 repack/inspect PASS,16654336 bytes, no trailing bytes. Final hashes:
Kernel 7914ad6a24488fa8ef6eac3b710cce443cdda86ef1d929bd7a3d220aba0828e9
Init/root f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
Payload 7627016addc520457b15b3d44e6fe056194ce36bf17c57f18588c09908283202
Boot 788b0210792991528c6a83401cd8417948d85a55af5e5db2f422c912c74f45b0
Final image shim/out/marble-xnu/latest-marble-xnu.img; hashes independently reread.
Logs /tmp/iomedia-{pipeline.log,linked-cntp.txt,linked-publish.txt,final-map.txt}.
No physical commands run; mockfs/PID1 pending user observation. Documentation-only
follow-up commit does not change kernel provenance. Next manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Expected next new breadcrumb: MARBLE ROOT: no IOMedia class, skip hidden-media publish
then setRootMedia complete, mockfs mount begin, and either PID1 or a precise blocker.

Earlier handoffs below are historical.

## Active handoff: MARBLE mockfs RAMDisk PID 1 (2026-10-22)

User physical observation of latest boot: Skywalk self-tests PASSED, BSD
kinit, lo0/gif0/stf0 and !BSD, then IOFindBSDRoot waits for IOMedia/Apple_HFS.
No panic. This supersedes the suspected zone hang: root-filesystem boundary
reached, same as SWEET. No independent physical test this session.

Diagnostic changes: append minimal MARBLE missing-storage-class exceptions and
root/mount/signature breadcrumbs to0082; reuse sweet-init.S with MARBLE_INIT;
static signed Mach-O itself is mockfs root /sbin/launchd,16635 bytes. Helper
accepts --ramdisk and --cmdline-extra; exact extra rd=md0, no rootrw/UFS work.
Payload audit checks packed RAMDisk ADT/placement/bytes and enlarged sparse
owned tail plus160-page arena. docs/MARBLE_RAMDISK_ROOT.md has format, rebuild
commands and failure boundaries. Existing hardware patch sections untouched.

Local PASS: replay0001..0081, strict0082; real-header arm64 objects for all4
changed XNU units; SWEET preprocessing equal except __LINE__ derivatives; SWEET
init byte-identical; MARBLE deterministic static signed LC_UNIXTHREAD Mach-O;
packed RAMDisk ADT/placement/cmdline; enlarged sparse map and160-page arena;
timer27/SGI1/Group1 and zero GICR group/priority MMIO. Original0082 prefix
byte-identical. Prior linked kernel has zero physical timer instructions; exact
new kernel scan pending CI. Shell syntax, existing MARBLE tests and diff check
PASS. /tmp/ramdisk-* contains compile/comparison/audit artifacts. No device
interaction. Build commit899bfb1f59c66e9091d5bd16376899ac66aec219 pushed;
exact Actions39728864936 SUCCESS, headSha independently verified. Exact
xnu-kernel downloaded fresh to xnu/out-marble-ci-39728864936. Init rebuilt
again after CI success, same hash; all ad-hoc CodeDirectory page hashes checked.
Helper generated MARBLE ADT, payload WITH root + rd=md0, BOARD=marble-xnu
shim, stock boot_a repack and boot-v4 inspect. Independent post-write boot
header/bounds/padding/shim/payload+MRBLXNU1 locator comparison PASS.
New linked scan:4 executable sections, zero physical timer instructions,
1 CNTV_CTL MSR. Exact payload/map audit PASS: RAMDisk[8420ac000,8420b4000),
ADT8420b4000, boot_args8420b8000, top8420bc000;160-page allocator ends84233c000.
RAMDisk does not overlap kernel/stacks/tables/ADT/boot_args/allocator.
Final image16654336 bytes: shim/out/marble-xnu/latest-marble-xnu.img.
SHA256 kernel55f32622881732e32aa488283930d3c678425d1c005df25f5a1d974535f22026
init/root f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
payload fa98545b33b3ec474aeba86e51c06a416160039a584309c81d0973d017bf5d45
boot54f4375a0e0d83eb48ccdd4e736e5b977e670c34e92e95b78cae4d8e0b88a277
ADT008deddef65f712e00536a03b66208143b957cf0d21a483200c181a91c15ffa3
shim586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05
Hashes independently re-read. /tmp/ramdisk-pipeline.log, final-map.txt,
final-cntp.txt preserve packaging and linked validation output. This follow-up
handoff is documentation only; kernel provenance remains899bfb1/39728864936.
No physical-device commands run. New physical PID1 behavior remains unproven.
Next user manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Observe RAMDisk/property, Added memory device md0, BSD root md0, setRootMedia,
mockfs, exec/signature boundaries, then MARBLE USERSPACE banner and heartbeat.
No UFS work or storage writes. Preserve unrelated untracked breadcrumb doc.


Earlier handoffs below are historical.

## Active handoff: MARBLE zone hang diagnostics (2026-10-22)

User physically booted CNTP-fix commit62b42e842515f6389732cb6ad30beaf460bc4a2e,
Actions39724251384 (kernel650a50bf9e0e174f14ddf41111e11fd61760a318a2f48d6ef8009031fe9aea2b,
payload5562faacc4c8774909c13b37d4cf73b3096e158075b2bf47cd666d2b56743211,
boot2fc4b0b8d93c534c48a0b8cfecbf11c978f96b33e912369b14bc6945ce841365).
CNTP skip PASS. MMU/GIC/CNTV/VM/IOKit/scheduler/security/platform expert/CPU0
registration and SGI1 PASS: "MARBLE CPU: boot CPU 0 registered, SGI1 verified,
initialization complete". User reports hard hang after visible map RO, >1 minute,
no panic/reboot. Earlier GEN0..DATA/metadata/VM bootstrap lines also visible.
These are user observations, not an independent physical test this session.

Exact source: zone_init has ONE startup-table registration, normally before
IOKit/clock_init. No normal second-entry call path found. fbcon wraps rows,
does not scroll; photograph vertical order cannot establish execution order.
processor_start(master) explicitly invokes cpu_machine_init, no new idle/startup
thread, reset jump or startup dispatcher. Current SWEET0065 MOVED the call to
startAll, still includes CPU0. Upstream AppleARMSMP initial start loop likewise
calls processor_start for all CPUs. Retain MARBLE call; no CPU fix justified.

0082 appends only MARBLE zalloc diagnostics: static per-boot invocation counter,
entry/completion generations, submap entry plus before/after early-map register,
kmem_suballoc, guard1, guard2 and completion; metadata boundary. Existing timer_cnt
printed t= (includes software SIGPdec handling, NOT exclusive CNTV IRQ proof).
Normal zone_init precedes clock_init, so t=0 is plausible. No allocator behavior
or baseline mapping/timer/GIC/ADT/loader/UFS/CPU-count changes. Detailed audit,
expected sequence and stopping-point interpretation: docs/MARBLE_ZONE_HANG.md.

Local PASS:81 reverse/replay + strict0082 check/apply; real-header MARBLE zalloc.c
Mach-O compile; SWEET full preprocessing byte-identical including __LINE__;
all old0082 sections identical; physical timer absent in relevant preprocessing/
object; timer27/SGI1/Group1 unchanged and zero GICR group/priority MMIO;
zalloc object inspection; diff check. /tmp/zone-* contains validation artifacts.
Milestone: diagnostic source/report committed and pushed as
b3008501e9a78e92c2d2005cfd0cb59ac190f1a8. Exact Actions39726707388 running
with13.5/DEVELOPMENT/MARBLE/keep_going=true. Helper passed commit/push/dispatch;
Run39726707388 SUCCESS (build3m14s), headSha independently confirmed.
Exact xnu-kernel downloaded to xnu/out-marble-ci-39726707388. Linked executable
scan: four code sections, zero physical timer instructions, one CNTV_CTL MSR.
Linked zalloc disassembly confirms all requested bracketing calls. Sparse linked
map audit PASS with actual3760-byte ADT:160-page arena, owned tail/stacks/tables,
alias attributes/framebuffer/capacity. No forbidden MMU/GIC/timer/ADT change.
Helper regenerated ADT/payload with debug=0xc serial=3 cpus=1 keepsyms=1
-enable_kprintf_spam; BOARD=marble-xnu build, stock boot_a repack, boot-v4 inspect
and independent post-write boundary/padding/content verification all PASS.
Final image16637952 bytes: shim/out/marble-xnu/latest-marble-xnu.img.
SHA256 kernel c400971ea61ba2ddaf85a41555dbf38f8fa7934e2b8ab0513767c35b0c308ecd
payload f217a87648ab904fa3c98b165a3ad5591048dbc4f40e83d905b01e165332fded
boot 241d78fd768336db70e13e9be50a9ae6cdc5674287a5cdc474ed3bb86f1f87bd
ADT 2f324b0344746d2eb9beb6fbf5725d0506135e6fc291bd1d9359b4e2d5e408e9
shim 586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05
Hashes independently re-read. /tmp/zone-new-linked.txt, zone-linked-map.txt and
zone-linked-disassembly.txt record final audits. Physical boot pending; no claim
that this diagnostic fixes the hang. Next user manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Collect generation and newest boundary beside blank cursor rows. No automatic
phone interaction. Follow-up documentation commit does not alter kernel provenance.
No physical-device interaction; final image must be booted manually by user.

Earlier handoffs below are historical.

## Active handoff: MARBLE CNTP trap (2026-10-22)

User exact physical run39723141106 / commit27eba3872b069658c5e109a4d59790aea2725d03
proves redistributor discovery, WAKER, IGROUPR0 skip, ISENABLER0 08000002,
ICC_SRE, BPR1/PMR/CTLR, GICD_CTLR and ICC_IGRPEN1 all PASS. CNTV_CTL_EL0
write PASS; CNTP_CTL_EL0 UNDEFINED/TRAPPED at PCfffffe000747b9e8,
_fiq_context_init+0x14, instructiond51be228 msr CNTP_CTL_EL0,x8.
This is user-provided physical evidence; EL2 trap policy remains unknown.

0082 only machine_routines.c changes: MARBLE retains CNTV enable, skips
precautionary CNTP mask and prints "MARBLE TIMER: CNTV enabled, CNTP skipped".
Four blank lines removed to preserve exact SWEET preprocessing/line numbers.
No other0082 section or ADT changed. Report docs/MARBLE_CNTP_TRAP.md.

Local PASS: full81 reverse/replay; strict0082 application; real-header arm64
machine_routines.c compile and disassembly (CNTV MSR present, CNTP absent);
SWEET preprocessing byte-identical; source/encoding audit and relevant MARBLE
preprocessing show no remaining physical timer instruction; cpu_timebase_init
CNTPCT comment actually calls CNTV hwclock. GIC real-header compile/preprocess
PASS: timer27/SGI1/Group1 unchanged, zero group/priority MMIO. Other sections
identical, git diff --check PASS. Artifacts /tmp/cntp-* and /tmp/gic-*.

Milestone: source/docs committed and pushed as
62b42e842515f6389732cb6ad30beaf460bc4a2e. Exact workflow run39724251384
is building that commit with requested13.5/DEVELOPMENT/MARBLE/keep_going=true.
Run39724251384 SUCCESS (build4m33s); exact xnu-kernel artifact downloaded to
xnu/out-marble-ci-39724251384. Plain arm64 linked kernel verified: four
executable sections scanned by instruction encoding, zero physical timer
instructions; one CNTV_CTL MSR. fiq_context_init atfffffe000747b9d4 retains
CNTV MSR atfffffe000747b9e0 and calls kprintf; old fault PC now ADD.
Linked sparse-bootstrap audit PASS with actual3760-byte ADT;160-page arena,
all aliases/stacks/tables/attributes/capacity verified. Exact ADT regenerated
with unchanged generator (random seed/hash naturally regenerated).
Payload cmdline debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam.
BOARD=marble-xnu shim build PASS; stock marble-boot-backup-clean/boot_a.img
repack PASS; boot-v4 inspect and independent post-write verification PASS.
Final image16637952 bytes: shim/out/marble-xnu/latest-marble-xnu.img.
SHA256 kernel650a50bf9e0e174f14ddf41111e11fd61760a318a2f48d6ef8009031fe9aea2b
payload5562faacc4c8774909c13b37d4cf73b3096e158075b2bf47cd666d2b56743211
boot2fc4b0b8d93c534c48a0b8cfecbf11c978f96b33e912369b14bc6945ce841365
ADT1183df8745240237a022823da65c77a6d240d7d33c226f20d39bc45c8de40c98
shim586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05
Hashes independently re-read after packaging. Full linked audit output
/tmp/cntp-new-linked.txt, /tmp/cntp-linked-map.txt. Hardware result pending.
Next user manual command:
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
Final follow-up commit records results only; kernel provenance remains62b42e8. Old exact kernel instruction scan independently
finds its sole physical timer instruction at user-reported PCfffffe000747b9e8.
Stop at verified latest-marble-xnu.img; user manually boots. No device command.

Earlier handoffs below are historical.

## Active handoff: MARBLE GICR_IGROUPR0 SEA experiment (2026-10-22)

User physical exact Actions39719201880 clears allocator/bzero crash and reaches
complete arm_vm_init, serial/kprintf and later PE initialization. New SEA:
PCfffffe0007a01e08 LRfffffe0007a01df4 FARfffffe000b3e8080 ESR96000010.
Local allocator kernel confirms _pe_init_fiq+0x1a0 = b8080d09,
str w9,[x8,#0x80]!; preceding add0x10000 and mov-1 prove IGROUPR0.
PE VAfffffe000b3d8000 +0x10080 = FAR, PA17190080.

0082 changes only pe_fiq.c: MARBLE skips IGROUPR0 entirely, preserves existing
priority-window exclusion and ISENABLER0(timer27|SGI1), adds granular MARBLE
breadcrumbs around discovery/WAKER/enable/ICC/GICD. SWEET preprocessed output
byte-identical including __LINE__; three blank lines removed to preserve it.
ADT warnings audited (generic master string vs empty property; missing debug
node), ADT unchanged. Exact source/report: docs/MARBLE_GICR_IGROUPR0.md.

Observed PASS: reverse/replay0001..0081, strict0082 check/application, real-header
MARBLE pe_fiq.c arm64 Mach-O compile/preprocess; no preprocessed IGROUPR0 or
IPRIORITYR MMIO, enable mask08000002, Group1 ICC writes, all other patch
sections byte-identical, git diff --check. Artifacts /tmp/gic-*.
Safe for diagnostic Actions BUILD; full new link and physical result pending.
No new CI run, commit/push (explicitly prohibited), device/storage operation.
Next: separate Actions build and temporary boot; if enable begin appears but
done does not, collect saved state to test ISENABLER0 accessibility. Preserve
working MMU/arena and all firmware-owned security/priority configuration.

Earlier handoffs below are historical.

## Active handoff: MARBLE early allocator arena (2026-10-22)

User physical run39717047014 reaches MMU-on arm_vm_init; exact original
abort bzero+0x1c first store, LR arm_vm_init+0x1b4, FAR=x0
fffffe00080b4000 ESR96000047. Exact local safe kernel symbols agree.
Root cause confirmed: initial avail_start/topOfKernelData PA8420b4000
translates to that FAR, precisely the exclusive sparse WB endpoint.

0082 adds bounded160-page/0x280000 early allocator capacity in BOTH aliases
as WB/RW/AF/PXN/UXN L3s, replacing Device identity pages. Existing layout
arena[8420b4000,842334000); future link reads actual T. Bound:2 roots+2 L2+
16 kernel L3+138 conservative physmap L3+low globals1+framebuffer1.
Pool/aperture/L1 limits checked after extension. Three MARBLE-only stage7
labels surround invalid_tte/cpu_tte. All other assembly/patch sections
unchanged. Full reasoning/validation: docs/MARBLE_EARLY_ALLOCATOR.md.

Observed PASS:81 replay, strict0082 application, diff check; full real-header
start.s preprocessing/arm64 assembly, arm_vm_init.c Mach-O compile; actual
constructor QEMU8192 descriptors/all160 arena pages; linked-layout policy
audit; SWEET preprocessing identical (__LINE__ normalized); zero MARBLE
GICR_IPRIORITYR. Audit tool defaults160 pages; option0 reproduces old map.
Safe for Actions BUILD. No full kernel link, new physical boot or CI run.
No commit/push per explicit user request; no device/storage operation.
Next: separately build, audit new link with actual ADT size, temporary boot
and observe invalid_tte/cpu_tte zeroed labels and subsequent progress.
Artifacts /tmp/arena-* and /tmp/mmu-start.{s,o}. Earlier handoffs historical.

## Active handoff: MARBLE original early-abort capture (2026-10-22)

User reports real POCO F5 sparse-map boot reaches SWEET EARLY 1..7,
including cpu_init and entry to arm_vm_init. Working MMU/cache/SCTLR baseline
is preserved. User symbolication of exact Actions 39715458390 artifact:
PC fffffe00073c3608 = vm_fault_internal+0x6c, LR fffffe00073c3504 =
vm_fault$XNU_INTERNAL+0x14; ldrb w8,[x0,#0x9e], x0=0, ESR96000006,
FAR9e. This is user-provided evidence, not a new hardware test here.

0082 changes only sleh.c behavior: MARBLE-only sweet_early.h include and
kernel_map == VM_MAP_NULL guard at the very start of handle_kernel_abort,
before current_thread/recovery lookup, DTrace and fault classification.
Prints stage8 "early kernel abort before kernel_map", then
panic_with_thread_kernel_state("MARBLE early kernel abort before kernel_map initialization", state).
No recovery, early map initialization, or mapping changes. Existing diagnostics
retained. Patch uses expanded context/whitespace-neutral replacements.

Exact local xnu-8796.141.3 source confirms map=kernel_map for kernel/no-recovery
faults; translation faults skip arm_fast_fault and call vm_fault(map,...).
Non-translation VM faults access map->pmap before that call. vm_fault forwards
its first vm_map_t argument unchanged to vm_fault_internal, whose first map
read is map->never_faults. Thus NULL map explains the reported secondary
read at9e; original PC/ESR/FAR remain unknown until physical diagnostic boot.

Observed PASS: reverse/replay0001..0081, strict0082 check/application;
real-header MARBLE sleh.c plain-arm64 Mach-O compile (/tmp/abort-sleh.o,
/tmp/abort-compile.log); SWEET preprocessing byte-identical with __LINE__
normalized (line-number-generated identifiers/panic locations otherwise shift);
zero preprocessed MARBLE GICR_IPRIORITYR; every non-sleh.c patch section
byte-identical to task start; git diff --check. No full kernel link or new boot.
Safe for diagnostic Actions build; next output expected stage8 + original
saved-state panic if the early NULL-kernel_map hypothesis holds.
No CI dispatched, no new run ID, commit/push/device/storage operation.
Explicit user no-commit/no-push overrides repository default.
Artifacts: /tmp/abort-before.patch, /tmp/abort-before-sleh.c,
/tmp/abort-{edit,finish}.py, /tmp/marble-mmu-tree/xnu.
Next: separately build exact diagnostic artifact and temporary boot to collect
original PC/LR/SP/ESR/FAR/registers. Do not modify the working MMU baseline.

Earlier handoffs below are historical.

## Active handoff: MARBLE sparse bootstrap mapping experiment (2026-10-22)

User physical staged result: original SCTLR=0x30d00988, white bits
3,7,8,11,20,22,23,28,29. E/E2 YES; M_OK and all later tiles/red NO.
No new hardware test here. All preserved staged SCTLR formulas unchanged.

0082 now maps whole high aperture Device/XN, with paired 16KiB L3s promoting
only nonempty Mach-O segments and owned tail through topOfKernelData to WB.
Unknown KVA pages invalid, both normal aliases identical; executable initprot
pages PXN0/UXN1, data/table pages XN. Pool supports 16 physical L2 blocks
(512MiB), fails closed on overflow/layout/alignment problems. TCR/TTBR/MAIR,
cache operations, loader/ADT/GIC/UFS/SMP/framebuffer descriptors unchanged.
Full report: docs/MARBLE_SAFE_BOOTSTRAP_MAP.md. Linked audit tool:
python3 tools/marble-bootstrap-audit.py KERNEL --adt-size ACTUAL_ADT_BYTES.

Additional observed defect: staged kernel framebuffer table PA0x841b67000 is
only4KiB aligned; linker forces __bss alignment0x1000. Pool and framebuffer
table now use existing __DATA,__data section (link alignment0x4000). Real C
object confirms alignment14 and aligned symbols; runtime guards added.
This is a second mapping correction: future M_OK cannot uniquely isolate
carve-out speculation. Old M_OK absence could also reflect framebuffer fault.
Old broad map is127 WB blocks (not128), PA0x840000000..0x93e000000, because
helper floors adjusted remaining memSize after header offset0x1004000.

Observed PASS: full reverse/replay0001..0081 + strict0082 check/apply;
real-header start.s preprocess/plain-arm64 Mach-O assemble; actual
arm_vm_init.c C cross-compile; extracted emitted constructor executed in
QEMU one/two-block cases (4096/8192 L3 descriptors), gaps/code/data/tail and
zero-size lower segment; both changed files SWEET preprocessing byte-identical;
other patch sections and snapshot/cache/register/staged SCTLR code unchanged;
zero MARBLE GICR_IPRIORITYR; cold OSLAR exclusion; diff check. Old-image
reference policy audit checks symbols/stacks; default rejects missing pool.

Read-only inspection of106 FDTs in vendor_boot/dtbo backups found no explicit
reserved reg overlapping high aperture. Dynamic alloc-ranges can include it
(va_md/demura/ramoops); actual allocated PAs/XPU policy unknown. Dumps stay /tmp.

Safe for diagnostic GitHub Actions BUILD. No full new link: exact new linked
WB endpoints/table/stack PAs pending; do NOT reuse reference addresses as new.
Next: separately build, run linked audit with exact ADT size before packing,
then temporary boot to observe E/E2/M_OK and later tiles. No CI run/ID,
commit/push/device/storage operation; explicit no-commit instruction retained.
Artifacts /tmp/safe-{before.patch,before-start.s,edit.py,regenerate.py,check.py,
qemu.py,qemu-multi.py,image-audit.txt,arm_vm_init.o,vm-object.txt,reserved.py,
reserved.txt}; /tmp/mmu-start.{s,macros,o}; /tmp/marble-mmu-tree;
/tmp/safe-vm-command.json. Existing untracked breadcrumb/MMU docs retained.

Earlier handoffs below are historical.

## Active handoff: MARBLE staged SCTLR experiment (2026-10-22)

User physically confirms cache experiment: all pre-MMU checks green, CACHE/E/E2
visible, F/sync-red absent. IVAC/IALLU completed. New experiment preserves all
existing diagnostics and all translation/cache-maintenance configuration.
Cold MARBLE snapshots original SCTLR into proven-dead x14, encodes all 64 bits
as white=1/dark-blue=0 cells (bit0 leftmost x0, stride16, 8x16 at y2208), then
writes preserved M-only, adds I, adds C, finally writes XNU 0x3454593d. Each
ISB has a distinct M_OK/I_OK/C_OK/XNU_SCTLR_OK tile at x448/512/576/640,y2272.
E2 now means M-only MSR completed before ISB. Low VBAR kept until existing F;
warm path retains original default write. Exact formulas, liveness proof,
bit comparison and marker interpretation: docs/MARBLE_SCTLR_STAGES.md.
Original numerical SCTLR is unknown in available records; do not invent it.

Observed PASS: full 81 reverse/replay, strict 0082 check/apply, complete real-
header MARBLE start.s preprocess/arm64 Mach-O assemble, emitted stage audit,
x14/no-call/scratch audit, all tile bounds, SWEET byte-identical preprocessing,
zero MARBLE GICR_IPRIORITYR references, cold OSLAR excluded, diff check.
Exact prior start.s recovered by removing only snapshot/stages (and reverting
scratch comment): all old mappings, TCR/TTBR/MAIR/cache operations unchanged.
Object stage MSR/ISB offsets: M4680/46d0, I4728/472c, C4784/4788,
XNU47e8/47ec; F4858 (hex section offsets, NOT linked PAs).
Safe for diagnostic Actions build; no full new link or physical staged boot.
No new CI run/ID, commit or push (explicit prohibition), device/storage action.
Next: separately build, inspect final linked addresses, obtain physical strip
and E/E2/M_OK/I_OK/C_OK/XNU_SCTLR_OK/F/red observations. Local artifacts:
/tmp/sctlr-{before.patch,before-start.s,verify.py,audit.py,disassembly.txt},
/tmp/mmu-start.{s,macros,o}, /tmp/marble-mmu-tree.

Earlier handoffs below are historical.

## Active handoff: MARBLE cache-coherency experiment (2026-10-22)

User physically reports ALL pre-MMU checks green, E/E2 visible, F/sync-red
absent. New single MARBLE cold-only IVAC loop in 0082 start.s before E:
[x23 actual adjusted Mach-O header PA, boot_args->topOfKernelData), start
rounded down to CTR_EL0 DminLine; DSB SY/IC IALLU/DSB SY/ISB; cyan completion
tile x384,y2272. No existing transition values/layout/checks/tiles changed.
Exact source/range proof/register audit/shim comparison and results:
docs/MARBLE_CACHE_EXPERIMENT.md. Hypothesis remains unproven; no new boot.

Observed: full 0001..0081 reverse/replay, strict 0082 check/apply, complete
MARBLE preprocessing/arm64 Mach-O assembly with real headers pass. SWEET
start.s byte-identical; unrelated patch sections identical; original source
recovered exactly by removing new block. RAM range/rounding audit passes;
zero MARBLE GICR_IPRIORITYR references; cold OSLAR still skipped; diff check
passes. Local clang, no full new link. Safe for diagnostic Actions build.
No new CI run/ID, device operation, commit or push (explicitly prohibited).
Next: review then separately build and obtain completion/E/E2/F/red results.
Artifacts /tmp/cache-{before.patch,before-start.s,verify.py,audit.py},
/tmp/mmu-start.{s,macros,o}, /tmp/marble-mmu-tree. Earlier handoffs historical.

## Active handoff: MARBLE SCTLR transition diagnostic (2026-10-22)

User physical observation supersedes prior handoff: initial cyan/green/white and
A/B/C/D/E visible; F absent. Failure boundary is SCTLR/translation activation,
not table-construction return. No new physical boot performed here.

0082 changes only start.s behavior: existing markers through E unchanged;
MARBLE cold pre-MMU TCR/TG/IPS/hardware PARange/full TCR, TTBR0/1 and MAIR
readback tiles; independent exact descriptor chains for V=P post-ISB code,
KVA alias, framebuffer first PTE, low vectors. Pink E2 between SCTLR MSR and
ISB. No translation values repaired. Low synchronous vectors draw red/spin;
cold low VBAR retained across transition, normal KVA VBAR restored after F.
All new checks/markers use x9-x13/NZCV only, except dead x0 for pre-SCTLR VBAR;
no stack, x20-x26/lr/SP changes. Warm path skips bootstrap checks.

Actual preprocessing: TCR=0x226511a511, TG0=2/TG1=1/IPS=2/T0SZ=T1SZ=17;
SCTLR=0x3454593d unchanged, no PAC/Apple monitor/KTRR/CTRR selection. Immediate
post-ISB PC uses TTBR0 V=P, not KVA. Both aliases independently checked.
Complete exact source excerpt, tile coordinates, manual page walks, register
safety and architectural limitations: docs/MARBLE_MMU_DIAGNOSTIC.md.

Observed validation: downloaded existing successful run 39613073847 buildtree
and log read-only; no new CI run. Full reverse/replay 0001..0081, final strict
0082 check/application, full start.s MARBLE preprocessing/arm64 Mach-O assembly
with real generated headers, actual constant evaluation and object disassembly
pass. SWEET complete start.s preprocessing byte-identical. Other 0082 sections
byte-identical. MARBLE pe_fiq.c preprocess passes with zero priority-window
references; OSLAR exclusion and tile bounds pass. git diff --check passes.
Local clang differs from Apple CI clang; full new kernel link not performed.
Safe for a diagnostic Actions build; final linked label/table absolute PAs must
be resolved from that build, not guessed from historical kernel symbols.

Artifacts /tmp/marble-mmu-tree, /tmp/mmu-start.{s,macros,o},
/tmp/mmu-disassembly.txt, /tmp/mmu-verify.py, /tmp/mmu-extra.py,
/tmp/mmu-cc-command.json, /tmp/marble-mmu-build.log. No commit/push (explicit
user prohibition overrides default), no new CI dispatch, device/storage action.
Next: review diagnostic report, separately submit build and obtain physical
check colors/E2/F/exception tile. Absence of E2/red is not conclusive because
pre-ISB translation effects and vector/framebuffer faults can obscure evidence.

Earlier handoffs below are historical.

## Active handoff: MARBLE A-H pre-C diagnostics (2026-10-22)

User physically observed CYAN, GREEN and WHITE on real marble. This supersedes
previous no-white result: shim entry, start_first_cpu/DAIF and Stage0 execute;
skipping cold-entry OSLAR_EL1 passed the earlier blocker. Keep MARBLE OSLAR
excluded. No new physical boot was performed in this session.

0082 now adds MARBLE-only inline A-H tiles across x64..575,y2368..2399.
Macro clobbers x9-x13/NZCV only, no stack/calls, preserves x0/LR and x20-x26.
All locations audited for liveness. Existing three markers unchanged. Exact
source excerpts, stage/color table and validation limitations are recorded in
[docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md](docs/MARBLE_BOOTSTRAP_BREADCRUMBS.md).

Observed local validation: full 81-patch replay passed; strict 0082 check/apply
passed; git diff --check passed. SWEET include-stripped preprocessing identical.
Eight real macro expansions compile arm64 Mach-O using actual MOV64; framebuffer
pixel bounds pass. MARBLE cold OSLAR excluded. GIC preprocess/stub compile passes,
zero MARBLE priority-window references, SWEET identical. Full start.s assembly
and full kernel link unavailable (generated headers/build environment absent).
No other XNU source behavior changed; boot/loader/storage/GIC untouched.

Validation artifacts: /tmp/marble-bootstrap-validation (81 replay + source),
/tmp/bootstrap-task-start.s (exact task-start source), /tmp/bootstrap-markers.o,
/tmp/validate-bootstrap-markers.py, /tmp/check-wrapper-gic.py. Ready for next
Actions DEVELOPMENT/MARBLE build with full assembly/link still to verify.
No CI run/ID, commit, push, device operation or storage write. User explicitly
prohibited commit/push, overriding repository default. Next: build separately,
then temporary physical boot to read A-H and existing arm_init stage1.

Earlier handoffs below are historical.

## Active handoff: MARBLE first-entry breadcrumbs (2026-10-22)

User-reported physical result: boot-v4 shim locates MRBLXNU1, copies all ten
segments, creates boot_args and jumps to XNU VA 0xfffffe0007473488 / PA
0x841473488. Red framebuffer lasts ~20 seconds, then black and reset ~10
seconds later; existing white Stage-0 marker never appears. Symbols identify
entry as __start/_LowResetVectorEnd, start_first_cpu VA 0xfffffe000747505c.
These are user observations; no new device test was performed here.

Changed only 0082's start.s source behavior: MARBLE __start draws cyan
64x32 at x=0,y=2304 before branch; start_first_cpu skips OSLAR_EL1 only
for MARBLE, then draws green 64x32 at y=2336 immediately after DAIFSet.
Both use x9-x13 only, preserve x0, physical framebuffer 0xb8000000,
stride4320, no stack/MMU and finish with dsb sy. Existing white y2368
marker is preserved. Reset-vector path and all other source files unchanged.
Identical -/+ context lines in the patch keep outer git diff --check clean.

Validation observations: /tmp/edit-breadcrumb.py reversed the 81 patches
from the saved 0081 baseline and replayed 0001..0081 in an isolated tree.
Historical whitespace in 0006 was preserved with --whitespace=nowarn.
Final 0082 git apply --check --whitespace=error and actual application pass;
git diff --check passes. Result: /tmp/marble-breadcrumb-validation.
/tmp/validate-breadcrumb.py preprocesses complete include-stripped start.s
with real board macros: SWEET output byte-identical to exact task-start
0082 source; MARBLE removes only the cold-entry OSLAR. Actual __start and
start_first_cpu through WHITE assemble to plain arm64 Mach-O using real
XNU MOV64 macro and DAIFSC_ALL=15 (/tmp/breadcrumb-entry.o). Full start.s
compilation with generated assym.s/exported headers was unavailable.
Independent exact task-start tree /tmp/marble-breadcrumb-original confirms
only osfmk/arm64/start.s differs. /tmp/check-wrapper-gic.py passes MARBLE
and SWEET GIC preprocess/compile with API declaration stubs: MARBLE has
zero priority-window references; SWEET GIC identical. Timer27, SGI1,
GICR stride0x40000, plain arm64/16K/MAX_CPUS=1 remain unchanged.

Ready for MARBLE GitHub Actions build as a diagnostic source patch; full
kernel build/link and new physical marker results remain unverified.
No CI run/ID, device operation, commit or push. User explicitly prohibited
commit/push, overriding repository default. Next: separately run the build,
then temporary boot and report cyan/green/white. No storage changes.
Earlier handoffs below are historical.

## Active handoff: MARBLE sampler link fix (2026-10-22)

User reports DEVELOPMENT/MARBLE run 39603903020 reached final kernel link,
with only undefined _sweet_sample_task from _sweet_sample_proc. This run
was not independently fetched or rerun. Updated only 0082 source hunks:
bsd/dev/sweet_sample.c now includes pexpert/arm64/board_config.h and wraps
all existing includes/implementation in ARM64_BOARD_CONFIG_SWEET. No
exception.c change, MARBLE sampler enablement, or GIC changes.

Local observations: copied /tmp/marble-baseline to
/tmp/marble-sampler-validation, reversed all 81 patches then reapplied
0001–0081 successfully. Final 0082 git apply --check --whitespace=error
and actual application pass. /tmp/check-marble-sampler.py uses real board
headers and empty unavailable API-header stubs: MARBLE preprocesses empty,
compiles to arm64 Mach-O /tmp/marble-sampler-empty.o, and llvm-nm shows no
sampler symbols/undefined references. SWEET preprocessing is byte-identical
to 0081 under the same API stubs; full SWEET compilation was not performed.
Other late standard additions sweet_keys.c, sweet_touch.c, sweet_rpmh.c,
sweet_spmi.c and sweet_usb.c already guard their complete implementations;
all preprocess empty for MARBLE. No additional unguarded SWEET-only
implementation references found in those files. GIC constants verified:
timer27, SGI1, GICR_PE_SIZE0x40000, no preprocessed MARBLE GICR_IPRIORITYR
references. Existing GIC patch hunks are untouched. git diff --check passes.

No new CI run, full kernel link, device operation, fastboot, commit or push.
Explicit user no-commit instruction overrides repository default. Next:
review this narrow patch; full CI link remains unverified after the fix.
Earlier handoffs below are historical.

## Active handoff: MARBLE boot-v4 payload locator review (2026-10-21)

Fixed the critical generic-ramdisk location assumption without redesigning 0082.
`--xnu-payload` validates raw SWEETXNU magic and appends exactly 16 bytes:
`MRBLXNU1` (8 bytes), then raw payload length as LE64. `--ramdisk` remains
available and is mutually exclusive. Raw and wrapped sizes/hashes are reported;
post-write reparse and independent extraction verification remain enabled.
No vendor_boot modifications; tools/mkpayload.py is unchanged.

SHIM_MARBLE_XNU uses the shared C helper shim/payload_range.h. It reads only
fixed tail locations, strips optional bootconfig only when final 12 bytes are
exactly #BOOTCONFIG\n, checks span >=20 and LE32 size <= span-20, then uses
end-20-size (size includes padding). Footer at ramdisk_end-16 determines the
payload start by checked subtraction. No vendor-byte scanning. Header and
segment table are copied to aligned local storage because vendor concatenation
need not align the payload. SWEET still locates its raw payload at initrd-start.

Before any destination write, both loaders check version1, nsegs1..64, table,
ADT and segment source ranges, virtual segment overflow, translated RAM bounds,
file_size<=vmsize, kernel_end, entry, ADT and rounded boot_args/top placement,
and initrd/kernel-memory overlap. MARBLE requires exactly 0x840000000+0x100000000.
Copies/zeroing handle partial words exactly, without reading/writing past bounds.
0082 changes this review are only three redundant guards and the Qualcomm
ARMv8.2 comment. Reviewed one-CPU/MMU/ADT/GIC and staged providers preserved.

Local validation (observations, not physical XNU results):
- BOARD=marble passes, Image188416, SHA256
  0e105d57f0781223b7c326b6aab702d9029d00788d27bb7784a543d2604aa1a6:
  byte-identical to the recorded successful physical stage-0 build.
- SHIM_RAW_ONLY=1 BOARD=sweet passes, Image184320, SHA256
  f1edc94005b895adcb148d49021898cfe4ae34fa7e57c4d178845425f67f5b48.
  Size/hash changed with shared loader bounds hardening; raw discovery preserved.
- BOARD=marble-xnu passes, Image81920, SHA256
  586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05.
- All six tools unittest cases pass. All three shim Python scripts pass
  (actual loader bounds, NOP/query, DEVACT); C locator and UFS decoder pass
  ASan/UBSan. Locator covers concatenated vendor layouts with/without bootconfig,
  malformed magic/size, zero/oversized size, truncation, underflow and decoys;
  actual loader harness also accepts deliberately unaligned concatenation.
- mkadt.py /tmp/marble.adt --marble --dump passes (3760 bytes). Missing local
  D22AP /product warning remains; exact MARBLE values covered by roundtrip test.
- 0082 git apply --check --whitespace=error passes against /tmp/marble-baseline
  (final 0081). Fresh isolated application and pe_fiq.c cross-compile/preprocess
  pass both boards with API declaration stubs. MARBLE has zero priority-window
  accesses/no header definition; SWEET preprocessed GIC equals saved baseline.
- git diff --check passes. CLI mutual exclusion, ordinary ramdisk/control and
  wrapped generic-ramdisk pack/reparse/extraction all pass.

Final format-only image: /tmp/marble-wrapper-final-FORMAT-ONLY.img, 16691200
bytes, no signature/trailer, new shim with old SWEET format-test payload.
This is NOT a bootable MARBLE-kernel proof and must not be physically tested.
Independent hashes:
raw payload16604624: 5620aab559016fb6b3b1411c589c3f54aa93440ad57bedd474ae747c049116ff
wrapped16604640: 7eb72419d58c7b2a88153db2596b4bb2e1b92443a1d690a7ca5584483beccc23
extracted16604640: 7eb72419d58c7b2a88153db2596b4bb2e1b92443a1d690a7ca5584483beccc23

No CI run/ID, device operation, staging, commit or push. Explicit no-commit
request overrides the repository default. Full XNU compile/link and physical
XNU execution remain unverified. Next action requires separate user direction;
do not run CI automatically. Earlier active handoffs below are historical.

## Active handoff: First one-core XNU execution on MARBLE (2026-10-21)

The latest user report physically confirms the complete stage-0 milestone:
boot-v4/temporary boot and ABL DTB handoff, retained framebuffer, PSCI/SMCCC
1.1, working PSCI reset, Group-1 GICv3/ICC interface, virtual timer INTID27
(30 IRQs, zero unexpected), SGI1 (10/10), 16K MMU, both high-memory endpoints
0x840000000..0x940000000 and the intentional unmapped hole. Boot MPIDR
0x81000000 has zero affinity fields. GICR priority access at 0x17190400
physically aborts and MUST remain excluded. Map visible framebuffer bytes
0xb8000000 + 0x009e3400, not the 0x02b00000 splash reservation.

New physical UFS result supersedes the older unconfirmed entries below:
NOP and READ_FLAG fDeviceInit=0 succeed. LUN0 TUR initially gives 02/04/02;
normal LUN00 generic START `1b 01 00 00 01 00` fails 05/24/00 and must not
be retried. Device WLUN D0 ACTIVE `1b 00 00 00 10 00` succeeds (OCS/status0),
then LUN0 becomes ready. Capacity/read succeed with 4096-byte logical blocks;
protective MBR AA55/type EE, GPT header/entries and userdata are discovered.
No filesystem or storage-sector writes occurred.

Prepared uncommitted patch 0082 and host tooling for the next milestone;
full design, conditional-sharing inventory, commands, checks and limitations:
[docs/MARBLE_XNU.md](docs/MARBLE_XNU.md). Separate MACHINE_CONFIG=MARBLE is
plain arm64/v8.2+crypto, 16K, one CPU/cluster; minimal Marble platform/CPU
from the old single-CPU driver; Group-1 timer27/SGI1, GICR stride0x40000,
no priority window accesses. Only link/early-console/IRQ providers shared;
no MARBLE UFS/HFS/touch/display/GPU/SMP. HFS staging is needed only so old
patches apply, not selected in MARBLE MASTER. Workflow unchanged.

BOARD=marble remains byte-identical: Image188416, SHA256
0e105d57f0781223b7c326b6aab702d9029d00788d27bb7784a543d2604aa1a6.
SWEET raw build passes (Image180224). New BOARD=marble-xnu passes
(Image77824, SHA256201a41661691fc55af7d923f03d28a22ef76e33ffc72533f863dfd2b03802113),
contains fdt/loader and no UFS; optional payload copied for explicit v4 pack.
Early MARBLE framebuffer mappings use 633 16K pages (0x9e4000 including
0xc00 unavoidable final-page rounding). Bootstrap preserves shared L1[0]
RAM L2, adding only a framebuffer L3; final alias uses a separate L3.

Validation: five Python tests pass; ADT roundtrip verifies all requested
values. 81 historical patches applied with pinned HFS present, and 0082
applies cleanly to that baseline. Exact new assembly fragment assembles;
actual pe_fiq.c cross-compiles for both boards with API-declaration stubs.
Preprocessed MARBLE has no priority accesses, SWEET GIC output is identical.
These are isolated checks, NOT a complete XNU compile/link.
`git diff --check` and 0082 `git apply --check --whitespace=error` pass.
Existing SWEET kernel only used for host payload format validation;
/tmp/marble-xnu-FORMAT-ONLY.img (16687104 bytes) uses stock v4 metadata,
new shim and SWEET payload, hash/reparse verified; NOT bootable MARBLE proof
and must not be used for physical XNU testing. Local D22AP /product artifact
is absent; root iPhone X identity remains. No MARBLE kernel exists yet.

No CI run/ID, commit, push, fastboot or phone access. Explicit task prohibits
automatic commit despite AGENTS default. Pre-existing untracked file named
`him: complete marble stage-0 hardware bring-up"` preserved. Next: human
reviews source diff, separately authorizes commit/push, then dispatches
existing xnu.yml DEVELOPMENT/MARBLE on branch marble. Full kernel link and
all physical XNU execution remain unverified. Do not write userdata.

All prior active/next-test statements below are historical and superseded.

## Active handoff: MARBLE stage 0 (2026-10-21)


### Device-WLUN ACTIVE diagnostic (2026-10-21, current)

Physically confirmed by the user: NOP succeeds with OCS=0; READ_FLAG
fDeviceInit succeeds and returns zero, so initialization is already complete.
LUN0 TUR returns OCS=0, CHECK CONDITION, sense 02/04/02 (NOT READY,
initializing command required). Generic disk START on LUN 0, CDB
`1b 01 00 00 01 00`, returned rc=4, OCS=0, CHECK CONDITION and
05/24/00: ILLEGAL REQUEST / INVALID FIELD IN CDB. That generic form is
invalid for this UFS LU/state and is removed from the executable path.

Inspected current Linux sources:
- https://raw.githubusercontent.com/torvalds/linux/master/drivers/ufs/core/ufshcd.c
  (`ufshcd_execute_start_stop`, `ufshcd_set_dev_pwr_mode`)
- https://raw.githubusercontent.com/torvalds/linux/master/include/ufs/ufs.h
  (`UFS_UPIU_UFS_DEVICE_WLUN=0xD0`, `UFS_ACTIVE_PWR_MODE=1`).
Linux sends the separate whole-device power-mode operation to
`hba->ufs_device_wlun`, using POWER CONDITION = pwr_mode << 4.
The sole next physical experiment is ACTIVE on UPIU LUN **0xD0**,
CDB **`1b 00 00 00 10 00`**. It has NOT been physically tested.

The existing `scsi(lun, ...)` / `scsi_timed(lun, ...)` helpers already put
lun in UPIU byte 2. Only DEVACT uses D0; TUR, READ CAPACITY(10) and READ(10)
remain on 00. COMMAND=01, flags=0, SCSI command set=0, incrementing SCSI
tag, expected length=0, zero remaining CDB bytes and no PRDT for DEVACT.
All existing owned/running/idle UTRL guards and invalid initial OCS remain.

Sequence: NOP success -> successful READ_FLAG observing flag=0 -> LUN0 TUR.
Only valid complete sense exactly 02/04/02 with OCS=0 and CHECK CONDITION
allows one DEVACT. Initial TUR success skips it; unrelated errors stop.
Before submission display DEVACT lun=D0 and CDB 1B0000001000; after completion
display rc and ocs/st. Any DEVACT failure dumps existing response/sense and
stops, with no variants, retry, or LUN0 START. Success prints DEVACT ready,
which does not assert LUN0 readiness.

After DEVACT success, LUN0 TUR polls immediately and at 100 ms offsets,
at most 50 attempts under one 5000 ms deadline including transfers.
First, final, success and changed/error results print TUR+ labels and sense.
Unchanged 02/04/02 through the deadline prints LUN0 still not ready and stops.
Any other failure prints sense and stops. Only TUR success prints LUN0 READY
and permits the existing read-only capacity/read/GPT path. No storage-writing
CDB, flag/query write, reset, host/link/PHY setup, clock/regulator or UniPro
attribute change was added. Protected bring-up and boot-v4 code unchanged.

Validation: `BOARD=marble shim/build.sh` and
`SHIM_RAW_ONLY=1 BOARD=sweet shim/build.sh` pass without warnings.
Actual readiness-flow host test passes exact DEVACT CDB/LUN, ordinary TUR
LUN, gate, single issue, CHECK CONDITION stop, changed sense, success and
five-second timeout. Source call-site/opcode checks cover LUN0 capacity/read,
sole D0 call and only SCSI opcodes 00/1b/25/28. Existing ASan/UBSan NOP/query
and response-decoder tests pass; boot-v4 tests pass (2/2).
Raw Image: 188416 bytes; SHA256
`0e105d57f0781223b7c326b6aab702d9029d00788d27bb7784a543d2604aa1a6`.
Repacked and inspected `shim/out/marble/shim-marble-stage0.img`: 3739648 bytes,
v4/1584, kernel at 4096, ramdisk at 192512 (3544657 bytes), no signature or
trailing bytes. Packed kernel SHA256 equals raw Image; independent extraction
also confirms byte equality. Generic ramdisk SHA256 remains
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
`git diff --check` passes. No CI run/ID, boot/device access, staging, commit
or push; explicit user instruction overrides automatic-commit guidance.
Pre-existing changes including shim/shim.c preserved. Next: user separately
boots this image and reports DEVACT response/sense and subsequent LUN0 TUR.
DEVACT success, LUN0 readiness and data/GPT reads remain unconfirmed.
Historical sections below are superseded.

### READ_FLAG-only diagnostic (2026-10-21, historical)

Physically confirmed by the user: NOP OUT succeeds first try (try=0), rc=0,
OCS=0, NOP IN transaction=0x20, returned tag=1 matches, UFS NOP ready.
SET_FLAG fDeviceInit after this successful NOP still returned rc=4, OCS=0,
QUERY RESPONSE=0x36, function=0x81, result=0xFF GENERAL FAILURE,
echoed opcode/IDN=0x06/0x01. The prior theory that missing NOP causes
SET_FLAG failure is disproven.

Hypothesis only: because this shim inherits an already-running ABL UFS
link/controller, fDeviceInit may already have completed before shim entry.
The next physical test reads the flag without changing it; no READ_FLAG
value has yet been observed on hardware.

Current build removes SET_FLAG entirely. After NOP it sends only READ_FLAG
fDeviceInit: 32 wire bytes as BE groups (TT is incrementing tag, initially 01):
`160000TT 00010000 00000000 05010000 00000000 00000000 00000000 00000000`.
Every query dumps these bytes and all eight slot-0 UTRD dwords before the
doorbell. UTRD: DW0=11000000, DW1=0, DW2=0000000f, DW3=0,
UCD low/high=runtime address of ucd (Image offset 16000; at the previously
observed a8000000 load base, a8016000/0), response=00800080
(offset 128 dwords, length 128 dwords), PRDT=0/0.
Response requires OCS=0, transaction=0x36, result=0 and existing tag/OSF
checks. Value is BE32 at bytes 20..23, masked with 1. Prints FDEV rc/OCS,
Q transaction/result/value, and flag. Errors dump all 32 response bytes and
stop. Initially clear prints FDEV already clear and permits unchanged
TUR/READ CAPACITY(10)/READ(10), including embedded sense decoder. Initially
set prints FDEV already set and polls READ_FLAG at 1 ms intervals, bounded
by a shared 1500 ms deadline including transfers and diagnostics; clear
prints FDEV ready, expiry prints FDEV timeout and stops before SCSI.
No START STOP UNIT or other management/storage write is sent. If sense
02/04/02 persists, record it as a new physical result; it is not yet tested.

Validation: requested MARBLE and SWEET raw builds pass without warnings;
actual-code ASan/UBSan NOP/query harness and sense decoder pass; boot-v4
unit tests pass (2/2). Source review confirms SCSI and everything following
it identical to the task-start snapshot; only CDBs 00/25/28. No changes to
packaging code, framebuffer, PSCI, GIC, timer, SGI, MMU, XNU or link/PHY setup.
Raw Image 184320 bytes, SHA256
`c42a886386b83aaac6ac65745861d4d6f07d4d396332f13a70aab6e1a6fa7c48`.
Repacked and inspected `shim/out/marble/shim-marble-stage0.img` (3735552 bytes):
v4/1584, kernel at 4096, ramdisk at 188416 (3544657 bytes), no signature or
trailer. Independent extraction equals raw Image; generic ramdisk SHA256
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
No CI run/ID, device commands, fastboot, staging, commit or push. Existing
uncommitted changes preserved. Next: user separately boots and reports FDEV
and subsequent read-only SCSI results. This diagnostic image is unbooted.
Historical sections below describe superseded builds.

### NOP verification build (2026-10-21, historical)

New user-reported physical result from the preceding fDeviceInit image:
SET_FLAG returned rc=4, OCS=0, QUERY RESPONSE transaction 0x36, echoed
query function 0x81, query result 0xFF GENERAL FAILURE (not unknown),
byte 7/value zero, returned opcode/IDN 0x06/0x01. Raw response words:
`36000001 0081FF00 00000000 06010000 00000000 00000000 00000000 00000000`.
Observation: query transport completes and reaches the device, but SET_FLAG
was rejected. Whether the missing NOP caused rejection remains unproven.
Previously confirmed physical boot-v4, framebuffer, PSCI/SMCCC/reset,
GIC/timer/SGI, MMU and UFS takeover/SCSI sense results below remain valid.

Inspected Linux drivers/ufs/core/ufshcd.c:
https://raw.githubusercontent.com/torvalds/linux/master/drivers/ufs/core/ufshcd.c
Normal ordering is link startup -> ufshcd_verify_dev_init (NOP OUT/NOP IN)
-> ufshcd_complete_dev_init (fDeviceInit SET_FLAG/READ_FLAG) -> device access.
Linux defines NOP_OUT_RETRIES=10 and NOP_OUT_TIMEOUT=50 ms. This shim keeps
ABL's retained link/controller state and adds only the missing verification;
no link startup, HCE toggle, reset, PHY, clock, regulator or power-mode change.

New MARBLE-only handshake: zeroed 32-byte NOP OUT, byte 0=0x00, byte 1=0,
byte 2=0, byte 3=incrementing 8-bit task tag, bytes 4..31=0. The entire
512-byte request area is zero except the tag. Shared query UCD request and
response areas; storage CT=1, DD=0, interrupt bit=1, initial OCS=0x0f,
zero PRDT. Shared no-data submission helper rechecks own UTRLBA/UTRLBAU,
UTRLRSR running and idle doorbell before submission. Buffer reuse is also
guarded before clearing. Success requires completion within timeout, OCS=0,
transaction byte exactly 0x20, and returned tag equal to sent tag. SCSI status
is ignored. Returned transaction/tag are printed; failures also print OCS,
sent/returned tags and all 12 response-header bytes.

At most 10 attempts, each bounded to 50 ms by CNTVCT/CNTFRQ. Timeout uses
existing UTRLCLR cancellation; retries require an idle owned running list.
A still-active slot or ownership/run failure stops safely without buffer reuse.
Only successful NOP IN prints `UFS NOP ready` and enters the existing 1500 ms
SET_FLAG/READ_FLAG sequence. Exhaustion/failure returns before any query/SCSI.
Query request/response checks and SCSI/sense implementation are preserved;
query diagnostics now name success and every defined result 0xF6..0xFF.
The sole reachable query write remains SET_FLAG(0x06), fDeviceInit(0x01).
Only SCSI CDBs 0x00/0x25/0x28 remain; no filesystem/storage writes added.

Validation: MARBLE and SWEET raw builds pass without warnings. New reproducible
`python3 shim/tests/ufs_dev_init_test.py` extracts actual code and passes
ASan/UBSan host MMIO/timer tests: exact NOP/query bytes, descriptor/PRDT,
OCS, wrong transaction/tag, tag wrap, retry success/exhaustion, 50 ms timeout,
cancellation/stuck slot, both base halves/run/idle guards, SET gate, flag
polling/deadline, query failure, all disallowed query opcodes and result names.
Existing response decoder ASan/UBSan tests pass; boot-v4 tests pass (2/2).
Leak detection disabled for host sanitizer runs. `git diff --check` passes.
SCSI and everything after it compare byte-for-byte to task-start source.

Raw Image: 184320 bytes, SHA256
`0a0273178f9eff8a3086a824daad4328e9b0bfbaef1e0862f3cd0b6c64333fce`.
Repacked/inspected `shim/out/marble/shim-marble-stage0.img`: 3735552 bytes,
v4/1584, kernel at 4096, ramdisk at 188416 (3544657 bytes), no signature or
trailing bytes. Independent extraction confirms packed kernel equals raw Image;
ramdisk SHA256 remains
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
No CI run/ID, device commands, fastboot, staging, commit or push. Existing
shim/shim.c edits preserved. New NOP image has NOT been physically booted.
Next: user separately boots this image and reports NOP, INIT and SCSI results;
NOP success, fDeviceInit success and data/GPT reads remain physically unconfirmed.
Earlier next-test statements below are historical and superseded.

### fDeviceInit implementation and validation (2026-10-21, historical)

Latest user-reported physical results: boot-v4 accepted; framebuffer and DTB
handoff work; PSCI 1.1 and SMCCC 1.1 work. PSCI_SYSTEM_RESET physically
rebooted the phone after the final 40-second delay. GIC works, virtual timer
INTID 27 delivered 30 IRQs with zero unexpected, and SGI1 delivered 10 IRQs
with zero unexpected. 16K MMU works, the future-XNU high window translates,
and the intentional hole remains unmapped. UFS retained-host takeover and
UTRL base readback work; SCSI transport completes with OCS=0. TUR,
READ CAPACITY(10), and READ(10) all returned RESPONSE UPIU transaction 0x21,
response 0x01, sense length 0x12, key 0x02 / ASC 0x04 / ASCQ 0x02:
NOT READY, logical unit not ready, initializing command required.
These are physical observations supplied by the user, not inferred successes.

The next physical test now uses the implemented MARBLE-only UFS fDeviceInit
sequence, modeled narrowly on Linux ufshcd_complete_dev_init(). The sole new
device-management write is QUERY SET_FLAG (0x06), IDN fDeviceInit (0x01),
standard write function 0x81. READ_FLAG (0x05), same IDN, function 0x01 polls
until the big-endian response value masked with bit 0 clears. Explicit byte
structures assert a 12-byte header + 20-byte OSF = 32 bytes, value at 20..23.
Requests use transaction 0x16, zero LUN/flags/index/selector/data length and
incrementing query tags; responses require transaction 0x36, matching tag,
echoed opcode/IDN, zero query result (header byte 6), reserved byte 7 and
no extra headers/data. Byte 6 is the query response/result, not SCSI status.

Slot 0 retains storage command type, no data direction/PRDT, invalid initial
OCS and the existing UCD response area. Existing takeover checks remain;
queries additionally recheck list base/run state and idle doorbell before
submission. CNTVCT/CNTFRQ bounds SET plus all reads to 1500 ms total, including
in-flight waits; roughly 1000 us separates reads. A timeout cancels slot 0
using the existing UTRLCLR convention and returns without SCSI. The screen
shows SET diagnostics, first read, changes, ready or timeout/error; query
errors include all 32 response bytes. SCSI starts only after flag zero;
the original TUR/capacity/read/GPT path and sense decoder are preserved.
No SCSI write, START STOP UNIT, descriptor/attribute write, other flag change,
configuration change, PHY/link reinitialization or partition/data write was
added. SWEET behavior and all working bring-up/XNU/packaging code are unchanged.

Validation: both requested raw builds passed without warnings; diff whitespace
check passed. Temporary host harness /tmp/marble-query-test.c extracts the actual
query implementation with mocked MMIO/timer and passes ASan/UBSan (leak checks
disabled): exact request bytes, no PRDT, flag 1->0, stuck flag, query error,
wrong transaction, transfer timeout, list-base guard and rejected opcode.
Harness tag assertion was corrected to allow the standard 8-bit tag wrap.
Existing SCSI path/helpers compare byte-for-byte to the task-start snapshot
except the MARBLE init gate: only CDB opcodes 0x00/0x25/0x28 remain.

Raw Image: 184320 bytes; SHA256
`a1f7b2e72954047c1725c453d6c975500a9e63346be402fccbed36aa6bedb4ff`.
Repacked `shim/out/marble/shim-marble-stage0.img`: 3735552 bytes,
v4/1584, kernel offset 4096, ramdisk offset 188416, ramdisk 3544657 bytes,
zero signature/trailing bytes. Inspect and independent byte extraction pass;
packed kernel equals raw Image byte-for-byte. Stock generic ramdisk SHA256:
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
No CI run/ID, adb, fastboot, device boot, commit, staging or push in this task.
The new fDeviceInit image has NOT been physically booted. Next: user reviews
and separately boots it, records INIT query diagnostics and subsequent sense,
capacity and GPT results. Data reads/GPT remain physically unconfirmed.
Earlier diagnostic-build expectations below are historical and superseded.

### Response-diagnostic build validation (2026-10-21)

Both `BOARD=marble shim/build.sh` and
`SHIM_RAW_ONLY=1 BOARD=sweet shim/build.sh` passed without warnings after
removing compiler-generated libc structure-copy/zero dependencies. MARBLE raw
Image is now 184320 bytes, SHA256
`ea9c6d81ede93084f6c2e8dc88a52f12f6fcbe6514330da6ce5a9228ddea94ea`.
Host parser assertions passed with AddressSanitizer/UBSan: both fixed and both
descriptor codes, key masking, short/zero/unknown sense, 18-byte copy clamp,
maximum fitting length, overflow and wrong transaction. LeakSanitizer cannot
run under this environment's ptrace; rerun passed with leak detection disabled
(the parser allocates nothing). Existing boot-v4 unittest suite: 2/2 passed.
`git diff --check` passed. Reviewed UFS diff: only existing CDB opcodes 0x00,
0x25 and 0x28; request construction, safety gates and takeover unchanged.
No new storage-modifying operation or REQUEST SENSE was introduced.

Replaced the previous generated image and repacked with the verified tool:
`shim/out/marble/shim-marble-stage0.img`, 3735552 bytes. Inspect passed:
v4/1584, kernel 184320 bytes at 4096, ramdisk 3544657 bytes at 188416,
zero signature/trailing bytes. Independent extraction equals the new raw Image
byte-for-byte and its SHA256 above. Ramdisk SHA256 remains
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
No CI runs/IDs, device commands, commits or pushes in this iteration.
Pre-existing edits in shim/shim.c were preserved without modification.
Next: user reviews and physically boots this diagnostic image separately;
record first/last TUR and capacity UPIU metadata and sense before deciding
any recovery. The new diagnostic image has not been physically booted.

## Confirmed physical stage-0 results (2026-10-21, latest)

User-reported second physical boot supersedes the earlier unverified timer/MMU
and priority-abort limitations below. Boot-v4 was accepted by ABL; stage-0
entered correctly and retained framebuffer output works. DTB pointer was
`0xb6ea4000`, MPIDR `0x81000000`, CNTFRQ `0x124f800` (19.2 MHz).
PSCI 1.1 and SMCCC 1.1 work; SYSTEM_RESET feature result is zero.
GIC distributor access works (`0xd0` -> `0xd3`); redistributor access works
at `0x17180000`, WAKER zero, except the protected priority window which is
intentionally skipped. Enabled mask `0x08000002`: virtual timer INTID 27
received 30 interrupts and SGI1 exactly 10, each with zero unexpected IRQs.
16K MMU enabling returned zero. Shim range `0xa8000000..0xa802c000`,
framebuffer, GIC and both future XNU high-window endpoints translated;
the intentional hole faulted as expected. These working areas are unchanged.

UFS host is present/enabled/ready: version `0x300`, CAP `0x1587031f`, HCE 1,
HCS `0x10f`, IS `0x400`, UTRLRSR 1, idle doorbell, 32 slots. Inherited list
`0xff129000` (high zero); takeover/readback of our list `0xa8015000` succeeds.
All three TURs, READ CAPACITY(10) and READ(10) returned rc=4, packed ocs/st=2:
transport OCS is zero, SCSI status is CHECK CONDITION (`0x02`). This is not a
UTRL/DMA timeout. Latest physical sense is key 0x02 / ASC/ASCQ 04/02, initializing command
required; UFS data reads and partition parsing remain unconfirmed.

Current diagnostic change captures RESPONSE UPIU transaction at byte 0,
response field at 6, status at 7, BE16 sense length at 32/33 and sense at 34.
Only transaction `0x21` with the full declared sense fitting the 512-byte buffer
is accepted; copying is capped at 18 bytes. Fixed 0x70/0x71 uses key byte 2
and ASC/ASCQ 12/13; descriptor 0x72/0x73 uses key byte 1 and ASC/ASCQ 2/3,
with individual length guards. Unknown/short formats show code and raw bytes.
Each failed probe displays metadata and sense (including explicit zero length).
Three TUR attempts remain; READ CAPACITY and READ continue as before, and
partition parsing requires successful READ. No recovery command, request-format,
LUN, takeover, hardware initialization or storage-write change was made.

### Earlier milestone: physical SEA observation and priority skip (2026-10-21)

Supersedes earlier statements below that no physical MARBLE boot exists.
User reports boot-v4 accepted, framebuffer works, shim executes through PSCI,
GIC distributor setup and redistributor discovery. First GIC failure: stage
`gic config`, ESR `0x96000010` (current-EL Data Abort / SEA), FAR `0x17190400`
(GICR IPRIORITYR), MPIDR `0x81000000`. Timer IRQ test was not reached;
MARBLE timer/SGI delivery remains unverified.

MARBLE-only correction skips all GICR priority reads/writes, prints
`PRIO skip protected GICR priority window`, retains INTIDs 27/1 and PMR `0xf0`.
Granular MARBLE stages: gic group / enable / cpuif / vtimer / sgi. SWEET code
binary contents unchanged; exception handling, XNU, UFS, framebuffer/MMU untouched.
Both requested raw builds exit 0 without warnings; existing packaging tests 2/2
pass. Preprocessed MARBLE has no priority accesses. Repacked from private clean
stock boot_a.img and inspected; independent extraction matches raw Image SHA256
`d6f4da538a362e9f23c28dc6a4bc84486a0579aa766e25123353e5e7e84a1233`.
Stock ramdisk SHA256 verified:
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
Image `shim/out/marble/shim-marble-stage0.img`: 3731456 bytes, SHA256
`958cc268268f1bba13953adbce1675b8ac5a3c55e321e6e708c9b49d717c03d2`;
v4/1584, kernel 180224 at 4096, ramdisk 3544657 at 184320, no signature/trailer.
Previous image preserved privately beside it as
`shim-marble-stage0-before-prio-skip-28bf49fc7d5e.img`.
No CI run IDs, device commands, fastboot, commit or push in this task.
Next: user review; corrected image has not been booted. No timer success claim.

### Earlier stage-0 implementation history

- User requested a separate SM7475 MARBLE diagnostic shim; SWEET XNU baseline
  already built successfully. Do not change the workflow. **Do not commit or
  push until user reviews. Do not run fastboot or flash.**
- Added board selection (`BOARD=marble shim/build.sh`), raw outputs only in
  `shim/out/marble/`. MARBLE rejects payloads and excludes loader/secondary CPU
  code. PSCI/GIC/virtual timer page, existing read-only UFS probe with MMU off,
  then 16K MMU translation diagnostics; PSCI reset only, no SWEET PSHOLD.
- Board constants use authoritative user-provided values; no MARBLE hardware
  observation exists. High Device mapping covers 0x840000000..0x940000000;
  no actual RAM access to that future XNU window. SWEET defaults preserved.
- Local MARBLE and SWEET raw builds passed without warnings; zero C ABS64,
  linked MARBLE ELF no relocations, only expected start.o header ABS64.
  Image 180224 bytes, ARM64 header size checked, SHA256
  `b344ada1efa0502547a151fd171843b8150d4e58688a04e81f2cf69688cbefa1`.
  All L2/L3 entries checked in extracted host table-construction harness for
  low/high/cross-block images on both configurations. UFS command code unchanged
  except moving its identical base address into board.h; no SCSI WRITE added.
- No new CI run, device boot, commit or push. Packaging remains blocked pending
  private stock v4 boot/vendor_boot header, DTB, load-placement and DMA checks.
  No MARBLE boot.img produced; never use SWEET v2 packaging for MARBLE.
- Review corrections (2026-10-21): framebuffer mapping uses `FB_VISIBLE_SIZE`
  (`4320 * 2400 = 10,368,000`), statically bounded by FB_RESERVED. Host checks
  confirm only MARBLE 0xb8000000 is Normal-NC; 0xba000000 stays Device.
  MARBLE now() reads CNTVCT; SWEET keeps CNTPCT; UFS counter code unchanged.
  User-provided Android log reports 19.20 MHz (virt/virt), live DT PPI 11 /
  INTID 27. MARBLE reset calls only PSCI_SYSTEM_RESET and WFE forever if it
  returns: no IMEM restart-reason or PSHOLD write. SWEET reset is unchanged.
- Re-ran `BOARD=marble shim/build.sh` and
  `SHIM_RAW_ONLY=1 BOARD=sweet shim/build.sh`: both exit 0, no warnings,
  raw Images each 180224 bytes. Both boards: zero C ABS64, only the expected
  start.o header ABS64, linked ELF no relocations. Regenerated host harness
  from current mmu.c: every L2/L3 entry passes for low/high/cross-block image
  placements, out-of-range rejected, exactly one Normal-NC block per board.
  Harness is local `/tmp/marble-mmu-check.c`; these are offline observations,
  not hardware boot results. No CI run, device command, packaging, commit or push.
- Next: user reviews diff, then privately inspect packaging inputs described in
  `MARBLE_STAGE0.md`. Original images/device identifiers must stay out of git.


### Packaging milestone (2026-10-21; supersedes packaging blocker above)

- Added separate standard-library `tools/mkbootv4_marble.py` inspect/control/
  repack CLI and synthetic tests; stage-0 hardware, XNU and SWEET unchanged.
- `BOARD=marble shim/build.sh` exit 0 without warnings; raw Image 180224 bytes,
  SHA256 b344ada1efa0502547a151fd171843b8150d4e58688a04e81f2cf69688cbefa1.
- Private clean boot parsed v4/1584, OS 17.0.0/2026-10, empty cmdline,
  signature zero. Control `shim/out/marble/control-stock-v4.img` 48185344
  bytes equals the whole meaningful source region; component hashes match.
  Source partition trailing 153141248 bytes excluded, including footer area.
- `shim/out/marble/shim-marble-stage0.img` 3731456 bytes, kernel at 4096,
  ramdisk at 184320 (3544657 bytes); post-write separate decoder confirms
  kernel hash equals raw Image and ramdisk equals stock. No trailing bytes;
  format padding zero. Re-inspection passed for both outputs.
- Synthetic unittest suite: 2 tests passed (malformed/truncated rejection,
  overflow, corruption, deterministic packing, metadata/trailer checks).
- No CI run IDs, device actions, physical boot, commit or push in this task.
  All source changes left uncommitted for review as explicitly requested.
  Private stock/generated artifacts remain excluded from git. Vendor_boot,
  dtbo and all phone partitions untouched. Next: human packaging review;
  raw Image acceptance, ABL placement/DTB handoff and hardware remain untested.


## Agent handoff / active work (2026-10-15, latest)

### >>> UPDATE 2026-10-18 (read first, then the 10-17 handoff below) <<<

**STATE at end of 2026-10-18 (evening):**
- On the phone: userdata = **image v15** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v15.img/.simg`; = v14 + `/private/var/preferences/SystemConfiguration/preferences.plist` with one network service "USB Ethernet": Interface DeviceName ue0 Type Ethernet, IPv4 Manual 192.168.7.2/24 router 192.168.7.1, DNS 1.1.1.1 8.8.8.8, set "Automatic" as CurrentSet). Fallback image v14 (v12/v13 deleted).
- Kernels: **0078** = all 8 cores (`cpus=8`, cpu6/7 = A76, homogeneous SMP; mkadt now emits 8 CPU nodes; ADT `shim/out/sweet-0078hi.adt`); **0079** = display off/on via IOMFB selector 12 kern_RequestPowerChange(state) (fade over 6 vsyncs, then black; verified: power button gives "SWEET FB: display off/on"); **0080** = `SWEET NET: <proc> route add/delete/change ...` and `... add/delete address ...` trace (built, `shim/out/shim-boot-0080s.img`, NOT booted yet).
- **Internet over USB: not working yet.** Host side is ready (temporary iptables: FORWARD accept for 192.168.7.0/24 + MASQUERADE, comment "ios-sweet"; lost on host reboot). With v15 the phone sent no DNS and no outbound traffic (only mDNS/ARP) -> configd probably did not apply the service (or did, without default route/DNS). Next: boot 0080s on v15, watch `SWEET NET` lines (does configd add 192.168.7.2 / default route on ue0?). If configd ignores ue0 (not an IOKit IONetworkInterface; configd 1241.140.6 source in `research/configd-1241`, SCNetworkInterface createInterface needs IONetworkInterface -> controller (IOMACAddress, SelfNamed) -> bus), add IOKit stand-ins and/or rename the ifnet to en*.
- Live log listener (`nc -ukl 5140`) may still be running, writing `logs/live-0078s.txt`.

**LIVE LOG over USB (0077, boot 0077s): no more recovery round-trips.** Boot an image with `sweetusb=2`, run `tools/sweet-usbnet.sh logs/live-NAME.txt` on the PC: it waits for the phone's CDC-ECM interface, sets 192.168.7.1/24 (sudo) and prints/saves the kernel console the phone streams every 100 ms as UDP to 192.168.7.1:5140 (starts with the last 64 KiB). `ping 192.168.7.2` checks the link. Current image: `shim/out/shim-boot-0077s.img` (kernel 0077, ADT sweet-0069hi, cpus=6, sweetfb_noconsole=1, sweetfb_hz=30, sweetusb=2). The recovery pull (`tools/sweet-log-pull.sh`) is still the way after a panic/hang before USB comes up.

**🎉 USB networking works (boot 0076s, 18:24 local): `ping 192.168.7.2` from the PC answers in ~1 ms, 0 % loss (200-packet burst, 1500-byte frames, 512/1024-byte frames).** 0075: CDC-ECM function (bulk 0x81/0x01, interrupt 0x82 NETWORK_CONNECTION; host MAC 02:00:5e:77:ee:01) + kernel ethernet ifnet `ue0` (legacy output, header strip like if_fake) with 192.168.7.2/24 set from the kernel (proto_plumb + SIOCAIFADDR on an in-kernel socket). 0076: received frames into one cluster mbuf (mbuf_allocpacket gave a first mbuf of length 0 -> panic "Failed mbuf validity check: len -14"). Host side (Linux cdc_ether, interface `enp0s20f0u3u1`): `nmcli dev set IF managed no; sudo ip addr add 192.168.7.1/24 dev IF; sudo ip link set IF up`. Boot image `shim/out/shim-boot-0076s.img` (`sweetusb=2`). iOS itself does not see ue0 yet (configd needs an IONetworkInterface in IOKit).

**USB device mode works (boot 0074s, 17:45 local): the host enumerates the phone at high speed as `1209:0001 ios-sweet "Sweet iOS (USB bring-up)"`.** 0072 read-only probe: ABL leaves the USB30_PRIM GDSC and all 7 USB clocks on, DWC3 v3.20a (GSNPSID 0x5533320a) in device mode (GCTL 0x00112000), halted (DCTL RUN_STOP 0, DSTS 0x00d3de04), event buffer still at ABL's 0xfdfc8000, QUSB2 PHY alive. 0073 (`sweetusb=2`): DCTL soft reset, own event buffer (polled, interrupt masked), ep0 DEPSTARTCFG/SETEPCONFIG/SETTRANSFRESOURCE, setup TRB, RUN_STOP; control-transfer state machine as Linux ep0.c; descriptors: vendor class, no data endpoints. It ran but no event came: **0074** forces the VBUS session in the Qualcomm wrapper (QSCRATCH 0xa6f8800: HS_PHY_CTRL |= UTMI_OTG_VBUS_VALID(20)|SW_SESSVLD_SEL(28), SS_PHY_CTRL |= LANE0_PWR_PRESENT(24), as Linux dwc3_qcom_vbus_override_enable) -> connect + enumeration. Image `shim/out/shim-boot-0074s.img`. Black Phone app: main thread waits in -[VMVoicemailManager fetchAccounts] (sync XPC; voicemail needs the modem).

**Navigation works (boot 0071s on v14, log `logs/boot-0071s.txt`):** swipe up from the bottom edge returns to the home screen; app switcher works. Two fixes: **0070** pid_hibernate (syscall 435 was nosys on the macOS config -> SIGSYS killed SpringBoard in -[SBToAppsWorkspaceTransaction _didComplete] when an app left the foreground; the only CONFIG_EMBEDDED-only entry in syscalls.master); **0071** touches starting within 48 px of an edge carry kIOHIDDigitizerEventFromEdgeTip (UIKit `_UIEventHIDTouchEdgeTypeForHIDEvent` reads the digitizer EventMask 0xb0007 bits 0x800/0x1000/0x2000/0x40000). Diagnosed, not fixed: Settings (Preferences) SIGTRAP in PodcastsUI func_1cdc47c58: force-unwrap of `URL.volumeTotalCapacity` (nil on our HFS+ root). Phone/Photos/Messages show black (MobilePhone launches, no crash) - next: stack samples via boot-arg `sweetsample=MobilePhone,MobileSlideShow,MobileSMS,SpringBoard` (image `shim/out/shim-boot-0071s.img`).

**🎉🎉 MILESTONE 2026-10-18 ~15:30 local: iOS 16.7 SPRINGBOARD HOME SCREEN ON THE PHONE** (boot `shim/out/shim-boot-0069s.img` = kernel 0069 + ADT `shim/out/sweet-0069hi.adt`, image **v14**; log `logs/boot-0069s-v14-HOMESCREEN.txt`). Home screen with a few apps, Settings opens, Control Center / lock screen / notification center work, touch + buttons work, 6 A55 cores (`cpus=6`), `sweetfb_noconsole=1 sweetfb_hz=30`. Known issue: cannot leave Settings (home gesture / AssistiveTouch home do nothing) - to investigate.
What it took today (in order): 0058 HID services (Apple IOHIDFamily-1915 user client), 0059 iPhone X identity (hw.product etc.), 0060 SPMI keys + GENI touch, 0061 1125x2436 presented display, 0062 RPMh L11C touch power + IOPMPowerSource battery, 0063 GENI FIFO packing (Goodix GT9896), 0064 PRIV_WORK_INTERVAL grant (SpringBoard "Failed to create work interval"), 0065 SMP via PSCI (6 A55), 0066 crash map regions, 0067 console mute without cons_ops write, 0068 IOSurface lookup of an already-mapped surface returns base -1 (backboardd snapshot crash), 0069 UFS log flush 10 s. Image v13: CommCenter removed from launchd.plist, BKNoWatchdogs. **Image v14** = v13 + Setup skipped (`/var/mobile/Library/Preferences/com.apple.purplebuddy.plist` SetupDone/SetupFinishedAllSteps true, SetupVersion 11, daemonizeNeedsToRun false; purplebuddy.notbackedup mini-buddy flags false; managedconfiguration.notbackedup LockdownActivationIndicatesCloudConfigurationAvailable false; springboard MCForceShowCloudConfigurationUI false) + mobileactivationd data ark seeded (`/private/var/containers/Data/System/D90C94C4-F94E-4FCF-8A28-A93BE3846D8E/Library/internal/data_ark.plist`, -ActivationState Activated etc.) + MediaToolbox D22/D221/Default SubServerConfiguration StartRecorderServer=false (mediaserverd crash loop: portrait-filter prewarm called NULL GL). **Activation:** ADT /chosen certificate-production-status 0, effective-production-status-ap 0, certificate-security-mode 1, effective-security-mode-sep 1 -> mobileactivationd's native Hactivation branch (Codex `codex/activation/report.md`; alternative 4-byte daemon patch documented there). Fallback image v13; v12 deleted.

**🎉 TOUCH WORKS (boot 0063u on image v13, 2026-10-18 ~13:15 local):** tapping (i) on Setup's Hello opens the device-info sheet; swipe-up is recognised (spinner, then back to Hello - under investigation). Chain: RPMh L11C vote (0062, `bsd/dev/sweet_rpmh.c`) -> GT9896 @0x5d on GENI SE7 (0063 fixed FIFO packing: register address went out byte-swapped) -> sweet_hid_touch -> SweetHIDTouch -> backboardd. Battery icon OK (0062 SweetBattery IOPMPowerSource, static 100 %). **Image v13** (= v12 + CommCenter jobs removed from launchd.plist + `BKNoWatchdogs`=true and `FBLaunchWatchdogExceptions{com.apple.purplebuddy:100}` in /var/mobile/Library/Preferences/com.apple.springboard.plist): Setup no longer killed by the scene-create watchdog (it blocked in CoreTelephony getSubscriptionInfo -> CommCenter, Codex `codex/setup/report.md`; that report also lists how to skip Setup: SetupDone/SetupFinishedAllSteps/SetupVersion=11 in com.apple.purplebuddy.plist + activation check). v9 deleted, fallback = v12. Input latency ~1 min with 1 CPU -> Codex task 11 = SMP via PSCI (`codex/smp/`).

**INPUT WORKS (boot 0060u on a freshly flashed v12, log `logs/boot-0060u.txt`):** power, volume up, volume down reach iOS (PMIC -> sweet_keys.c -> SweetHIDButtons -> backboardd). Power locks/unlocks (screen "off" shows the kernel console because the panel never really turns off). **Device identity fixed: iPhone X** (home indicator, Face-ID-style Setup). Earlier test (0059u, `sweethidtest=15` fake Home presses) advanced Setup from Hello to the language list.
- **0058** HID: `iokit/Kernel/arm/hid/`: IOHIDEventServiceUserClient + IOHIDEventServiceQueue + IOHIDEvent compiled UNCHANGED from Apple IOHIDFamily-1915.140.3 (= exact version of the iOS 16.7 IOHIDLib, clone in `research/iohid-1915`) over our minimal IOHIDEventService (SweetHID.cpp: SweetHIDButtons consumer page 0x0C power 0x30 / vol 0xE9/0xEA / menu 0x40; SweetHIDTouch digitizer collections). C hooks `sweet_hid_key(key, down)` (0 power, 1 vol+, 2 vol-, 3 home) and `sweet_hid_touch(finger, down, x, y)`. HID logs go to IOLog. Boot-arg `sweethidtest=N` = fake Home press every N s.
- **0059** identity: hw.machine/hw.model/hw.target/hw.product from the ADT (macOS-config kernel used to answer "iPad8,6"/"Redmi Note 10 Pro"). mkadt: root compatible `D22AP|iPhone10,3|xiaomi,sweet|...`, model iPhone10,3, target-type D22, `/product` copied from the real D22AP device tree (`research/ipsw-x/d22ap.adt`, extracted from the IPSW, NOT in git), `/buttons home-button-type 2`. Codex report `codex/mg/report.md`: MG ProductType = sysctl **hw.product** (unrecognized -> iPod), HWModelStr = hw.target, HomeButtonType = `/buttons/home-button-type`; disk cache `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist` (keyed by build + UUID only -> stale iPod answers survived; reflashed clean v12 to clear it).
- **0060** drivers by Codex (`codex/input/hw-report.md`): `bsd/dev/sweet_keys.c` (SPMI arbiter v5 observer reads, PON 0x810 bits KPDPWR/RESIN SID0, PM6150L GPIO2 SID4 0xc110; works), `bsd/dev/sweet_touch.c` (GENI SE7 I2C @0xa84000, starts 45 s after boot). Touch result: SE7 fw ok (proto 3) but **0x5d and 0x38 both time out -> touch IC unpowered** (L11C LDO needs an RPMh vote). Codex task 8 = RPMh client (`codex/rpmh/`), task 7 = battery (`codex/battery/`).
- **0061** (CI 39117078444): red status bar "rdar:45025538" = UIKit "No status bar visual provider for screen" (360x800 pt is no real iPhone). AppleCLCD now presents **1125x2436** (iPhone X) and shows the centered 1080x2400; touch mapped the same; ADT canvas 1125x2436. `sweetfb_native=1` reverts.
- Images: `shim/out/shim-boot-0060b.img` (0060 + /buttons ADT `sweet-0060hi.adt`). Next: 0061 image with ADT from current mkadt.

### >>> HANDOFF 2026-10-17 late (read this first) <<<

**STATE: iOS 16.7 Setup.app "Hello" screen is ON THE PHONE** (boot `shim/out/shim-boot-0057u.img` on image v12). Photo `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg`. SpringBoard + backboardd + Setup run; nothing crashes in the GUI path. Remaining crash/relaunch loops: installcoordinationd (should be fixed by 0057, unverified), mediaserverd (VirtualAudio removed in v12, unverified), mobileactivationd (~100/boot, not analysed), bluetoothd + fairplayd.H2 relaunch constantly (no hardware).

**What is on the phone now:** userdata = image **v12** (`/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v12.img` + `.simg` + `.sha256`; v9 kept as fallback, v8/v10/v11 deleted or superseded). Kernel **0057** (`xnu/out-0057`, CI `39067532732`). ADT **`shim/out/sweet-0057hi.adt`** (QEMU twin `research/q0057-hi.adt`). Boot image **`shim/out/shim-boot-0057u.img`**. Boot args: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 wdt_test=no_user_checkin ufsrw=1 rootrw=1 launchd_unsecure_cache=1 wdt=-1`.

**Build a phone image** (kernel K, ADT A): `python3 tools/mkpayload.py $K $A shim/out/payload-X.bin --cmdline "$B" && (cd shim && ./build.sh ../shim/out/payload-X.bin && cp out/shim-boot.img out/shim-boot-X.img)` then check `python3 tools/unpack_bootv2.py shim/out/shim-boot-X.img shim/out/check-X && cmp shim/out/check-X/ramdisk shim/out/payload-X.bin`. QEMU smoke test: `python3 tools/mkpayload.py $K research/q0057-hi.adt $S/csq/payloadX.bin --ramdisk $S/csq/root-fork.img --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` + `PATH=~/swift/usr/bin:$PATH python3 tools/qemu-sweet.py ... --secs 40 --kernel $K --fail-on-panic` (S = scratchpad; root-fork.img lives in the session scratchpad csq/ dir and may be gone in a new session).

**Kernel workflow:** edit `research/bt28/xnu/...` (keep the pre-edit copy in `research/preNNNN/`), syntax check `python3 tools/xnu-cc.py research/run28.log research/bt28 <file>`, make `xnu/patches/NNNN-*.patch` with `diff -u pre bt28 | sed` path rewrite, add new/changed files to `research/check-patch-order.py` list, run it (must say applied + MATCH), commit + push -> GitHub Actions `xnu` builds (~8 min) -> `gh run download <id> -R dipa-studio/ios-sweet -n xnu-kernel -D xnu/out-NNNN`. **Repo is PUBLIC since 2026-10-17** (private macOS runner minutes ran out: "recent account payments have failed"); public = free runners. Commit trailer: only `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>`.

**Phone workflow (user does buttons, Claude runs commands):**
- Boot test kernel: phone in fastboot -> `fastboot boot shim/out/shim-boot-X.img`. NEVER `fastboot getvar`.
- **Read logs WITHOUT filming:** after a test the user holds Power+VolDown -> fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox, temp) -> wait for `adb shell true` -> `tools/sweet-log-pull.sh /run/media/dipa/android/ios-sweet-work/logs/<name>.txt` (reads the 4 MiB console ring the kernel keeps in the last 1025 blocks of userdata; patch 0047). Then `adb reboot bootloader` brings the phone back to fastboot without the user.
- **Flash a root image:** `fastboot flash -S 512M userdata <img>.simg` (7 min, 25 chunks). After a big flash the Xiaomi ABL fastboot hangs: next `fastboot boot` stalls at "Sending" -> the USER must re-enter fastboot by hand (Power+VolDown). Do not retry commands against the hung ABL. A flash right after `adb reboot bootloader` once failed on chunk 1 (USB protocol error): just retry. User must NOT unplug during flash (once interrupted at 25/25 -> reflash).
- **Edit the phone root without reflashing (same-length only):** find the file's raw offset in the local image (it is one extent; search the image for its first 4 KiB), compare with `adb exec-out dd if=/dev/block/sda34 ...`, then `adb push` changed 4 KiB blocks and `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back. Recovery kernel has no hfsplus.
- **Pull the whole phone root** (12 min): `adb exec-out "dd if=/dev/block/sda34 bs=1048576 count=16384" > img`; mount ro with udisksctl or `sudo mount -t hfsplus -o loop,ro`. To write into a pulled image: `sudo fsck.hfsplus -fy` first (volume is never cleanly unmounted -> Linux mounts ro even with -o force), then `sudo mount -t hfsplus -o loop,force`.
- Making images: copy latest img with `cp --sparse=always`, mount rw with force, change, `sync; umount`, `sha256sum`, `img2simg`. Keep only the latest image + one fallback on the SSD (/home is ~98% full; big work files live in `/run/media/dipa/android/ios-sweet-work/`, old kernels/images archived in `.../ios-sweet-work/archive/`).

**Diagnostics built into the kernel (all SWEET-only):** persistent console log (0047, boot-arg sweetlog=0 off; flush every ~1 s); `|name| text` copies of /dev/null writes for processes in `sweetnull` (default backboardd,SpringBoard; 0048); `IOK name:` IOKit lookup/open trace for `sweetiolog` (default backboardd,SpringBoard; 0049/0054, 400 lines max); `SWEET Sandbox: proc op N` (0050); `STR ...` heap text dump on SIGABRT/SIGTRAP for `sweetscan` (default backboardd,SpringBoard; 0051/0053) - this is how NSException/BSAssert reasons were found; `SMP name tN pc .. bt ..` user stack sampler for `sweetsample` (default SpringBoard,backboardd; first at 90 s then every 120 s, 40 samples, 16 frames; 0054/0055); `SWEET FB: N swaps` every 1000 swaps; `CRASH name ...` crash reports (0043/0044). Symbolicate cache addresses with `ipsw dyld a2s research/dsc/dyld_shared_cache_arm64 <addr - slide>`; main-binary addresses: addr - mh + 0x100000000.

**Patches added today (0046-0057, all CI-built):** 0046 IOSurface (IOCoreSurfaceRoot) + IOMobileFramebuffer (AppleCLCD on /arm-io/disp0) + arm-io nubs; 0047 persistent log; 0048 /dev/null tee; 0049 IOKit trace; 0050 permissive "Sandbox" MAC policy; 0051/0053 heap text on crash; 0052 RENAME_SWAP via exchangedata on HFS; 0054/0055 sampler, swap counter, AKS selectors 35 (extended device state = 17) and 101; 0056 panel copy from the vsync timer at 10 Hz (sweetfb_hz) instead of every swap; 0057 no config_ext_resolver (ACL group entries resolve without memberd). ADT (tools/mkadt.py): /arm-io/disp0, /chosen/display-scale 3, /chosen/unique-chip-id (synthetic 0x5357454554000001) + chip-id 0x8015 -> IOPlatformUUID A9683613-3704-53F2-95D0-98A8FB574E78. Image v9-v12: /private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}; launchd.plist StandardOut/ErrorPath renamed to ...PatX (pointing jobs at /dev/console stops them launching: EACCES); v12: LastSystemVersion=20H392 in plain /var/mobile/Library/Preferences/com.apple.migration.plist (stops the 1-hour data migration that ran every boot), VirtualAudio.plugin moved to /Library/Audio/Plug-Ins/HAL.disabled/.

**Codex helper** (`codex exec --skip-git-repo-check -m gpt-6.1-sol -c model_reasoning_effort=high -s workspace-write -C /run/media/dipa/android/ios-sweet-work/codex -o OUT "$(cat task.md)" < /dev/null`, run detached with setsid nohup; config already defaults to gpt-6.1-sol high). Reports in `/run/media/dipa/android/ios-sweet-work/codex/`: mediaserverd-report.md, installcoordinationd-report.md (-> 0057), ufs-performance.md (ranked UFS speed plan), **ufs/0058-sweet-ufs-faster.patch** (READY, not yet applied: ufslogsecs default 10 s log flush batching, optional ufscache=1 directional cache ops, optional ufswait=1 spin-then-sleep; syntax-checked, host-stub verified; see ufs/README.md). Apply it as patch 0058 after review.

**Claude safety-classifier note:** several messages about QuartzCore renderer selection / writing an HFS reader tool were cut off by an automatic classifier (false positives, user agrees). Keep those topics short or let them be; they are not blockers now (rendering already works).

**NEXT STEPS (in order):**
1. **Input** (Setup stuck on Hello): touch + power + volume as IOHIDEventService/IOHIDDevice services backboardd matches (log shows backboardd matching IOHIDDevice with DeviceUsagePairs and IOService with HIDServiceSupport=true). Phone hardware: Goodix/Focaltech touch over I2C/SPI (check live DT `dtb/`), buttons via PMIC (pon) and GPIO keys. Start with a fake HID service (e.g. power button via a timer or boot-arg) to learn the ABI, then real drivers.
2. **Device identity**: MobileGestalt reports iPod + Home button. Add /product node / product-type (iPhone10,3, D22AP), device class iPhone, home-button-less (Face ID) properties in mkadt; find exact MG keys (MGIOMFBSupport.c, `IODeviceTree:/product` lookups seen in backboardd trace).
3. **Battery**: AppleSmartBattery/IOPMPowerSource style service (status bar shows empty red battery).
4. Apply Codex 0058 (UFS speed), consider cpus>1, check whether installcoordinationd/mediaserverd loops are gone, analyse mobileactivationd.
5. Hide kernel console over the GUI when not debugging: boot-arg sweetfb_noconsole=1 (but then panics are not on screen).

- **🎉 MILESTONE: iOS GUI ON THE PHONE - Setup.app "Hello" screen (2026-10-17 ~21:30 UTC, boot 0057u on image v12).** Photo: `/run/media/dipa/android/ios-sweet-work/MILESTONE-setup-hello-2026-10-17.jpg` (animated "dobar d(an)" hello lettering, status bar "iPod" + battery icon, bottom "Pritisnite Home za otvaranje" = "Press Home to open" (locale hr), (i) button). Rendered by iOS 16.7 SpringBoard/Setup through CoreAnimation -> backboardd -> kernel IOSurface (IOCoreSurfaceRoot) -> kernel AppleCLCD swaps -> ABL panel memory. What made it: data migration finally skipped (v12: `LastSystemVersion` 20H392 in the plain `/var/mobile/Library/Preferences/com.apple.migration.plist`; ADT `/chosen/unique-chip-id` + `chip-id` for IOPlatformUUID), 0057 (no ext resolver -> ACL containers work), plus everything before (0046 display/IOSurface, 0050 Sandbox policy, display-scale 3, containers dirs, RENAME_SWAP, AKS 35/101, 10 Hz present).
  **Missing (next work, in rough order):**
  - **Input: no touch, no power button, no volume buttons** (no HID drivers; backboardd looks for IOHIDDevice / HIDServiceSupport services). Setup is stuck on "Hello".
  - **Device identity: it thinks it is an iPod with a Home button** (status bar "iPod", "Press Home to open"): MobileGestalt has no product/model identity (no /product node, product-type, etc.) - give it iPhone10,3 / home-button-less (Face ID class) identity.
  - **No battery detection** (no battery/charger/PMIC service; status bar battery shows empty/red).
  - Locale came up Croatian (hr) - harmless.
  - Performance: cpus=1, polled UFS (Codex UFS patch in progress: `codex/ufs/`), backboardd presents at 60 Hz.
- **README refreshed (2026-10-17):** read the full notes and updated the public overview through patch 0045, v7 hardware observations and prepared v8 diagnostics. Documents real Apple userspace, the missing display/IOSurface GUI work, limited security services, highmem, persistent userdata root, current tooling and build examples. Documentation only; no kernel build, tests, flashing or phone boot performed.

- **v11 still migrated (boot 0056u, 20:32 UTC, `logs/boot-0056u-v11.txt`).** On iOS kCFPreferencesCurrentHost lands in the plain plist: all DMEnvironment setters (setLastBuildVersionPref, setUserDataDispositionPref, ...) use CurrentHost and the phone's `/var/mobile/Library/Preferences/com.apple.migration.plist` holds DMUserDataDisposition; datamigrator's XPC service runs with `_RoleAccount: mobile`. **Image v12** = v11 + `LastSystemVersion` = 20H392 added to that plain `com.apple.migration.plist` (keeps DMUserDataDisposition, 501:501 0600) + `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin` moved to `/Library/Audio/Plug-Ins/HAL.disabled/` (Codex: stops the mediaserverd SIGSEGV loop; untested). **installcoordinationd loop explained (Codex `codex/installcoordinationd-report.md`):** os_crash "Failed to create data directory" EACCES for `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.installcoordinationd/Library/InstallCoordination`: `Library`/`Library/Caches` in the container are ACL-only (uid/gid 0xfffffffe, mode 0000, ACE for group GUID ...012B = gid 299 systemusers); with `config_ext_resolver` the kernel asks an identity resolver (memberd/opendirectoryd) that iOS does not run -> EWOULDBLOCK -> ACE skipped -> EACCES. **Patch 0057**: drop config_ext_resolver from FILESYS_BASE (compatibility UID/GID<->GUID mapping is used instead), likely fixes other ACL-protected containers too. Codex task 3: UFS driver performance design (`codex/ufs-performance.md`).
- **mediaserverd SIGSEGV loop explained (Codex report `/run/media/dipa/android/ios-sweet-work/codex/mediaserverd-report.md`):** the fault (FAR 0x390) is in the HAL plug-in `/Library/Audio/Plug-Ins/HAL/VirtualAudio.plugin/VirtualAudio` (ApplyBeamFormerPreference <- VirtualAudio_PlugIn::SetPropertyData <- HALS_AHPPlugIn::ObjectSetPropertyData <- AudioObjectSetPropertyData <- MediaExperience vaemVADSerializationListener): the default virtual audio device ('vdef', VirtualAudioDevice_Default) does not exist (no audio hardware/driver, no /product/audio). Proposed workaround for GUI bring-up: move VirtualAudio.plugin out of /Library/Audio/Plug-Ins/HAL/ in the next root image (untested). v11 reflashed OK after an interrupted flash (USB unplugged at chunk 25/25). Codex task 2: installcoordinationd crash loop.
- **ROOT CAUSE of the endless migration: no IOPlatformUUID (2026-10-17).** datamigrator's `-[DMMigrator isMigrationNeededWithBuildVersion:lastBuildVersion:clientPID:]` gets lastBuildVersion from `-[DMEnvironment lastBuildVersionPref]` = `CFPreferencesCopyValue("LastSystemVersion", "com.apple.migration", kCFPreferencesCurrentUser, kCFPreferencesCurrentHost)` -> a ByHost file. The phone had `/var/mobile/Library/Preferences/com.apple.migration.plist` (only DMUserDataDisposition) and NO `Preferences/ByHost` directory at all. On arm XNU publishes IOPlatformUUID (gethostuuid) only from `/chosen/unique-chip-id` (8 bytes) + `/chosen/chip-id` (4 bytes) (IOPlatformExpertDevice::generatePlatformUUID, called from IOPlatformExpert::start); the SWEET ADT had neither, so every CurrentHost preference write failed. Fix: mkadt adds `unique-chip-id` = 0x5357454554000001 (synthetic) and `chip-id` = 0x8015 -> UUID `A9683613-3704-53F2-95D0-98A8FB574E78` (same SHA1 namespace computation as the kernel). ADT `shim/out/sweet-0057hi.adt`, boot image `shim/out/shim-boot-0056u.img` (0056 kernel + 0057hi ADT, QEMU OK). **Image v11** = v10 + `Preferences/ByHost/com.apple.migration.<UUID upper and lower>.plist` {LastSystemVersion: 20H392} (501:501, dir 0755 files 0600). Flashing v11 2026-10-17 ~20:10 UTC. Codex (gpt-6.1-sol high) analysing the mediaserverd SIGSEGV loop in `/run/media/dipa/android/ios-sweet-work/codex/` (report `mediaserverd-report.md`).
- **v10 did NOT stop the migration (boot 0056n on v10, 19:18 UTC, `logs/boot-0056n-v10.txt`):** datamigrator + migrationpluginwrapper ran again, backboardd drew the progress UI (13000+ swaps in ~5 min). So `com.apple.DataMigration.plist`/LastSystemVersion is not the deciding input. What is known about the decision (datamigrator XPC service `DataMigration.framework/XPCServices/com.apple.datamigrator.xpc/com.apple.datamigrator`, strings): `Migration sentinel present. Migration necessary.` (sentinel `/private/var/datamigrator/migrate`, created and removed by datamigrator itself; absent in v10), `System build version changed from %@ to %@. Migration necessary.` / `...unchanged... not necessary`, `Disposition dictionary with build version %@ is out of date relative to current build version %@`, `SyntheticDidUpgrade`, DMUserDataDispositionManager; previous build source not found yet (not in the binary's plain strings; likely in DataMigration.framework's DMUserDataDispositionManager / preferences domain `com.apple.migration`). backboardd calls `DMPerformMigrationIfNeeded` and holds SpringBoard in `checkInAndWaitForDataMigration` until it returns. NEXT: find where the previous build version / disposition dictionary is stored (disassemble DataMigration.framework DMUserDataDispositionManager + datamigrator's isMigrationNeeded path), write it into the image; or get datamigrator's os_log out (OS_ACTIVITY_DT_MODE needs a launchd env change).
- **Historical failed v10 hypothesis (image v10, 2026-10-17; disproved by the later v10 test).** Boot 0056n (18:16 UTC, `logs/boot-0056n.txt`, 30 min): 10 Hz panel copies, backboardd still presents at ~60 Hz (107k swaps), SpringBoard still in `BKSSystemShellService _checkIn` at sample 14. Every migration run takes 1+ hour on cpus=1 and repeats each boot. The then-unverified hypothesis used `/var/mobile/Library/Preferences/com.apple.DataMigration.plist` key `LastSystemVersion` (vs ProductBuildVersion 20H392); v10 disproved it, and v12 instead used the migration domain as documented above; the pulled phone root (21:01 local) had NO such file. **v10** = that pulled phone state + fsck.hfsplus -fy (volume was marked not cleanly unmounted -> Linux mounts it read-only even with -o force; fsck found only hard-link counts + minor volume header, repaired) + `com.apple.DataMigration.plist` {LastSystemVersion: 20H392} (501:501 0600). `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v10.img` (+ .sha256, .simg); v8 files deleted, v9 kept as fallback.
- **Repo made PUBLIC (2026-10-17, user request) so GitHub-hosted macOS runners are free:** the 0056 CI run was refused ("recent account payments have failed or your spending limit needs to be increased"). Checked before: no device dumps, serials, IMEI or Apple binaries in the history (.gitignore keeps backup/, dtb/, recovery/, research/ out); commit author emails are public now. 0056 rerun `39056660104` passed -> `xnu/out-0056`, QEMU OK, image `shim/out/shim-boot-0056n.img` booted 18:16 UTC.
- **Boot 0055n (17:16 UTC, ~65 min, `logs/boot-0055n.txt`): migration bar reached 99% in ~30 min (was ~60), then crawled.** Root cause of the slowness: backboardd presents the progress UI at ~58 Hz (**167,000 swaps in ~48 min**) and AppleCLCD copied the full 10 MB frame into the panel on every swap -> ~600 MB/s memcpy on the single CPU (cpus=1), starving everything (polled UFS I/O too). Sampler (16 frames): **SpringBoard waits in `-[BKSSystemShellService _checkIn]`** (synchronous BSXPC call to backboardd, from FBSystemShellInitialize <- SBSystemAppMain) - backboardd holds the system shell check-in until the data migration ends, so the migration is the gate to SpringBoard UI. **Patch 0056**: swap only records the latest swap record; the vsync timer copies it to the panel every 60/sweetfb_hz ticks (default 10 Hz); `SWEET FB: N swaps` every 1000.
- **Boot 0054n (16:53 UTC, ~12 min, `logs/boot-0054n.txt`, patch 0054 sampler):** the data migration runs AGAIN on every boot (it completed once in the 0053s run) - completion is not being recorded. backboardd keeps swapping the progress UI (3700+ swaps in ~10 min, `SWEET FB: N swaps`). Sample during migration: SpringBoard main thread blocked in a synchronous XPC call (`mach_msg2_trap <- dispatch_mach_send_and_wait_for_reply <- xpc_connection_send_message_with_reply_sync <- -[BSXPCServiceConnectionMessage _sendSynchronously:] <- BSXPCServiceConnectionProxy ...`). Unsupported AKS selectors seen: 101 `aks_assert_consume`, 93 `aks_get_internal_info`, 34 `_aks_stash_load` (datamigrator), **35 `aks_get_extended_device_state`** (SpringBoard, chronod, remindd, searchd, symptomsd...). **Patch 0055**: AKS 35 answered like 17 (same DER device state), 101 succeeds; sampler backtraces 16 frames, 40 samples (~80 min).
- **MILESTONE: FIRST iOS PIXELS ON THE PANEL (boot 0053s long run, 15:33 UTC, ~60 min; photos IMG_20261017_183029/183222/183419; log `/run/media/dipa/android/ios-sweet-work/logs/boot-0053s-long.txt`, 407 KB, 1428 flushes).** The iOS data-migration boot screen (Apple logo + progress bar) was shown and the bar advanced to full in ~60 minutes. It is drawn by **backboardd through our kernel display path**: `SWEET SURF: backboardd create id 2/3 1080x2400 fmt 0x42475241 (BGRA) bpe 4 bpr 4352 size 10452992 keys 11`, IOSurface sels 9, 27, 5, 34 and traps 2/3 (lock/unlock), IOMFB SwapBegin (4) / SwapEnd (5, 1132-byte struct) / GetLayerDefaultSurface (3) / 68 / 55, then `SWEET FB: swap N layer 0 surface 2|3 1080x2400 ... a 0,0 1080x2400 b 0,0 1080x2400` alternating (double buffering; only the first 16 swaps are logged). Triggered by `com.apple.datamigrator` (AKS sels 101/93/34 return unsupported) and `com.apple.migrationpluginwrapper`. Probably ProgressUI-style CoreGraphics drawing into IOSurfaces (no GPU used). After the migration: SpringBoard and backboardd stay up (exec once each, no crash), nothing new drawn; crash loops only for mediaserverd, installcoordinationd, mobileactivationd (~108 each in the hour); bluetoothd and fairplayd.H2 relaunch constantly (no hardware). Kernel console text overlays the image (sweetfb_noconsole=1 would hide it).
- **MILESTONE: SpringBoard and backboardd both stay up (boot 0053s on v9, 15:29 UTC, `logs/boot-0053s.txt`).** With /chosen/display-scale = 3: `exec SpringBoard` once, `exec backboardd` once, no CRASH for either; MobileGestaltHelper reads IOMFB size/dot pitch; backboardd opens AppleCLCD (sels 57,15,22,29,33,79,74 as before). No IOSurface creates and no swaps: backboardd keeps polling `IOProviderClass IOAcceleratorES` (-> 0 found) and AGXAccelerator/IOAcceleratorESLegacy - no GPU, so no CoreAnimation renderer yet. Log goes quiet after ~47 s (only 47 flushes): the system idles. NEXT WALL: CoreAnimation rendering without a GPU (CPU path) so the window server produces frames.
- **SpringBoard's invalid mode = scale 0 (boot 0053n, 15:19 UTC, `logs/boot-0053n.txt`, heap scan):** `FBSDisplayMode cannot be configured as requested : <FBSDisplayMode: ...; infxinf@0x (1080x2400/0) 60Hz sRGB SDR>` - pixel size and 60 Hz are fine, scale is 0. libMobileGestalt (MGIOMFBSupport.c, sub_19c560a54) reads `display-scale` (u32, default 0) and `display-rotation` from **IODeviceTree:/chosen**, pixel size via IOMobileFramebufferGetDisplaySize (MobileGestaltHelper sel 8/28 in the log). mkadt now adds `/chosen/display-scale` = 3 (1080x2400 @3x = 360x800 pt). ADT `shim/out/sweet-0054hi.adt` (QEMU `research/q0054-hi.adt`), image `shim/out/shim-boot-0053s.img` = 0053 kernel + 0054hi ADT. Possible catch: MobileGestalt may have cached scale 0 in `/private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/...`.
- **MILESTONE: backboardd survives and opens the display (boot 0052n on v9, 15:07 UTC, `logs/boot-0052n.txt`).** No `CRASH backboardd`. It walks `IODeviceTree:/arm-io` children, matches IOMobileFramebuffer, `open AppleCLCD type 0 -> 0x0`, calls IOMFB selectors 57, 15, 22, 29, 33, 79 (GetBlock, out 1580/40), 74 (SupportedFrameInfo), 12, 6, 27, 17, 84, 50; opens IOCoreSurfaceRoot (sel 13); looks for AGXAccelerator / IOAcceleratorES / IOAcceleratorESLegacy (none, repeatedly), `IODeviceTree:/product` (none, repeatedly), `/buttons`, aop-smart-cover, IOPMrootDomain. No swaps yet. **SpringBoard now gets past display discovery** and dies (sig 5) in `-[FBSDisplayMode _initWithWidth:height:preferredScale:scaleOverride:refreshRate:gamut:hdr:rotation:virtual:validityCheck:]+580` <- `_initWithCADisplayMode:scale:rotation:` <- `FBSDisplayConfiguration _initWithImmutableDisplay:` <- `FBSDisplaySource initWithDisplay:` <- `FBSDisplayMonitor` (slide 0x14504000): "FBSDisplayMode cannot be configured as requested". Checks: width/height >= 2, preferredScale > 0, scaleOverride >= 0, refreshRate non-zero, valid gamut/HDR/rotation. Suspects: refresh rate 0 (IOMFB timing blocks answered with zeros) and/or scale 0 (MobileGestalt main-screen-scale; no /product node in the ADT). **Patch 0053**: heap text scan also on SIGTRAP and for SpringBoard (default sweetscan list backboardd,SpringBoard) to read the exact mode description.
- **Image v9 (2026-10-17) = v8 + `/private/var/containers/{Bundle,Data/System,Shared/SystemGroup,Temp}` (root:wheel 0755; on iOS these live on the data volume, absent from the rootfs) + launchd.plist with StandardOutPath/StandardErrorPath renamed to ...PatX (the in-place phone fix; daemons' stdout reaches the log via the 0048 /dev/null tee).** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v9.img` SHA256 aa9f9139...6e67, `.simg` 12,145,303,864 bytes; written through `sudo mount -t hfsplus -o loop,force`. **Patch 0052** (`xnu/patches/0052-sweet-hfs-rename-swap.patch`, CI `39042761826` -> `xnu/out-0052`, QEMU OK, image `shim/out/shim-boot-0052n.img`): vn_rename falls back to VNOP_EXCHANGE when VNOP_RENAMEX(RENAME_SWAP) returns ENOTSUP for two regular files on one volume (HFS exchange swaps data and cnode descriptors = swap semantics). Flashing v9 started 2026-10-17 ~15:00 UTC.
- **backboardd EXCEPTION FOUND (boot 0051n, 14:41 UTC, `logs/boot-0051n.txt`, patch 0051 heap scan):** `*** Terminating app due to uncaught exception 'NSInvalidArgumentException', reason: '*** -[NSURL initFileURLWithPath:]: nil string parameter'`. First-throw stack (slide 0x337f0000): `+[NSURL fileURLWithPath:]` <- `-[BSSystemContainerForCurrentProcessPathProvider libraryPath]` <- `cachesPath` <- backboardd main+0x1d858 (StartWindowServer, shader cache path). BaseBoard: libraryPath = `BSSystemSharedResourcesDirectoryForIdentifier` = `BSSystemSharedDirectoryForIdentifier(id)` + "/Library"; that calls `container_system_path_for_identifier` (libsystem_containermanager -> `_container_legacy_lookup` -> containermanagerd XPC), which returned NULL (BaseBoard logs "Error getting shared system container ..."). With 0050 the sandbox denials are gone. containermanagerd.log.0 in the pulled (pre-0050) image: "Did not receive any persona attributes", "Expected to find at least one persona", notify_register_dispatch failed 9; `/private/var/containers` does NOT exist in the root image (on iOS it lives on the data volume). usermanagerd does create kernel personas 99/199/1000, but fails to save `/private/var/keybags/usersession.kb` and `persona.kb`: "Failed to atomically swap writing file: Operation not supported (45)" (HFS has no RENAME_SWAP). NEXT: create `/private/var/containers` (and check what containermanagerd needs for system group containers), fix or emulate RENAME_SWAP on HFS, then re-check backboardd.
- **Disk housekeeping (2026-10-17):** /home was at 4 GiB free. Moved (not deleted) `xnu/out-0010..0044` and old `shim/out/*.img`/`payload-*.bin` (everything before 0046) to `/run/media/dipa/android/ios-sweet-work/archive/{xnu,shim-out}` (6.3 GiB); /home now 8.7 GiB free. Large work files (phone-root.img 16 GiB, logs, tracev3 dumps) live in `/run/media/dipa/android/ios-sweet-work/`. **Patch 0051** (`xnu/patches/0051-sweet-crash-heap-strings.patch`, CI `39041440935`): on SIGABRT of a process in boot-arg `sweetscan` (default backboardd) the crash log prints heap text runs as `STR ...` (to find the NSException reason). Boot 0051n 14:41 UTC.
- **Boot 0049n (14:11 UTC, `logs/boot-0049n.txt`, patch 0049 trace): backboardd's IOKit lookups before it dies** (each run): `IODeviceTree:/arm-io/pearl-sep` -> none, matching ApplePearlSEPDriver -> none, `IOService:/IOResources/AppleKeyStore` open OK, matching IOHIDDevice (DeviceUsagePairs) / `HIDServiceSupport` notifications, `usb-drd,t8027` notification; **never any IOMobileFramebuffer / display lookup** - the exception happens before display detection. launchd (tracev3) shows backboardd's mach lookups denied with `error = 159: Sandbox restriction`: com.apple.mobilegestalt.xpc, com.apple.iohideventsystem, com.apple.system.notification_center, com.apple.logd, containermanagerd, ACCHWComponentAuthService, oscard. libsystem_sandbox uses `__mac_syscall("Sandbox", op, arg)` (ops: 1 init, 2 check, 3 note, 4 container path, 5/6/7/8 extensions, 0x15 check_bulk, ...); with no policy named "Sandbox" every call gets ENOPOLICY. **Patch 0050** (`xnu/patches/0050-sweet-sandbox-policy.patch`): built-in permissive MAC policy "Sandbox" in sweet_amfi.c (mpo_policy_syscall returns 0, container/extension ops ENOENT; logs first use of each op as `SWEET Sandbox: proc op N`).
- **Phone root pulled (16 GiB, 12 min, `adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` (loop-mounted ro at /run/media/dipa/iOSRoot).** No .ips crash reports. logd tracev3 (Persist, LZ4 `bv41` blocks, decompressed strings in `ios-sweet-work/tracev3/all.txt`): /private/var/db/uuidtext is EMPTY so only launchd's own messages are readable. Findings: v8 launch failure = `Service could not initialize: posix_spawn(/usr/libexec/backboardd), error 0xd - Permission denied` (xpcproxy exit 78) - /dev/console not openable for the mobile user; backboardd[98] spawned `com.apple.MTLCompilerService` before SIGABRT; **launchd denies many mach lookups with `error = 159: Sandbox restriction`** (mediaserverd -> com.apple.backboard.display.services, remoted, mobiletimerd -> sleepd, identityservicesd -> apsd) and **tccd exits OS_REASON_SANDBOX "profile not found"** - no Sandbox kext/profiles on SWEET; likely cause of many daemon crash loops (next wall after the display). CF's uncaught-exception text never reaches stderr for daemons (no CF handler; libc++abi prints only the type). **Patch 0049** (`xnu/patches/0049-sweet-iokit-trace.patch`): `IOK name: ...` console lines for registry path lookups, child iterators, matching (with result count/class), matching notifications and IOServiceOpen of the processes in boot-arg `sweetiolog` (default backboardd), max 400 lines.
- **CONFIRMED: launchd StandardOut/ErrorPath=/dev/console stops backboardd from launching.** After the in-place rename (boot 0047n-b, log `logs/boot-0047n-b.txt`) backboardd launches again and dies as on v7: sig 6, `___pthread_kill <- abort <- demangling_terminate_handler <- _objc_terminate <- std::terminate <- _dispatch_client_callout <- _dispatch_once_callout <- main+0x9334` (window-server dispatch_once). It never opened AppleCLCD or IOCoreSurfaceRoot (no `SWEET FB/SURF: backboardd` lines) -> throws before/at display detection. **Patch 0048** (`xnu/patches/0048-sweet-devnull-tee.patch`, CI `39037749668` -> `xnu/out-0048`, image `shim/out/shim-boot-0048n.img`): writes to /dev/null by processes named in boot-arg `sweetnull` (default `backboardd,SpringBoard`) are printed as `|name| text`. Boot 0048n (13:48 UTC, log `logs/boot-0048n.txt`): only `|backboardd| libc++abi: terminating due to uncaught exception of type NSException` (CF's reason line goes to os_log, not stderr, despite CFLOG_FORCE_STDERR/OS_ACTIVITY_DT_MODE). Next: pull the whole 16 GiB root from recovery (`adb exec-out dd if=/dev/block/sda34`) to `/run/media/dipa/android/ios-sweet-work/phone-root.img` and read ReportCrash .ips files / logd tracev3 for the exception reason.
- **Persistent log WORKS (boot 0047n on v8, 13:31 UTC; pulled from OrangeFox: 70 KB, 111 flushes, `/run/media/dipa/android/ios-sweet-work/logs/boot-0047n.txt`).** In 3 min **backboardd was never exec'd** (v7 ran it), ~70 bare `exec xpcproxy`, SpringBoard loops on FBSDisplayMonitor (no display), mediaserverd sig 11 loop, locationd, lockdownd sig 5. Suspect the v8 plist (StandardOut/ErrorPath=/dev/console on backboardd). **In-place plist edit from recovery (no reflash):** launchd.plist is one extent at image/partition byte offset 0x1e025f000 (195 blocks; verified bytes identical on phone vs local v8 mount); renamed StandardOutPath->StandardOutPatX and StandardErrorPath->StandardErrorPatX (same length, both jobs) in blocks 68 and 105 via `adb push` + `dd of=/dev/block/sda34 seek=... conv=notrunc,fsync`, read back VERIFIED. Phone now differs from local v8 image in those 2 blocks (files in `/run/media/dipa/android/ios-sweet-work/`). Test boot 0047n 13:38:42 UTC. Recovery kernel has no hfsplus (raw block edits only).
- **Patch 0047: persistent console log (CI `39036478663` -> `xnu/out-0047`, QEMU no panic; phone image `shim/out/shim-boot-0047n.img` = 0047 + sweet-0046hi.adt + 0045n cmdline).** `_cnputs` (all console output: kernel printf + daemons' /dev/console) also appends to a 4 MiB ring in sweet_ufs.c; after the UFS partition is ready and writable (ufsrw=1) a thread writes new ring blocks + header to the LAST 1025 blocks (4 KiB) of userdata every ~1 s and SYNCHRONIZE CACHE (prints `SWEET LOG: console log to the last 4100 KiB ...`). Read: phone to fastboot -> `fastboot boot recovery/recovery.img` (OrangeFox) -> `tools/sweet-log-pull.sh OUT.txt` (adb dd of that area + `tools/sweet-log.py`). Not yet verified on the phone. Panics after the last flush are not in it (screen still shows them). 2x font attempt reverted: XNU's v_scale only scales the progress icon.
- **Boot 0046n on v8 (13:05 UTC, VID_20261017_150522_HSR_120):** phone prints `SWEET SURF: IOCoreSurfaceRoot registered` and `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1` (nubs + match work on hardware). Visible userspace: early boot tasks, launchd_cache_loader, `exec SpringBoard`; no `exec backboardd` / `SWEET FB: backboardd` line seen in the readable frames (video blurry). Frame 00:47: lower half of the screen shows OLDER console text (16:01:12) below newer lines -> unconfirmed hint that a swap copied an old snapshot of the panel (CA reads the default/displayed surface = panel memory). SpringBoard still dies in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` (sig 5, slide 0x30960000). **Shim: 2x console font** (`shim/loader.c` Video.v_depth scale field = 1) so phone videos are readable; image `shim/out/shim-boot-0046b.img` = 0046n + 2x font.
- **Patch 0046: built-in IOSurface + IOMobileFramebuffer (2026-10-17, offline, NOT phone-tested).** `xnu/patches/0046-sweet-iosurface-iomfb.patch`: new `iokit/Kernel/arm/SweetSurface.{h,cpp}` (IOCoreSurfaceRoot + IOSurfaceRootUserClient: sel 13/0/4/34/35, traps 0-5, wired buffers mapped into the caller, per-client refs) and `SweetFramebuffer.cpp` (AppleCLCD : IOMobileFramebuffer on /arm-io/disp0: sizes, swap = CPU copy of enabled layers into the ABL panel memory, 60 Hz vsync via sendAsyncResult64WithOptions(CanDrop), panel memory published as the default IOSurface, kernel text console paused on the first swap only with `sweetfb_noconsole=1` (default keeps the console: pausing switches it to serial and would hide panics)); SweetPlatformExpert creates nubs for /arm-io children (not gic) attached to the platform expert (IOPlatformDevice::compareName casts its provider to IOPlatformExpert, so nubs under the arm-io nub never matched - first CI build showed that in QEMU). mkadt: /arm-io/disp0 {device_type display-subsystem, compatible sweet,display, canvas-width 1080, canvas-height 2400}. CI `39021572169` -> `xnu/out-0046`. **QEMU** (`research/q0046-hi.adt`, RAM disk init, msgbuf): `SWEET SURF: IOCoreSurfaceRoot registered`, `SWEET FB: AppleCLCD 1080x2400 stride 4320 at 0x9c000000, default surface 1`, init alive, no panic. Phone image **`shim/out/shim-boot-0046n.img`** (SHA256 9c4d2fe9..., CI `39024108588` with the review fixes: swap bounds check, zeroed 64-bit async ref, port release, 1.5 GiB wired budget, ref leak/race fixes; QEMU re-checked) = 0046 kernel + `shim/out/sweet-0046hi.adt` + the 0045n cmdline; boot it on image v8 (backboardd/SpringBoard log to console) and film. Expected new console lines: `SWEET SURF: <proc> create id ...`, `SWEET FB: backboardd sel N ...`, `SWEET FB: swap ...`. Open question for the next wall: QuartzCore's IOMFB server builds its renderer from Metal first (`CAMetalContextCreate`), GLES only when enabled; how the CPU renderer gets selected on a device without a GPU is not yet established.
- **IOSurface values ABI (offline RE, `/run/media/dipa/android/ios-sweet-work/iosurface-values.md`) - TODO in SweetSurface (0046 only accepts and drops values, so IOSurfaceCopyValue always returns NULL):** sel 9 SetValue in = {u32 id, u32 pad, IOCFSerialize([value, key]) or ([dict] = merge)}, sel 0xb RemoveValue in = {u32 id, u32 pad, key\0} (empty key = remove all); both out 4 bytes = new generation, client accepts only (gen+2)|1. Kernel after each change: gen = (gen+2)|1 (odd, never 0) -> state+0x20, serialized size (>=1) -> state+0x28. sel 0xa in {u32 id, u32 0, u8 0}, out {u32 ?, u32 gen, serialized non-bulk dict}; too small -> 0xe00002db + needed size (client retries x16). sel 0x1b in 0x88: bulk struct 0x70 @0, u64 valid size @0x70, u64 changed mask @0x78, u32 id @0x80 -> copy masked fields into state+0x30 (bit0 32B @0, bit1 16B @0x20, bit2 8B @0x30, bits3-10 1B @0x38..0x3f, bits11-14 24B @0x40/4B @0x58/8B @0x5c/1B @0x64).
- **IOMFB display matching confirmed (offline RE, `/run/media/dipa/android/ios-sweet-work/iomfb-match.md`):** the framework never matches on "AppleCLCD"; any registered IOMobileFramebuffer subclass works. `iomfb_match_callback` reads only `dfr`/`AppleTV`/`external` (CFBoolean, service itself, no parents); internal main display = all absent/false (type 0, name "primary"). Display count = /arm-io children whose device_type starts with "display-subsystem" (count 0 -> CreateDisplayList returns NULL; more nodes than services -> 30 s wait). IOMobileFramebufferOpen fails only on IOServiceOpen failure; canvas-width/height read as 4-byte CFData from the IOService-plane parent (optional). CopyProperty = IORegistryEntrySearchCFProperty on the service only. Patch 0046 (disp0 node, `external`=false, AppleCLCD : IOMobileFramebuffer) fits all of this.
- **IOMobileFramebuffer swap + notification ABI (2026-10-17, offline).** Swap record = fb+0x18, **0x46c bytes**, zeroed by SwapBegin and sent whole by `kern_SwapEnd` = IOConnectCallStructMethod(sel 5, rec, 0x46c, no output). **SwapBegin** = sel 4, no input, 1 scalar out = swap id (stored at rec+0x50). `kern_SwapSetLayer(fb, layer<4, IOSurfaceRef, CGRect a, CGRect b, flags)`: rec+0x54+4*layer = **IOSurface id**; rec+0x104 bit layer = layer enabled (rec+0x108 bit cleared); rect a (int x,y,w,h, scaled) at rec+0x64+16*layer, rect b at rec+0xc4+16*layer; rec+0x114+4*layer = transform from flags&0xf; flag bits 5/31/6/7/8/9 set bytes rec+0x2ca/0x2cc/0x2e3/0x2e5/0x2e6/0x467+layer. A NULL surface only sets the enable bit with zero id. SwapWait = sel 6 scalars [swap id, timeout, 0].
  - **Notifications**: `IOMobileFramebufferScheduleWithDispatchQueue`/`GetRunLoopSource` create an IONotificationPort and `IOConnectSetNotificationPort(conn, type, port, 0)` (kernel `registerNotificationPort`). `kern_EnableNotifications(fb, type, cb, ctx)` = **sel 72 scalars [NotifyCallbackFuncs[type], fb, type, 0]** -> the kernel keeps an async reference {port, func, refcon=fb} per type and fires it with `sendAsyncResult64`. Types: 0 HotPlug, 1 Power, 3 FrameInfo (args[0] = mask of 31-bit keys, args[1] u32, then values), 4 CRC, **5 Vsync**: 6 args, each a 32-bit half in a u64 slot: (ts lo, ts hi), (t2 lo, hi) passed through the time-ingest helper, (t3 lo, hi); the framework then calls the client's vsync callback(fb, ts, t2', t3, ctx). Vsync callbacks are dropped while the notification port has queued messages.

- **IOSurface.framework user-client ABI reversed (2026-10-17, offline, step 2 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOSurface` (selector scan script: scratchpad `selscan.py`).
  - Connect (`_iosConnectInitalize`, pthread_once): `IOServiceGetMatchingService(IOServiceNameMatching("IOCoreSurfaceRoot"))`, retried with sleep(1) up to 241 times (a missing service stalls every client ~4 min, no crash); `IOServiceOpen(type 0)`; then **sel 13** (no inputs, struct out 0x18 bytes = `_ioSurfaceLimits`) and requires u16 at out+0x16 == 1 (ABI version); out+0 = offset/plane-base alignment mask, out+4 = bytes-per-row alignment mask (used as (x+m)&~m), +0..+0x14 also copied into IOSurface remote-method init, otherwise logs and closes the connection.
  - **Create = sel 0**: scalar in [parent id or 0], struct in = `IOCFSerialize(props, kIOCFSerializeToBinary)` (OSUnserializeBinary format; keys IOSurfaceWidth/Height/BytesPerRow/BytesPerElement/PixelFormat/AllocSize/PlaneInfo/CacheMode/IsGlobal/...), struct out **0xa68 bytes** ("lock result"). **Lookup = sel 4**: scalar in [id], same struct out. LookupFromMachPort = sel 0x22 (scalar in [port name]); CreateMachPort = sel 0x23 (scalar in [id, options], scalar out [port name]).
  - Lock result (copied to client+0x68, size 0x68 + planes*0x80, min 0xe8): 0x00 u64 base address **mapped in the caller's task**; 0x08 u64 task VA of a per-surface shared state page (+0 u64 registry id, +8/+0xa u16 bound accel ids, +0xc u32 seed, +0x14 u8 tiled, +0x20 u32 value generation, +0x24 YCbCr matrix, +0x28 u32 non-bulk values size, +0x2d u8 displayable, +0x2e u8 sysmem-only, +0x30 0x70 bytes bulk attachments); 0x10 u64 task VA of timestamp page (4 u64 indexed timestamps, +0x20 detach code); 0x18 u32 surface id; 0x1c u32 alloc size; 0x20 width; 0x24 height; 0x28 bytes per row; 0x2c buffer offset; 0x30 pixel format; 0x34 u32 (dcache flush length); 0x38 plane count; 0x40 u16 bytes/element; 0x42 u8 element width; 0x43 u8 element height; 0x44 cache mode; 0x4c u8 subsampling; 0x4d u8 prohibit-use count; 0x50 parent id; 0x54 slice count; 0x58 u64 trace id; 0x60 u64 protection options; planes[n] at 0x68+n*0x80 (+0 width, +4 height, +8 bytes/row, +0xc offset, +0x14 size, +0x18 u16 bpe, +0x1a/+0x1b u8 element w/h, +0x1c u8 component count, +0x1d address format, +0x54 u8 compression type (non-zero -> no CPU base address)).
  - **Traps** (IOConnectTrapN -> `IOUserClient::getTargetAndTrapForIndex`): 0 IncrementUseCount(id, category), 1 DecrementUseCount(id, category), 2 **Lock**(id, options, &seed_out), 3 **Unlock**(id, options, &seed_out), 4 Release(id), 5 Release after a failed create/lookup setup (id).
  - Other selectors: 5 SetYCbCrMatrix, 6 WrapClientImage, 7 WrapClientMemory, 9 SetValue (serialized), 0xa UpdateNonBulkValueCache (struct in 9), 0xb RemoveValue, 0xc BindAccel, 0x11 SetSurfaceNotify (async), 0x12 RemoveSurfaceNotify, 0x13 Log, 0x14 SetPurgeable, 0x15 SetOwnership, 0x16 SetTiled, 0x18 SetTimestamp, 0x19 GetTileFormat, 0x1a CopyDataValueBytes, 0x1b SetBulkAttachments (struct 0x88), 0x1e/0x2e-0x31 (via outlined helpers), 0x1f SetCompressedTileDataRegionMemoryUsed, 0x20 GetGraphicsCommPageAddress, 0x21 SetIndexedTimestamp, 0x24-0x26/0x2d IOSurfaceAccelerator, 0x27-0x29 shared events, 0x2a SignalEvent, 0x2b Set/InitDetachModeCode, 0x2c SetOwnershipIdentity, 0x32-0x34 data properties.
  - => SWEET kernel service: class/name **IOCoreSurfaceRoot** + IOSurfaceRootUserClient; minimum = sel 13, 0, 4, 9/0xa/0xb (values), traps 0-5, 0x22/0x23 later for cross-process surfaces (CA sends surfaces to backboardd by mach port). Memory: IOBufferMemoryDescriptor per surface, mapped into each task with createMappingInTask; ids from a global table.

- **Image v8: daemon logs on the console.** `tools/patch-launchd-plist.py IN OUT LABEL...` rewrites launchd.plist (binary, plistlib): renames every `_PanicOnCrash` to `_PanicOnCrasX` and gives the listed jobs `StandardOutPath`/`StandardErrorPath` `/dev/console` (devfs console is 0622, writable by mobile) plus `OS_ACTIVITY_DT_MODE=YES` (os_log mirrored to stderr) and `CFLOG_FORCE_STDERR=1`. v8 = v7 + that plist for com.apple.backboardd and com.apple.SpringBoard, written through the mount (796310 bytes, root:80 0644), SHA256 in `ios16-root-20H392-v8.img.sha256`, `.simg` ready; boot with `shim/out/shim-boot-0045n.img`. Goal: see backboardd's uncaught exception text and the window server's display probing. ODDITY (unresolved): the v5 raw-image rename at offset 0x1e025f000 is present in the v5-v7 image bytes, but the plist read through a Linux mount of v7 still had the original `_PanicOnCrash` keys; filefrag shows the file as one extent. Never patch file contents through raw offsets again; write through the mount.
- **IOMobileFramebuffer.framework reversed (step 1 of the GUI plan).** `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image IOMobileFramebuffer`.
  - Display discovery (`IOMobileFramebufferCreateDisplayList` -> `getDisplayListNumber`): iterates children of `IODeviceTree:/arm-io`, counts nodes whose `device_type` is "display-subsystem" or "ext-display-subsystem" (or `compatible` "paravirtualizedgraphics,gpu"); then `iomfb_populate_display_infos` adds an IOServiceAddMatchingNotification(IOServiceFirstMatch, **IOServiceMatching("IOMobileFramebuffer")**) and runs the run loop up to 30 s until that many services matched. `iomfb_match_callback` reads service properties `dfr`, `AppleTV`, `external` (CFBoolean) and names displays (external ones "%s-%d").
  - `IOMobileFramebufferOpen(service, task, type, &fb)`: `__ioMobileFramebufferAlloc` (CFPreferences com.apple.iokit.IOMobileGraphicsFamily: canvas_width/height, override_display_width/height, override_panel_width/height, benchmark, enable_ktrace), `IOServiceOpen(service, task, type)` (GetMainDisplay passes type 0), `getEDTProperty` reads `canvas-width`/`canvas-height` from the service's IODeviceTree parent, then fills a table of `kern_*` function pointers.
  - User client selectors (`kern_*` -> IOConnectCall*): 3 _kern_GetLayerDefaultSurface[ScalarMethod_stub]; 4 _kern_SwapBegin[ScalarMethod_stub]; 5 _kern_SwapEnd[StructMethod_stub]; 6 _kern_SwapWaitWithTimeout[ScalarMethod_stub] _kern_SwapWait[ScalarMethod_stub]; 7 _kern_GetID[ScalarMethod_stub]; 8 _kern_GetDisplaySize[ScalarMethod_stub]; 10 _kern_SetTVOutMode[ScalarMethod_stub]; 11 _kern_SetWSSInfo[ScalarMethod_stub]; 12 _kern_RequestPowerChange[ScalarMethod_stub]; 13 _kern_EnableStatistics[ScalarMethod_stub]; 14 _kern_SetFlags[ScalarMethod_stub]; 15 _kern_SetDebugFlags[ScalarMethod_stub]; 16 _kern_SetTVOutSignalType[ScalarMethod_stub]; 17 _kern_SetGammaTable[StructMethod_stub]; 18 _IOMobileFramebufferIsMainDisplay[ScalarMethod_stub]; 19 _kern_SetWhiteOnBlackMode[ScalarMethod_stub]; 20 _kern_SwapSignal[ScalarMethod_stub]; 22 _kern_SetDisplayDevice[ScalarMethod_stub]; 23 _kern_SetDigitalOutMode[ScalarMethod_stub]; 24 _kern_GetHDCPDownstreamState[StructMethod_stub]; 25 _kern_GetDigitalOutState[ScalarMethod_stub]; 26 _kern_printDisplayRegs[ScalarMethod_stub]; 27 _kern_GetGammaTable[StructMethod_stub]; 28 _kern_GetDotPitch[ScalarMethod_stub]; 29 _kern_GetDisplayArea[StructMethod_stub]; 30 _kern_EnableDisableDithering[ScalarMethod_stub]; 31 _kern_SetUnderrunColor[ScalarMethod_stub]; 33 _kern_EnableDisableVideoPowerSavings[ScalarMethod_stub]; 34 _kern_SetVideoDACGain[ScalarMethod_stub]; 35 _kern_SetLine21Data[ScalarMethod_stub]; 41 _IOMobileFramebufferEnableMirroring[ScalarMethod_stub]; 42 _IOMobileFrameBufferGetMirroringCapability[StructMethod_stub]; 43 _IOMobileFramebufferSetRenderingAngle[StructMethod_stub]; 44 _IOMobileFramebufferSetMirrorContentRegion[StructMethod_stub]; 47 _kern_HDCPSendRequest[ScalarMethod_stub]; 48 _kern_HDCPGetReply[ScalarMethod_stub]; 49 _kern_SurfaceIsReplaceable[ScalarMethod_stub]; 50 _kern_SetBrightnessCorrection[ScalarMethod_stub]; 51 _kern_SetColorRemapMode[ScalarMethod_stub]; 52 _kern_SwapCancel[ScalarMethod_stub]; 53 _IOMobileFramebufferSetCanvasSize[ScalarMethod_stub]; 54 _IOMobileFramebufferGetMatrix[Method_stub]; 55 _IOMobileFramebufferSetMatrix[Method_stub]; 56 _IOMobileFramebufferKernelTests[StructMethod_stub]; 57 _kern_GetColorRemapMode[ScalarMethod_stub]; 66 _kern_SPLCSetBrightness[ScalarMethod_stub]; 67 _kern_SPLCGetBrightness[ScalarMethod_stub]; 68 _kern_SetParameter[Method_stub]; 69 _kern_SwapSetColorMatrix[StructMethod_stub]; 72 _kern_DisableNotifications[ScalarMethod_stub] _kern_EnableNotifications[ScalarMethod_stub]; 73 _kern_ChangeFrameInfo[ScalarMethod_stub]; 74 _kern_SupportedFrameInfo[Method_stub]; 75 _kern_FactoryPortal[StructMethod_stub]; 77 _kern_GetCurrentAbsoluteTime[ScalarMethod_stub]; 78 _kern_SetBlock[Method_stub]; 79 _kern_GetBlock[Method_stub]; 80 _kern_GetLinkQuality[ScalarMethod_stub]; 81 _kern_SwapCancelAll[ScalarMethod_stub]; 82 _kern_GetProtectionOptions[ScalarMethod_stub]; 83 _kern_CopyLayerDisplayedSurface[ScalarMethod_stub]; 84 _kern_SetContrast[StructMethod_stub]; 85 _kern_GetBufBlock[Method_stub]; 86 _IOMFBGainEncoderFinishEncoding[Method_stub]; UNKNOWN {}
  - => Kernel needs: an `/arm-io` child node with device_type "display-subsystem" (+ canvas-width/height) and an IOService of class **IOMobileFramebuffer** (subclass name match) attached under it, opened with type 0, implementing at least GetDisplaySize(8), IsMainDisplay(18), GetID(7), GetLayerDefaultSurface(3), SwapBegin(4)/SwapEnd(5 struct)/SwapWait(6), Enable/DisableNotifications(72), frame info(73/74), CopyLayerDisplayedSurface(83), plus IOSurface for the swapped buffers. NEXT: CoreAnimation's AppleDisplay/IOMFBDisplay usage of these (constructor, first swap, vsync), then IOSurface.framework's IOSurfaceRoot selectors.
- **GUI PLAN (decided 2026-10-16): CPU rendering + kernel IOMobileFramebuffer.** User: CPU rendering is fine for now (goal = prove the GUI runs), may later research an Apple-style GPU driver for the Adreno 618 -> keep display output and renderer separable. QuartzCore findings (symbols from the cache's .symbols subcache: `ipsw dyld symaddr research/dsc/dyld_shared_cache_arm64 --image QuartzCore`; strings: `ipsw dyld macho ... QuartzCore --strings`):
  - Renderers: `sw_new_context` (CA::OGL::SWContext, full CPU renderer incl. blur, images, IOSurface-backed surfaces, make_buffer_current(WindowServer::Surface)), `gles_new_context`, `metal_new_context`, `new_null_context`. Env knobs include CA_ENABLE_OGL, CA_DISPLAY_TYPE, CA_FORCE_LOCAL_SERVER, CA_FORCE_TIMER, CA_CANVAS_WIDTH/HEIGHT, CA_MAIN_DISPLAY_SCALE/ORIENTATION, CA_DISABLE_RENDER, CA_ALWAYS_RENDER (selection logic not traced yet).
  - `-[CAWindowServer _detectDisplays]` (0x1884e3150) iterates static tables `open_funcs`/`count_funcs` = AppleCLCDDisplay, AppleRGBOutDisplay, AppleWirelessDisplay only; each `count()` = `display_count_of_type(IOMFBDisplayType)` over **`IOMobileFramebufferCreateDisplayList()`**, `open(i)` = `create_display_of_type` -> `CA::WindowServer::AppleDisplay(CFString name, ..., IOMFBDisplayType)` (an IOMFBDisplay driven by IOMFBServer: vsync_callback, frame_info_callback, swaps). `CA::WindowServer::VirtualDisplay` exists but is never auto-detected (explicit API only). => the main display MUST come from an IOMobileFramebuffer kernel service.
  - NEXT: reverse IOMobileFramebuffer.framework: IOMobileFramebufferCreateDisplayList / IOMobileFramebufferOpen (service matching, display type property), the user-client selectors used by IOMFBServer (display size/modes, swap begin/set-layer/end with IOSurface ids, vsync notifications), then the IOSurface kernel side (IOSurfaceRoot user client: create/lookup/lock, memory mapping) that both IOMFB swaps and CA surfaces need. Kernel: SWEET IOMobileFramebuffer service that copies the swapped IOSurface to the 1080x2400 framebuffer at 0x9c000000.
- **logd fixed; backboardd = DISPLAY WALL (boot 0045n on v7, 21:08:57 UTC, frames VID_20261016_230850 00:55-01:28, slide 0x4c3ec000, `research/crash-0045n-v7.txt`).** No `CRASH logd` any more; new daemons run (runningboardd, WirelessRadioManagerd, networkserviceproxy, dasd, cloudpaird, magicswitchd, atc, askpermissiond, ManagedSettingsAgent, containermanagerd uses AKS 0/17). New: locationd sig 11 at CFRunLoopAddSource+132 (NULL source) from its main+0x2af138 in a dispatch_once. **backboardd** sig 6: abort <- std::terminate <- _objc_terminate <- dispatch_once <- main+0x9334 = the "start %{public}@..." wrapper (0x100009264) for **"window server"** (block 0x10000a770 -> dispatch_once body 0x10001d7f0 = StartWindowServer): MTLSetShaderCachePath, `[CAWindowServer serverWithOptions:@{kCAWindowServerDisableUpdatesOnMainDisplay: @YES}]`, `setRendererFlags:`, **`mainDisplay`** -> `displayId` -> `[CADisplay displayWithDisplayId:]`, setWindowServerDisplay:, bounds, pointScale, currentMode, preferredScale, nativeOrientation, touchScales... With no display, mainDisplay is nil and it throws. (HID system and GS start fine before it.) SpringBoard dies on the same missing display (FBSDisplayMonitor). QuartzCore display backends (from the cache's .symbols subcache, `ipsw dyld str`): `CA::WindowServer::AppleCLCDDisplay` (IOMobileFramebuffer hardware) and **`CA::WindowServer::VirtualDisplay`** (open(), new_server, clone_update). `CA_DISPLAY_TYPE` and `CA_FORCE_LOCAL_SERVER` strings exist in QuartzCore but have no direct xref (likely read via a table of CA_* env names). NEXT: find how CA::WindowServer::Server enumerates displays (IOMobileFramebuffer services vs VirtualDisplay / CA_DISPLAY_TYPE) and choose: (a) kernel IOMobileFramebuffer service + IOSurface, or (b) a VirtualDisplay rendered by CA's CPU path (CA::OGL::SW) and copied to the framebuffer.
- **watchdogd + CommCenter + identityservicesd fixed (boot 0045n on v6, 20:41:30 UTC, frames VID_20261016_224133 00:39-01:13, slide 0x20fec000).** `SWEET WDT: watchdogd sel 0 in 0/0 out 1/0 -> ok`, no watchdogd/CommCenter/identityservicesd crashes (CommCenter/identityservicesd now call AKS 0/17/7). usermanagerd boot task runs (UMD_INIT creates primary session uid 501 "mobile", personas 99 System and 199 Default registered with the kernel); `Failed to atomically swap writing file /private/var//keybags/usersession.kb: Operation not supported (45)` (HFS lacks the atomic swap rename; non-fatal so far). Remaining: SpringBoard (FBSDisplayMonitor, no display), backboardd (uncaught exception), mediaserverd, lockdownd (crash inside obfuscated code, main+0x4c1b4?), logd. **logd**: main+0x18160 = `BUG IN LIBTRACE: Failed to migrate directory` from 0x10001801c(dir 0): 0x100016538 requires the dir to exist with uid/gid/mode from the table at 0x10002df14 (0: /private/var/db/diagnostics 272:272 0751, 1: /private/var/db/uuidtext 272:272 0755, 2: /private/var/db/diagnostics/timesync 272:272 0755) plus a `.migrated` file, else XPC "operation 6" to a helper and crash. **Image v7** = v6 + those dirs/markers (also in mkiosroot.sh), SHA256 in `ios16-root-20H392-v7.img.sha256`, `.simg` ready. Boot with `shim/out/shim-boot-0045n.img`.
- **Exit-reason text works (boot 0044n, frames VID_20261016_221726 00:32-00:53, slide 0x22d5c000).** CommCenter/identityservicesd: `couldn't dlopen libobjc-trampolines.dylib: dlopen(/usr/lib/libobjc-trampolines.dylib, 0x0106): tried: '/usr/lib/libobjc-trampolines.dylib' (no such file, not in dyld cache)`: the file only exists in the OS cryptex and dyld does not search cryptexes at ignition_level=1. 19 cryptex files have no root counterpart (OS: DriverKit dyld cache + .symbols, VisualTestKit, libffi-trampolines, libobjc-trampolines, libstdc++ 6.0.9 + 2 symlinks; App: SafariSupport.bundle, AuthenticationServicesAgent, com.apple.Safari.History, passwordbreachd, safarifetcherd, webbookmarksd, webinspectord, webpushd) -> hard-linked (symlinks copied: Linux hfsplus cannot hard-link symlinks); `tools/mkiosroot.sh` does it generically. watchdogd still crashed: the `-wdt_no_pmu` / `/arm-io/wdt no-pmu` check (0x10000a01c) only runs when os_variant_has_internal_diagnostics; otherwise 0x100009b18 looks up IOServiceMatching("IOService") + IOPropertyMatch {IOPMUPrimary: 1} (NSConstantDictionary) and crashes if absent, then IORegistryEntrySetCFProperty(boot stage 0xff) (failure only logged). Patch **0045**: IOWatchdog sets IOPMUPrimary = 1 and accepts setProperties; CI `38961814194` -> `xnu/out-0045`. **Image v6** = v5 + the 19 cryptex links, SHA256 7c610c6a...297a, `ios16-root-20H392-v6.simg` (full flash needed). Boot image `shim/out/shim-boot-0045n.img` (0045 + sweet-0044hi.adt). Still open: SpringBoard (no display), backboardd (uncaught exception, reason none), mediaserverd (Fig NULL dict), logd (main+0x18160), lockdownd (main+0x4c1b4).
- **System survives daemon crashes (boot 0043p, video frames VID_20261016_215006 00:25/00:42/00:54).** With the v5 plist patch no panic: launchd keeps launching (runningboardd, powerd, tccd, healthd, peopled, cryptexd, routined, aksd, mediaremoted, familynotificationd, nanoprefsyncd, navd, cloudpaird, passd, amsaccountsd, accessoryupdaterd, wcd ...). Shared cache slide that boot 0x406b4000 (`research/crash-0043p.txt`). watchdogd still crashed at main+0xb82c from the PMU step: `-wdt_no_pmu` is only honored when os_variant_has_internal_diagnostics; customer builds read `no-pmu` from IODeviceTree:/arm-io/wdt (IORegistryEntrySearchCFProperty) -> mkadt adds /arm-io/wdt {no-pmu}. **cryptexd** sig 6: abort_with_payload <- os_crash_fmt <- `__darwin_arm_secure_boot_chip.cold.7` ("panic: failed to get crypto algorithm") <- `_img4_chip_select_personalized_ap`: reads /chosen use-ddi-secure-boot, allow-ecid-mismatch, crypto-hash-method ("sha1" | "sha2-384"), /chosen/asmb lp-smb0/1 -> mkadt adds crypto-hash-method "sha2-384". **identityservicesd** sig 6 = same `_objc_fatal` in imp_implementationWithBlock as CommCenter (block trampolines; message needed). lockdownd sig 5 at main+0x4c1b4. Patch **0044**: crash report adds `CRASH name reason ns N code X: text` (exit reason description = abort_with_payload text). CI `38959096811` -> `xnu/out-0044`, QEMU OK. Image `shim/out/shim-boot-0044n.img` = 0044 + `shim/out/sweet-0044hi.adt` (wdt no-pmu, crypto-hash-method) + cmdline (wdt=-1, no -wdt_no_pmu).
- **First symbolicated daemon crashes (boot 0043u on journaled v4, 19:38:53 UTC; video frame chat image 36; transcribed in `research/crash-0043u.txt`; shared cache slide 0x40d60000 for every process).** (Gemini's video transcription invented values, use frames only.) `tools/sweet-crash.py research/dsc/dyld_shared_cache_arm64 x research/crash-0043u.txt`:
  - **watchdogd** pc main+0xb82c (`_os_crash` trap helper) from 0x100009bb0 = set PMU boot stage via IORegistry (no PMU) -> fix: boot-args `wdt=-1 -wdt_no_pmu` (Apple's own test mode writes "%s wdt=-1 -wdt_no_pmu"; watchdogd logs "skipping setting PMU boot stage because -wdt_no_pmu found in boot-args or no-pmu found in EDT"). Kernel effect of wdt=-1: sched hygiene debug off, zone_exhausted_timeout -1 (harmless).
  - **SpringBoard** sig 5 in `-[FBSDisplayMonitor _initWithBookendObserver:transformer:]+1160` <- `+[FBDisplayManager sharedInstance]` <- `FBSystemShellInitialize` <- `SBSystemAppMain`: no main display. GUI WALL: display service (IOMobileFramebuffer / CoreAnimation display).
  - **backboardd** sig 6: abort <- std::terminate <- _objc_terminate (uncaught exception; message not shown).
  - **CommCenter** sig 6: `_objc_fatal` in `imp_implementationWithBlock` (from `+[_PFRoutines initialize]`, CoreData): objc block trampolines cannot be allocated -> likely kernel gap (trampoline page remap); will hit many processes.
  - **mediaserverd** sig 11: CFDictionaryGetValue(NULL) in FigNotificationListenerStartNotifications (routing session manager).
  - **logd** sig 5 at its main+0x18160 (bt main+0x9dfc); lockdownd sig 5 (not yet symbolicated).
  - Image v5 = v4 + launchd.plist (`/System/Library/xpc/launchd.plist`, contiguous at image offset 0x1e025f000, 1456980 bytes) with the 7 `_PanicOnCrash` keys renamed `_PanicOnCrasX` in place (raw image patch, no metadata change) -> `diff-v4-v5.simg` = 7 blocks; v5 SHA256 78f96974...185a. Boot image `shim/out/shim-boot-0043p.img` = 0043 + `wdt=-1 -wdt_no_pmu`.
- **0043 console crash reports (QEMU verified); image `shim/out/shim-boot-0043u.img`; NEXT: flash v4 + boot 0043u.** Boot 0042u (video photo IMG_20261016_211646): short exec lines work; watchdogd crashes with NO `SWEET WDT:` line (fails before its first IOWatchdog call: lookup or IOServiceOpen, or elsewhere); lockdownd, SpringBoard, mediaserverd, CommCenter, identityservicesd, backboardd, watchdogd all crash repeatedly ("Too many corpses being created" = corpse limit, no crash reports). AKS callers: lockdownd (0, 7), imagent/sleepd (0, 17, 7), backboardd (0, 17), UserEventAgent (0, 7, 102, 103 -> unsupported). Patch **0043**: `sweet_crash_log` (osfmk/kern/exception.c, called from proc_prepareexit for crash exits on the current proc) prints `CRASH name[pid] sig S code (exc<<32|code) sub X slide SR mh MH`, `CRASH name pc lr sp fp far`, `CRASH name bt` (10 fp frames); AKS sel 103 notify_state_is_set -> 0. CI `38954520419` -> `xnu/out-0043`. QEMU test: init forks, child `brk #1`: `CRASH launchd[2] sig 5 code 0x600000001 sub 0x1000004f0 slide 0x0`, pc correct, parent keeps running (pid 1 crashes panic before proc_prepareexit, so test with a child). `tools/sweet-crash.py CACHE ROOT [report]` symbolicates typed-in CRASH lines (`ipsw dyld a2s` with addr - slide; main binary offsets = addr - mh + 0x100000000).
- **v3 reflashed 18:50-18:55 UTC (`research/flash-userdata-v3b.log`, 24/24 OKAY); 0042u booted 19:01:17 UTC on the clean disk (`research/boot0042u-2.log`), SLOW MO VID pending (watchdogd failure reason).** ABL hangs on the first `fastboot boot` after every big flash; user re-enters fastboot. User gave standing approval to reflash/boot without asking (memory standing-flash-approval). Commits now end with `Co-Authored-By: dipa-studio <183933817+dipa-studio@users.noreply.github.com>` (user request; never a Claude trailer).
  - watchdogd flow: connect_to_kext (0x100005408): IOServiceGetMatchingService("IOWatchdog") fails -> "failed to discover" + _os_crash; IOServiceOpen(type 1) fails -> "IOServiceOpen failed with error : 0x%x" + _os_crash. Then sel 0 (out 1 scalar): 0 -> "userspace monitoring disabled", 0x100009bb0, sleep 2, exit(0); nonzero -> "userspace monitoring enabled", normal operation.
  - **Image v4 (JOURNALED):** `tools/mkiosroot.sh` now does `mkfs.hfsplus -J`, mounts with `-o loop,force`, adds the /System/Library/Caches/com.apple.dyld hard links (44) and /private/var/keybags/systembag.kb (0700/0600 root). Built from the IPSW dmgs (OS 087-86698-044, SystemOS 087-86593-047, AppOS 087-86715-047) -> `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v4.img` SHA256 fba4aeae...ec0f9 + `.simg`. Header: attr 0x80002100 (unmounted, journaled), journal info block 129, journal 8 MiB at 532480 flagged need-init. Linux `fsck.hfsplus -n` reports "Volume header needs minor repair" on any fresh journaled volume even after -y (quirk). QEMU: 64 MB journaled test root (`rd=md0 rootrw=1`, 0042 kernel): `hfs: Initializing the journal (joffset 0x3000 sz 0x80000)` -> mounted -> init runs, no panic. NEXT: flash v4 (full), boot 0042u.
- **SPRINGBOARD STARTS (boot 0041u 18:39:53 UTC, photo IMG_20261016_204142).** backboardd, bluetoothd, fairplayd.H2, SpringBoard (pid 111, crashed: "Too many corpses"), xpcproxy run; `SWEET AKS: backboardd sel 0 -> 0`, `sel 17 in 1/0 out 0/4096 -> 0`. Panic: watchdogd[113] exited, namespace 2 subcode 5 (SIGTRAP = its _os_crash): watchdogd crashes on purpose when IOServiceGetMatchingService("IOWatchdog") fails ("connect_to_kext() unexpectedly failed") or IOServiceOpen(type 1) fails ("IOServiceOpen failed with error"); IOWatchdog DOES register (QEMU msgbuf: `SWEET WDT: IOWatchdog registered`), cause not on screen yet -> need video. Note `wdt_test=no_user_checkin` makes watchdogd log "detected testing boot-args to not run, exiting" (path not reached here?). **HFS CORRUPTION:** `hfs_swap_BTNode: offset #0 invalid (0xBC1D) (blockSize 0x2000 numRecords 81)`, `node=19677 fileID=4` (catalog), `hfs_mark_inconsistent` repeated. Likely cause: non-journaled HFS + unclean panics while writing (0038e wrote a 2.7 GB core then panicked; every boot since ends in panic). Plan: reflash v3 (clean), longer term HFS journaling. Patch **0042**: one short `exec NAME` console line instead of the 3-line "Allowing spawn of iOS binary" notice; CI `38949451276` -> `xnu/out-0042`; image `shim/out/shim-boot-0042u.img` (same cmdline as 0041u).
- **LAUNCHD DAEMONS RUN (boot 0039u, 18:29:13 UTC, photo IMG_20261016_203052).** With `launchd_unsecure_cache=1` all boot tasks pass and launchd starts LaunchDaemons (pids > 100: identityservicesd 114 and lockdownd 106 crash, "Too many corpses being created"). Fatal: `watchdogd: ERROR: failed to discover watchdog KEXT service` -> exit (namespace 2 = signal, subcode 5) -> `_PanicOnCrash` panic. watchdogd: IOServiceMatching("IOWatchdog"), IOServiceOpen type 1, IOConnectCallScalarMethod sel 0/1 (check in)/3/4 (disable/enable userspace monitoring)/5, IOConnectCallStructMethod sel 2 (1 KiB in) and 9 (small out); VM path ("detected virtual machine environment and no watchdog KEXT found, exiting...") only when it detects a VM. Console also flooded with `hfs: set hardlink bit on vol=iOSRoot cnid=321318` (Linux-made hard links lack kHFSHasLinkChainBit; repaired only in memory on each lookup). Patches **0040** (`iokit/Kernel/arm/SweetWatchdog.cpp`: IOWatchdog + IOWatchdogUserClient, all selectors succeed with zeroed outputs, each logged once as `SWEET WDT: ...`) and **0041** (sweet_hfs hfs_catalog.c: the three link-repair printfs limited to 8 per boot); CI `38948245372` PASSED -> `xnu/out-0041` (QEMU regression OK). Image `shim/out/shim-boot-0041u.img` (0041 + sweet-0038hi.adt + ufsrw rootrw + launchd_unsecure_cache=1) booted 18:39:53 UTC (`research/boot0041u.log`), photo pending.
- **v3 FLASHED + keybag passes; next wall AMFI (launchd_cache_loader).** User said "flash, nothing to lose": `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg` 17:51:52-17:57:01 UTC, 24/24 chunks OKAY (`research/flash-userdata-v3.log`). userdata = v3 (SHA256 fa84274c...22df) until the next rw boot. ABL fastboot then hung ("Sending" forever, `reboot bootloader` timed out) until the user re-entered fastboot by hand (common Xiaomi ABL crash). Boot 0038e 18:06:15 UTC (`research/boot0038e-3.log`), photos IMG_20261016_200812/200838: keybag OK, then boot tasks tzinit (`Bad zoneinfo link`, resets to system partition, OK), finish-restore, finish-demo-restore, sysstatuscheck, prng_seedctl (`failed to load kernel prng seed`, `failed to load virtual random (-147)`, AllowCrash), auearlyboot, then **launchd_cache_loader: `abort: Unable to find AMFI`** -> 2.7 GB core written to /cores in 91 s -> launchd panic `launchd_cache_loader[22] exited -- exit reason namespace 7 subcode 0x1`. launchd_cache_loader: SecStaticCodeCheckValidity of /System/Library/xpc/launchd.plist with detached .sig, then IOServiceMatching("AppleMobileFileIntegrity") + IOServiceOpen type 0 + IOConnectCallMethod sel 6 (1 scalar = 1, struct in = cdhash) = trust the cdhash, then sends the cache to launchd. Boot-arg `launchd_unsecure_cache=1` skips signature + AMFI ("Using unsecure cache"); the value is parsed with strtoul base 10 (helper 0x100002da8), so a path = 0 = off: boot 0039w (18:17:13 UTC, `=/System/Library/xpc/launchd.plist`, photo IMG_20261016_202008) still aborted `Unable to find AMFI` (core dump now skipped: `Failed to generate core file ... error 14`, so 0039 works). Image `shim/out/shim-boot-0039u.img` uses `launchd_unsecure_cache=1`. Patch **0039**: do_coredump = 0 on SWEET (kern.coredump sysctl still works); CI `38945267341` -> `xnu/out-0039` (_do_coredump now in __common). Image `shim/out/shim-boot-0039w.img` = 0039 + sweet-0038hi.adt + ufsrw rootrw + `launchd_unsecure_cache=/System/Library/xpc/launchd.plist`. TODO later: real AppleMobileFileIntegrity IOService (sel 6 trust cdhash etc.).
- **Image v3 ready, awaiting user "flash".** Boot 0038w 17:38:10 UTC, photo (chat image 30): `SWEET AKS: keybagd sel 0 -> 0x0`, `sel 14 out 1/0 -> 0x0` (x2), `MKB_INIT: mount is with NO CPROTECT ... does not support Data Protection`, `System Keybag loaded`; then keybagd still opens /private/var/keybags/systembag.kb (0x100012d3c, for BackupKeyBagKeys) -> ENOENT, `no-effaceable-storage` not set -> `Can't load the keybag. tears in rain... Time to die` -> `FATAL KEYBAG ERROR: kb_load` -> reboot -> Halt/Restart Timed Out panic. Fix: ADT `/defaults/no-effaceable-storage` (mkadt.py; `shim/out/sweet-0038hi.adt`, `research/q0038-hi.adt`, QEMU OK) + file `/private/var/keybags/systembag.kb` (0600 root, dir 0700; XML plist {KeyBagKeys: data}). **v3 image** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392-v3.img` = v2 + that file, fsck OK, SHA256 fa84274c...22df; `ios16-root-20H392-v3.simg` (img2simg: zero blocks become FILL chunks, so a full flash overwrites every block the rw boots changed). Flash: `fastboot -S 512M flash userdata ios16-root-20H392-v3.simg`, then boot `shim/out/shim-boot-0038e.img` (0038 + sweet-0038hi.adt + ufsrw=1 rootrw=1).
- **0038 AppleKeyStore (CI 38938744130 PASSED -> `xnu/out-0038`; QEMU msgbuf: `SWEET AKS: AppleKeyStore registered (no passcode, unlocked)`; phone image `shim/out/shim-boot-0038w.img` booted 17:38:10 UTC, `research/boot0038w.log`, photo pending).** QEMU full kernel log trick (fb.txt is only the last screen): `llvm-nm KERNEL | grep _msgbufp` -> `--hmp "x /1gx ADDR"` gives struct msgbuf address (static, 0xfffffe0007b56678 on 0038) -> `--hmp "x /3gx STRUCT"` gives bufc (3rd quad) -> `--hmp "memsave BUFC 0x20000 \"FILE\""` (quote the file name), `tr -d "\0" < FILE`. Same inputs give the same addresses. Boot 0037w 17:08:35 UTC, photo IMG_20261016_191052: bindfs fixed mount; mount-phase-1/2 pass; `cc_fips_test` boot task: all corecrypto FIPS POST tests PASSED in userspace; then keybag boot task `keybagd --init`: `MKB_INIT: FATAL KEYBAG ERROR: failed to load system bag`, `Could not get options entry from the device tree` (x2, IODeviceTree:/options = NVRAM, non-fatal), `REBOOTING INTO RECOVERY MODE` -> reboot -> panic `Halt/Restart Timed Out @IOPlatformExpert.cpp:884` (no restart path on SWEET).
  - keybagd (static libaks): load_devicebag (0x100012c30) calls aks_get_system (sel 14, 0-1 scalar in, 1 out) and loads /private/var/keybags/systembag.kb only if the result is 0xe00002f0 (NotFound); any other error -> fatal; SUCCESS -> skip the file (userspace-reboot path). systembag.kb is a plist {KeyBagKeys}; decrypted with effaceable storage unless IODeviceTree:/defaults has `no-effaceable-storage`. Image has no /private/var/keybags. has_data_protection: statfs of /private/var; no cprotect on our HFS -> device-bag volume mapping skipped.
  - libaks connection: IORegistryEntryFromPath / IOServiceMatching("AppleKeyStore"), IOServiceOpen type 0, then selector 0 (no args) must succeed.
  - **AppleKeyStore selector map (iOS 16.7 AppleKeyStore.framework, via `ipsw dyld disass`):** 0 open, 2 create_bag, 3 save_bag, 4 unload_bag, 5 set_system_with_passcode, 6 load_bag, 7 get_lock_state (1 in, 1 out; bit 2 = unlocked since boot), 9 unlock_device, 10 wrap_key, 11 unwrap_key, 12 unlock_bag/test_stashed_kek, 13 lock_bag, 14 get_system, 15 change_secret_se, 16 internal_state, 17 get_device_state (1 in, struct out <=4K: DER SET of SEQUENCE{UTF8 key, INTEGER}: ss state, sls lock_state (MKBGetDeviceLockState returns it), sb backoff, sbo, sfa failed attempts, sfao, sgs generation, sas assertions, sgpe grace, srcd countdown, sr reserved), 18 recover_with_escrow_bag, 19 obliterate_class_d, 20 drain_backup_keys, 21/22 set/clear_backup_bag, 23 get_bag_uuid, 24 rewrap_key_for_backup, 26/27 assert_hold/drop, 30/31 set/get_configuration, 33-37 stash, 38 auth_token_create, 40 generation, 41 fdr_hmac_data, 42 verify_password, 43 _aks_operation, 44 remote_session, 49/50 signing keys, 51/53/54 stash enable/persist/escrow, 55 unload_session_bags, 57/58 remote peer, 59-62 smartcard, 63 migrate_s_key, 65 set_keybag_for_volume_with_cookie_persona, 66/67 sync bags, 68 copy_volume_cookie_persona, 69-73 se_*, 74-79/84/85/99 fv_* (FileVault/VEK), 80/81 absinthe, 82 make_public_backup_bag, 83 drop_auxiliary_auth, 86 kext get/set options, 87 invalidate_bag, 88-91/94/95/106/107 se_*, 92 lower_iteration_count, 93 get_internal_info, 96-98/117 keybag_persona create/list/delete, 100/101 assert promote/consume, 102/103 notify_state set/is_set, 104 fairplay, 105 change_secret_epilogue, 108 delete_xart_leak, 110-113 backup volume, 114 sealed_hashes_set, 115 prewarm_sps, 118-128 AKSIdentity*/AKSGetLastUser.
  - Patch **0038**: `iokit/Kernel/arm/SweetKeyStore.cpp` (class AppleKeyStore on IOResources, IOUserClientClass AppleKeyStoreUserClient; personality in KernelConfigTables.cpp): 0/4/5/9/12/13/26/27/55/102 success, 14 -> handle 0, 7 -> 0x4, 17 -> DER state (ss 4, sls 0), others kIOReturnUnsupported; logs `SWEET AKS: <proc> sel N arg0 in a/b out c/d -> ret` for every call.
  - Tools: shared cache copied to `research/dsc/` (git-ignored; ipsw needs a writable dir for its .a2s symbol cache); `ipsw dyld disass research/dsc/dyld_shared_cache_arm64 --image AppleKeyStore|MobileKeyBag`; scratchpad `annot2.py BIN DIS FIXUPS` annotates llvm-objdump output with strings and import names (`ipsw macho info --fixups`).
- **0037 bindfs (phone boot 0037w pending photo).** Boot 0036mw 16:57:47 UTC, photo IMG_20261016_190102: WRITABLE ROOT WORKS: `/dev/ufsroot0 on / (hfs, local, noatime)` after mount_hfs update (GetMasterBlock EBUSY harmless), coredump of mount written to /cores (rw). Then `mount: failed to mount /private/preboot/5CBE3601.../usr/standalone/firmware -> ...: Operation not supported by device (19)` -> exit 74 -> launchd panic `mount[2] exited`. Cause: the macOS-derived config had nullfs but no bindfs (ENODEV = unknown fs type). Caller passes env 0 -> bind not required, ENOENT (missing source dir) tolerated. Patch **0037** adds `bindfs` to FILESYS_BASE in MASTER.arm64.sweet; CI `38936550483` -> `xnu/out-0037` (bindfs_vfsops present; QEMU probe regression OK). Image `shim/out/shim-boot-0037w.img` (0037 + sweet-0036hi.adt + ufsrw=1 rootrw=1) booted 17:08:35 UTC (`research/boot0037w.log`). NOTE: userdata has now been modified by rw boots; it no longer equals the v2 image, so sparsediff with v2 as OLD is not safe any more (full reflash or a new baseline needed).
- **0036 phone: launchd boot tasks run; mount -P 1 needs /chosen/boot-manifest-hash.** Boot 0036hr 16:15:32 UTC, photo IMG_20261016_185236: platform check passes; fsck boot task runs (`fsck: not booting main or diagnostic OS. Skipping fsck on OS container`); mount-phase-1: `failed to get filesystem info` x2 (no IODeviceTree:/filesystems/fstab, non-fatal), `mount: data volume missing, but not required in env: 0`, mount_hfs update of /: `GetMasterBlock: Error 16 opening /dev/ufsroot0` (EBUSY, mounted block dev, non-fatal) then mount() EROFS (read-only boot) -> `mount: / failed with 1`; then `failed to get boot-manifest-hash` -> errx exit 66 -> launchd panic `mount[3] exited`. /sbin/mount: fn 0x100005f90 reads IODeviceTree:/chosen boot-manifest-hash (hex), bindfs-mounts /private/preboot/<HEX>/usr/standalone/firmware (ENOENT tolerated unless required). `tools/mkadt.py` now adds `boot-manifest-hash` = SHA-384("sweet boot manifest") (5CBE3601...5205). ADTs `shim/out/sweet-0036hi.adt`, `research/q0036-hi.adt` (QEMU probe OK, csops 0x26000001). Image `shim/out/shim-boot-0036mw.img` (0036 + new ADT + ufsrw=1 rootrw=1), booted 16:57:47 UTC (`research/boot0036mw.log`): FIRST WRITABLE BOOT of userdata (restore source: v2 image on SSD).
- **0036 CS_SIGNED (phone boot 0036hr pending photo).** Phone boot 0035hr 2026-10-16 15:57:02 UTC (`research/boot0035hr.log`, photo IMG_20261016_180249): highmem works on hardware; shared cache maps (trust-cache warnings only), Apple launchd runs (`Darwin Bootstrapper Version 7.0.0`, `entering ondemand mode`), starts boot task fsck, then userspace panic `boot task is not a platform binary (fsck, /sbin/fsck)`. launchd+0x3fea0: `csops(pid, CS_OPS_STATUS)` must have bit 0x04000000. Cause: nothing set CS_SIGNED (AMFI does it in vnode_check_signature), so csproc_get_blob() returns NULL for every process and csops never reports CS_PLATFORM_BINARY (also breaks per-process cdhash/entitlement queries). QEMU probe init (`csops` status printer, scratchpad csq/) on 0035: `0x02000001`; patch **0036** (`*cs_flags |= CS_SIGNED` in the SWEET AMFI hook), CI `38929635791` -> `xnu/out-0036`: `0x26000001`. Images `shim/out/shim-boot-0036hr.img` / `-0036hw.img` (same cmdlines as 0035). 0036hr booted 16:15:32 UTC (`research/boot0036hr.log`). Next launchd boot tasks (embedded __config plist): fsck -qL and mount -P 1/2 (RequireSuccess); no /etc/fstab on the image.
- **0035 ENTITLEMENTS + PLATFORM BINARIES (QEMU verified).** `xnu/patches/0035-sweet-amfi-entitlements-platform-binaries.patch`: new `iokit/Kernel/arm/SweetEntitlements.cpp` (OSObject subclass: OSDictionary from OSUnserializeXML of the signature's XML entitlements + original XML for CS_OPS_ENTITLEMENTS_BLOB); `bsd/kern/sweet_amfi.c` answers queryEntitlementBoolean/String(+WithProc, string also matches array members), copyEntitlementAsOSObject(+WithProc, retained), asdict (retained), get_xml (kalloc_data copy); built-in MAC policy "SWEET AMFI" (registered from bsd_init before vfs/exec) with mpo_vnode_check_signature: every signed binary on the MNT_ROOTFS mount gets CS_PLATFORM_BINARY (stand-in for AMFI's static trust cache: iOS system binaries are ad-hoc, cd_flags 0x2, platform byte 0), and attaches entitlements ONLY for the writable copy (cs_blob != csb_ro_addr; revalidation passes the RO blob). LESSON: first version attached in adjustContextWithoutMonitor -> QEMU `unable to adjust OSEntitlements context without monitor: 53` because ubc_cs_convert_to_multilevel_hash (4K-page signatures on 16K kernel) sets csb_entitlements_blob = NULL; ALL iOS 16 binaries (launchd, backboardd, SpringBoard) use 4K code pages, so this would have broken launchd on the phone. Boot-arg `sweet_amfi_debug=1` logs `SWEET AMFI: <ident>: N entitlements (test: ...)`. `tools/mkinit.py OBJ OUT [ENTS.plist]` adds an XML entitlements blob (special slot -5; default output byte-identical). QEMU `research/q0035-ent` (RAM disk `research/root-hfs-ent.img`, init with 3 test entitlements, highmem): `org.sweet.init: 3 entitlements (test: bool 1 string 1 array 1)` then init PID 1. MAC policies loaded: 0034 = 1, 0035 = 2 (QMP `mac_policy_list`). CI `38909807230` -> `xnu/out-0035`. Phone images: `shim/out/shim-boot-0035hr.img` (highmem, ro), `-0035hw.img` (highmem, +ufsrw=1 rootrw=1), `-0035r.img` (low mem fallback).
- **PHONE TEST ORDER (updated):** 0035hr -> if instant reset, 0035r -> then 0035hw.

- **HIGHMEM: XNU in the upper DDR bank, ~3.95 GiB (was 1.2 GiB).** Live FDT memory = <0x80000000 2G> + <0x1_00000000 0xfcc00000>; all fixed reserved-memory carve-outs are in the low bank (highest: ramdump_fb 0xaf000000, rmtfs ~0xfde01000), dynamic pools have alloc-ranges <= 0xffffffff, UFS node has no `iommus` (Linux DMAs anywhere). `tools/mkadt.py --highmem` sets /chosen dram-base 0x100000000 dram-size 0xfcc00000; `tools/mkpayload.py` now takes phys_base/mem_size from the ADT (default payloads byte-identical, verified); `tools/qemu-sweet.py` sizes -m from the payload (8G for highmem). Patch **0034** (`0034-sweet-ufs-dma-above-4g.patch`): UFS refuses DMA memory above 4G without UFSHCI CAP.64AS (bit 24), logs `DMA at 0x...`. CI `38905889883` success -> `xnu/out-0034`. **QEMU verified** (`research/q0034-hi`, ADT `research/q0034-hi.adt` --qemu --highmem, HFS RAM disk): phys_base 0x100000000, init PID 1 heartbeat, no panic; `max_mem` = `mem_size` = 0xfcc00000 read via QMP (`research/q0034-hi-mem`). Phone images: `shim/out/shim-boot-0034hr.img` (read-only) / `-0034hw.img` (+ufsrw=1 rootrw=1), ADT `shim/out/sweet-0034hi.adt` (asmb SIP + sweet-ufs + highmem). PHONE RISK: unknown runtime TZ/XPU protection in the upper bank would show as an instant reset; fall back to 0033r/w. Watchdog ruled out for the overnight reset: msm-watchdog bark is 20 s (qcom,bark-time 0x4e20) yet panic screens stay up for many minutes.

- **Offline research 2026-10-16 (user away, phone unavailable). Images rebuilt** `shim/out/shim-boot-0033r.img` / `-0033w.img` now also carry `wdt_test=no_user_checkin`. NEXT ON PHONE: boot 0033r (expect past in6_nigroup), then 0033w (first writes: rw root fixes HFS link-chain bits itself and gives /var for launchd sockets /var/run/syslog, /var/run/lockdown.sock).
- **launchd.plist** (`/System/Library/xpc/launchd.plist`, compiled; 532 daemons, 66 RunAtLoad/KeepAlive, list in scratchpad `early-daemons.txt`). `_PanicOnCrash` daemons: containermanagerd/usermanagerd (InternalOnly), lockdownd/remoted/trustd/remotepairingdeviced (AutomationOnly), **watchdogd unconditional** (KeepAlive SuccessfulExit=false). watchdogd needs IOKit `IOWatchdog` kext service; if absent it exits only when `kern.hv_vmm_present` (ADT `/defaults/vmm-present`, hvg_sysctl.c) or with boot-arg `wdt_test=no_user_checkin` ("detected testing boot-args to not run, exiting"; reads kern.bootargs). Using the boot-arg (vmm-present would change many daemons; keep as an option).
- **GUI path research (QuartzCore in the shared cache, `ipsw dyld str CACHE STR`, ~10 s/search):** CA::WindowServer has IOMFBServer/IOMFBDisplay (Apple DCP/IOMobileFramebuffer), AppleCLCDDisplay, AppleRGBOutDisplay, **VirtualServer/VirtualDisplay** and **MemorySurface**, EAGLServer. Renderers: CA::OGL::MetalContext, GLContext and a **CPU software rasterizer CA::OGL::SW** (samplers/blend modes; "image is too large for software renderer"). Env knobs: `CA_ENABLE_OGL`, `CA_DISPLAY_TYPE`, `CA_FORCE_LOCAL_SERVER` (249 CA_* vars). Hypothesis (unverified): backboardd's render server could run a VirtualServer/MemorySurface with the SW renderer and we copy the surface to the ABL framebuffer -> needs disassembly of CA::WindowServer server creation. Expected other GUI walls: IOSurface (closed-source kext; needs a reimplementation), IOMobileFramebuffer user client, IOHID touch events, AppleKeyStore/keybag (SEP) for lock state, MobileGestalt answers (AppleCLCD etc.).

- **0032r RESULT (boot 05:07:50 UTC, `research/boot0032r.log`, photo IMG_20261016_071200): SHARED CACHE MAPPED, LAUNCHD RUNS.** With SIP relaxed (ADT asmb) the `not in trust cache` lines are only warnings for every subcache (.31 ... .42.dyldlinkedit); no SIP rejection; libSystem loads; launchd configures networking (`skip attaching fsw to lo0 using legacy TX model`) -> kernel data abort far 0x28 in `SHA1Init` (symbolized as sha1_init) from `in6_nigroup` (IPv6 on lo0): g_crypto_funcs NULL. Kernel addresses are unslid: `~/swift/usr/bin/llvm-symbolizer --obj=KERNEL ADDR` works directly.
- **0032** BearSSL SHA-1 (`0032-sweet-bearssl-sha1.patch`), **0033** BearSSL SHA-384/512 (`0033-sweet-bearssl-sha384-sha512.patch`, BearSSL ctx stored in SHA512_CTX, static-asserted to fit; ubc_subr.c uses SHA-384 for code directories). `0020-stage-bearssl.sh` now also stages hash/sha1.c, hash/sha2big.c, codec/{dec,enc}{32,64}be.c. CI `38854909053` success (0032-only run `38854802073` superseded). Kernel `xnu/out-0033` (SHA1Init -> _br_sha1_init verified by disassembly; nm symbols have a leading underscore). Images (ADT sweet-0032): `shim/out/shim-boot-0033r.img` (read-only), `shim-boot-0033w.img` (+ufsrw=1 rootrw=1). Still NULL g_crypto_funcs users: des, chacha20poly1305, rsa, aesxts, rand, flow_divert.
- `research/check-patch-order.py` now skips patches touching CI-staged sweet_hfs sources (0031) instead of stopping.

- **0031r RESULT (boot 05:03:52 UTC 2026-10-16, `research/boot0031r.log`, photo IMG_20261016_070508): SHARED CACHE FOUND.** dyld now opens `dyld_shared_cache_arm64` (v2 image hard links), kernel refuses to map it: `shared_region: ... map(...'dyld_shared_cache_arm64'): not in trust cache` -> `vnode is not SIP-protected` (vm_unix.c: macOS arm64 path needs trust cache, else root-owned + SF_RESTRICTED unless CSR_ALLOW_UNRESTRICTED_FS) -> `dyld cache '(null)' not loaded: syscall to map cache into shared region failed` -> libSystem not loaded -> coredump to /cores fails error 30 (EROFS) -> panic initproc failed -> "MACH Reboot" (spins; screen kept). Lots of `hfs: set hardlink bit on vol=iOSRoot cnid=... linkid=...` spam (Linux-made hard links lack the link-chain bit; read-only mount cannot persist the fix). FIX: ADT `/chosen/asmb` with `lp-sip0`=0x6f (u64; incl. CSR_ALLOW_UNRESTRICTED_FS) and `lp-sip1`=1 (unauthenticated root), `tools/mkadt.py` -> `shim/out/sweet-0032.adt`. Images with kernel 0031: `shim/out/shim-boot-0032r.img` (read-only) and `shim-boot-0032w.img` (+ufsrw=1 rootrw=1).

- **2026-10-16 morning:** userdata now = **v2** image (`diff-v1-v2.simg` flashed 21:06:50 UTC 2026-10-15, OKAY, `research/flash-userdata-diff-v2.log`); future diffs use `ios16-root-20H392-v2.img` as OLD. Booted `shim-boot-0029k.img` (ignition_level=1) right after (`research/boot0029k-v2.log`); **no photo** (user asleep). Next morning the phone was in PixelOS recovery = some hardware reset (ABL then booted Android, which cannot use userdata). OBSERVATION: our kernel cannot reset the SoC itself (`PE_halt_restart` is never set; reboot/halt print "MACH Reboot"/"CPU halted" and spin), so the reset came from outside XNU: Qualcomm watchdog or a TZ/XPU violation. Unknown which; re-boot 0029k and watch/video until the reset. Do NOT tap factory reset/format data in recovery (would wipe the iOS image).
- **0030** (`xnu/patches/0030-sweet-ufs-writes.patch`, CI `38852655542`): UFS WRITE(10) + read-modify-write for partial 4 KiB blocks + SYNCHRONIZE CACHE (DKIOCSYNCHRONIZE), only with boot-arg `ufsrw=1`; `ufs_write_blocks` re-checks partition bounds before every write (only place data goes out).
- **0031** (`xnu/patches/0031-sweet-read-write-root.patch`, CI `38852837176`): boot-arg `rootrw=1` clears MNT_RDONLY before the root mount (no data volume on sweet: /private/var is on the root; image has no /etc/fstab); Apple HFS accepts a dirty non-journaled ROOT read-write on SWEET (logs "mounting dirty non-journaled root read-write"). Later: journaled HFS for crash safety. Kernel `xnu/out-0031` (CI `38852837176` success, 5m31s; 0030 run cancelled by the newer push). Boot images (phone ADT `sweet-0028.adt`, ramdisk byte-matched): `shim/out/shim-boot-0031r.img` = 0029k args (read-only, ignition_level=1) and `shim/out/shim-boot-0031w.img` = same + `ufsrw=1 rootrw=1`. PLAN: boot 0031r first and film until the reset (diagnose overnight reset), then 0031w (first ever writes to userdata; v2 image on the SSD is the restore source). `research/check-patch-order.py` cannot check 0031 (staged sweet_hfs files are not in its index); CI stage scripts run first, so CI is the check.

- **ignition_level=1 result** (boot 21:01:39 UTC, `research/boot0029k.log`, photo IMG_20261015_230308): preboot/cryptex stages skipped (need >= 2/3), `dylib_cache: finding shared cache on system volume: ignition level = 1, search root fd = 4, subpath = System/Library/Caches/com.apple.dyld/` -> not found -> `ignition boot failed: 19` -> no shared cache -> libSystem not loaded. FIX IN PROGRESS: image v2 = copy of the flashed image + `/System/Library/Caches/com.apple.dyld/` with HARD LINKS to the 44 cryptex cache files (no extra space; avoids symlink-following doubts), then `tools/sparsediff.py ios16-root-20H392.img ios16-root-20H392-v2.img diff.simg` and flash only the diff. Boot with `ignition_level=1` (shim-boot-0029k.img).
- **ignition_level=0 result** (boot 20:58:07 UTC, `research/boot0029j.log`, photo IMG_20261015_230037): all stages skipped as "ignition level insufficient" (hello/preboot/cryptex1 sniff >= 2, select os cryptex path/graft >= 3, **dyld_cache >= 1**), `ignition boot failed: 89`, "ignition partially disabled", then same `Library not loaded: /usr/lib/libSystem.B.dylib (no such file, no dyld cache)`. => dyld gets the shared cache directory from ignition's dyld_cache stage. Next: `ignition_level=1` (`shim/out/shim-boot-0029k.img`) to skip preboot/cryptex stages but run dyld_cache; its log "finding shared cache on %s ... subpath = %s" will show where it searches. If it searches rootfs /System/Library/Caches/com.apple.dyld, add a symlink there (image rebuild; consider a diff-only sparse flash tool to avoid rewriting 12 GB).
- **APPLE dyld/launchd RUNNING (libignition) with `unentitled_ios_sim_launch=1`** (boot 20:53:24 UTC, `research/boot0029i.log`, photo IMG_20261015_225617): kernel prints "Allowing spawn of iOS binary ... boot-arg set to true"; `shared_region: ... check_np ... vm_shared_region_start_address() failed` (no region yet, normal); dyld's built-in **libignition** (Darwin Ignition Sequence 1.0.0, libignition-51~1974; prints rd=ufsroot0, hardware target sweet, ignition level 0x5, platform 0x2, boot spec local, 7 stages): `hello from launchd.1` -> `preboot: mounting preboot` -> `failed to lookup preboot: 25` (ENOTTY: looks for a separate Preboot volume by role) -> ignition fails -> dyld `Library not loaded: /usr/lib/libSystem.B.dylib ... (no such file, no dyld cache)` -> launchd exit -> panic initproc failed. dyld boot-args found via strings: `ignition_level`, `ignition_force_dylib_root` (forced rootfs/livefs/cryptex fallback), `ignition_halt_after`, `ignition_live_app_graft`; dyld cache search paths include /System/Cryptexes/OS, /System/Volumes/Preboot/Cryptexes/OS/, /private/preboot/Cryptexes/OS/ (present in our image). Next try `ignition_level=0` (`shim/out/shim-boot-0029j.img`).
- **APPLE launchd EXECUTED FROM UFS (2026-10-15).** Flashed iOS image: `img2simg` -> `ios16-root-20H392.simg` (12.1 GB) then `fastboot -S 512M flash userdata ...simg` (24 chunks, 307 s, `research/flash-userdata-ios16.log`; a raw-image flash was killed by earlyoom at 2.6 GB RSS - always flash the sparse image). ABL fastboot hung on getvar after the flash; power+vol-down fixed it. Boot 0029u 20:49:04 UTC (`research/boot0029u-ios16.log`), photo IMG_20261015_225134: `hfs: mounted iOSRoot` -> load_init_program /sbin/launchd -> panic `unexpected SIGKILL of launchd (CS_KILLED) with reason -- namespace 9 code 0xe` = OS_REASON_EXEC / EXEC_EXIT_REASON_WRONG_PLATFORM: our kernel is XNU_TARGET_OS_OSX, iOS-platform binaries are "alien" and refused unless spawn attr platform set or DEVELOPMENT TUNABLE `unentitled_ios_sim_launch`. Next try: same kernel, cmdline + `unentitled_ios_sim_launch=1` (`shim/out/shim-boot-0029i.img`). LONGER TERM: macOS-config kernel marks iOS maps alien (vm_map_mark_alien) and differs from iOS in many policies; an iPhoneOS-config kernel build may eventually be needed.
- **iOS 16 ROOT IMAGE BUILT:** `/run/media/dipa/android/ios-sweet-ipsw/ios16-root-20H392.img` (16 GiB case-sensitive HFS+, label iOSRoot, 12 GB used, fsck OK after `fsck.hfsplus -y` rewrote 32 non-ASCII localized WorkflowKit Shortcut names Linux decomposes differently). Built by `tools/mkiosroot.sh OS.dmg SYSTEMOS.dmg APPOS.dmg OUT.img [SIZE]` (needs sudo; apfs-fuse as root; OS dmg is UDIF -> link must end .dmg). Contents: iPhone X 20H392 OS root + SystemOS cryptex at /private/preboot/Cryptexes/OS (so /System/Cryptexes/OS -> cache, 44 files, dyld_v1 arm64) + AppOS at .../App. /sbin/launchd and /usr/lib/dyld root:wheel 0755. NEXT: (confirm) `fastboot flash userdata ios16-root-20H392.img` (auto-sparse), boot 0029u (rd=ufsroot0) -> Apple launchd attempt.
- **MILESTONE ON HARDWARE: BOOT FROM INTERNAL FLASH.** 0029 CI `38797924912` PASSED, `xnu/out-0029` SHA256 `a68bc847...2a37`. Image `shim/out/shim-boot-0029u.img` (payload-0029u = 0029 kernel + `shim/out/sweet-0028.adt` + `rd=ufsroot0`, NO RAM disk). Boots 20:01:34 and 20:12:37 UTC (`research/boot0029u*.log`), photo IMG_20261015_221403: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `SWEET: root volume is not authenticated (error 25); continuing unsealed` -> `load_init_program ... /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> heartbeat (ran for minutes unattended). userdata currently holds the 8 MB `research/root-hfs.img`. NEXT: build a multi-GB HFS+ image with the iOS 16 (iPhone X 20H392) userland (OS rootfs + SystemOS cryptex contents incl. dyld shared cache at /System/Library/Caches/com.apple.dyld; preserve modes/owners/symlinks; decompress LZBITMAP via apfs-fuse), flash it to userdata (sparse, needs user OK), then try Apple's dyld/launchd. Driver is read-only (root mounts RDONLY), fine for first launchd attempts.
- **userdata FLASHED with the 8 MB HFS test volume** (user said "flash it", 2026-10-15 19:53:17 UTC, `research/flash-userdata-hfs-test.log`: `fastboot flash userdata research/root-hfs.img` OKAY; pre-checks: one sweet device, partition-size:userdata 0x1AC4BFB000, partition-type f2fs, image fsck OK, SHA256 3626ea69...). Android userdata is now destroyed (expected/approved). Boot 0028u at 19:53:20 (`research/boot0028u-hfs.log`), photo IMG_20261015_215541: `BSD root: ufsroot0` -> **`hfs: mounted SweetRoot on device b(1, 0)` from internal UFS** -> panic `rootvp not authenticated after mounting @bsd_init.c:931` (arm64 macOS-config requires FSIOC_KERNEL_ROOTAUTH sealed root for non-ramdisk roots). Patch **0029** (`dd1c284`): SWEET logs `SWEET: root volume is not authenticated (error N); continuing unsealed` instead of panicking (Apple configs keep the panic; pivot_root still requires auth). CI **`38797924912`** running. Next: download out-0029, phone image with sweet-0028.adt + rd=ufsroot0 (no RAM disk), boot -> expect init from UFS.
- **UFS ROOT DRIVER VERIFIED ON HARDWARE (read-only).** 0028 CI `38796139570` PASSED, `xnu/out-0028` SHA256 `8b981640...9da6`; QEMU HFS RAM-disk regression `research/q0028-hfs` still runs init. Phone boot 2026-10-15 19:50:24 UTC (`research/boot0028u.log`, image `shim/out/shim-boot-0028u.img`, phone ADT `shim/out/sweet-0028.adt` with /sweet-ufs, NO RAM disk, `rd=ufsroot0`), photos IMG_20261015_215151/215220: `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB, read-only` -> `BSD root: ufsroot0, major 1, minor 0` -> `hfs_ValidateHFSPlusVolumeHeader: unknown Volume Signature : f188` (Android-encrypted data, as expected) -> `cannot mount root, errno = 19`, kernel retries mountroot (no panic). Nothing written to flash. NEXT (destructive, needs user confirmation right before): `fastboot flash userdata research/root-hfs.img` (8 MB HFS with test init) then boot rd=ufsroot0 -> expect init from internal flash.
- **PATCH 0028 (`33aceac`): XNU read-only UFS root device**, CI **`38796139570`** running (next artifacts xnu/out-0028, research/bt29, run29.log). `bsd/dev/sweet_ufs.c`: reuses ABL's UFSHCI state (like the shim probe), takes over UTRL at a kmem_alloc_contig region (DMA layout: UTRL 0x0, UCD 0x1000, 1 MiB bounce 0x4000), verifies UTRLBA readback before any doorbell, IE=0 polled, one SCSI cmd at a time on LUN0 (TUR x3, READ(10) via bounce, PRDT 256 KiB chunks), flush_dcache64 by PA around each command (host not dma-coherent per DT), finds GPT partition by name (`ufsroot=` boot-arg, default `userdata`), exposes `/dev/ufsroot0`/`rufsroot0` (512-byte logical sectors, physical 4 KiB, DKIOC* ioctls), refuses writes (EROFS). IOKitBSDInit: `rd=ufsroot0` -> sweet_ufs_rootdev() (lazy init) else panic. ADT: `tools/mkadt.py` adds `/sweet-ufs` reg <0x1d84000 0x3000> for the PHONE only (not --qemu). Local compile OK, imports resolve. Sandbox research/bt28 (pre0028 originals). FIRST PHONE TEST PLAN (non-destructive): boot 0028 with phone ADT + `rd=ufsroot0` and NO RAM disk: expect `SWEET UFS: "userdata" on LUN 0: first block 0x2b8c00, 109643 MiB` + `BSD root: ufsroot0`, then root mount failure (userdata is still Android-encrypted) -> panic. That validates the driver before flashing an HFS image into userdata (needs explicit user confirmation at that time).
- **SUPERSEDES the 64 GiB iosroot GPT plan: user said "u can delete android" (2026-10-15).** Use the existing `userdata` partition (LUN0 sda34, 4K LBA 0x2B8C00, 0x1AC4B MiB ~107 GiB) directly as the iOS root: NO GPT changes. Keep bootloaders, recovery (OrangeFox), modem/persist/fsg/modemst untouched. Write the HFS image later with `fastboot flash userdata` (sparse, auto-split under the 768 MiB limit). Android will no longer boot normally (expected; reinstallable). Order: XNU UFS driver first, read-only against the current GPT; flash only once it can locate userdata. Nothing erased yet.
- **DECIDED (user, 2026-10-15): 64 GiB `iosroot` on LUN0 (sda), taken from userdata (wipes Android user data; Android/super kept).** Planned GPT (4K LBAs): userdata 0x2B8C00..0xD7D6FF (~43 GiB, keep type/unique GUIDs and attributes); iosroot 0xD7D700..0x1D7D6FF (0x1000000 blocks = 64 GiB, 1 MiB aligned); backup GPT area unchanged. Procedure: user backs up phone data -> boot OrangeFox recovery (adb) -> back up GPT (sgdisk --backup + raw dd of LBA 0-5 and last 6 blocks) to research/ -> sgdisk edit -> Format Data -> verify Android boots to setup. NOT EXECUTED YET.
- **INTERNAL UFS WORKS FROM THE SHIM (read-only), user authorized internal-UFS approach incl. flashing (2026-10-15, "i allow everything").** Shim probe `shim/ufs.c` (commit `12ed3ed` + filter): ufshc@1d84000 is UFSHCI 2.1 (ver 0x210, cap 0x1587031F, 32 slots), ABL leaves HCE=1, HCS=0x10F (device present, lists ready, UIC ready); probe takes over UTRL at its own buffer (verifies UTRLBA readback before any doorbell), TEST UNIT READY/READ CAPACITY/READ(10) all succeed. LUN0 = 0x1D7D800 x 4 KiB (~126.6 GB), valid GPT (64 entries at LBA 2). Photos IMG_20261015_212916/213325/213429. Big LUN0 partitions (start in 4K LBAs / MiB): super 0xCA00/0x2200 (8.5 GiB), logdump 0x22CA00/64, minidump 0x230A00/128, rawdump 0x238A00/128, recovery 0x240C00/128, cache 0x248C00/384 ext4, exaid 0x260C00/384, cust 0x278C00/1024 ext4, **userdata 0x2B8C00/0x1AC4B MiB (~107 GiB), fs unreadable = encrypted (metadata encryption)**. cache..cust contiguous = only 1.75 GiB (too small for iOS ~10+ GiB). Plan needing user consent: shrink userdata in GPT (wipes Android data) and add an `iosroot` partition at the end of LUN0. LUNs 1-5 not listed yet (sdb..sdf backed up in backup/lun).
- **fastboot limit measured (2026-10-15, read-only getvar):** `max-download-size: 805306368` (768 MiB); `max-fetch-size` unsupported; `is-userspace: no` (ABL fastboot). A `fastboot boot` image (shim+kernel+RAM disk) must be < 768 MiB, so the 2.5 GiB iOS shared cache cannot ride in the boot RAM disk even if XNU gets all RAM. Real userland needs storage access (UFS driver, or USB host) or a much smaller cache. Unlocking full RAM is still needed later (GUI).
- **iOS 16 USERLAND SOURCE (Claude, 2026-10-15).** Chose **iPhone X (iPhone10,3/10,6, D22/D221AP)** iOS **16.7.16 (20H392)** over iPhone 8: same A11 (no PAC -> plain arm64, runs on Kryo 470/ARMv8.2), last iOS for A11; X userland is home-button-less and tall-screen (1125x2436 vs sweet 1080x2400), better fit for later GUI. Note the X has its OWN SystemOS cryptex (different digest from iPhone 8's). IPSW URL in `research/ipsw-x/URL.txt` (+ BuildManifest). Images on the user's external SSD (NOT in git, do not format that disk: it holds the user's photos): `/run/media/dipa/android/ios-sweet-ipsw/iPhone10,3_16.7.16_20H392/` — `087-86593-047.dmg` = Cryptex1,SystemOS (2,743,074,816 B), `087-86698-044.dmg` = OS rootfs (4,730,814,044 B), both zip CRC-32 verified, plus Firmware/*.root_hash/.trustcache/.mtree. AppOS cryptex is 087-86715-047.dmg (10 MB, same as iPhone 8).
  - Images are raw APFS; files use LZBITMAP (decmpfs type 14). 7z cannot decode. Tools: `ipsw` 3.1.738 (AUR ipsw-bin, user-approved) needs apfs-fuse on Linux; **apfs-fuse** built in user space (system cmake broken: cmake 4.4.4 wants libjsoncpp.so.27, jsoncpp 1.9.6 installed = partial upgrade, NOT fixed) with pip cmake + `-DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_CXX_FLAGS="-include cstdint"`, installed to `~/.local/bin/apfs-fuse` (+apfs-dump-quick). Mount via a comma-free symlink (apfs-fuse splits options on ',' in `iPhone10,3`; exFAT has no symlinks -> put link elsewhere): `apfs-fuse LINK/087-86698-044.dmg MNT` -> `MNT/root/...`; unmount `fusermount3 -u MNT`.
  - Verified from headers: `dyld_shared_cache_arm64` magic `dyld_v1   arm64`; `/sbin/launchd`, `/usr/lib/dyld` = cputype 0x100000c subtype 0 (plain arm64). libSystem exists only inside the cache.
  - **BLOCKER for real userland via RAM disk:** shared cache = 3.10 GiB in 44 files (~2.5 GiB without the 592 MB `.symbols`), but the kernel manages only 1.20 GiB (0xb0000000..0xfd000000). Options: (A) give XNU the phone's full ~6 GB (banks 0x80000000+2G and 0x100000000+0xfcc00000, carve-out holes need pmap support) AND check fastboot max-download-size for a multi-GB boot image; (B) storage driver (Qualcomm UFS) to read a root from flash (no flashing allowed: would need a file/partition strategy); (C) run against individual dylibs extracted from the cache (uncertain).
- **MILESTONE ON HARDWARE: HFS+ ROOT FILESYSTEM -> PID 1.** Boot 2026-10-15 18:22:12 UTC (`research/boot0027b.log`, image `shim/out/shim-boot-0027b.img`), photo `IMG_20261015_202334.jpg`: `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive`, no panic. Kernel 0027 (built-in Apple OSS HFS + BearSSL MD5), init with SP alignment fix. NEXT: real iOS 16 userland on the HFS image (dyld, libSystem/dyld shared cache, launchd). Known gaps: entitlements (none granted), SHA-1/SHA-384/512 providers, no storage driver (RAM disk only), root mounted read-only.
- **PHONE HFS ROOT (0027) + SIGBUS ROOT-CAUSED.** Phone boot 2026-10-15 17:49:06 UTC (`research/boot0027.log`, photo `IMG_20261015_200031.jpg`): `hfs: mounted SweetRoot on device b(1, 0)` (HFS works on hardware), init printed its first line, then `pid 1 exited -- exit reason namespace 2 subcode 0xa` = SIGNAL/SIGBUS -> `initproc failed to start` panic. Diagnostic boot 18:08:13 UTC (`research/boot0027d.log`, image `shim/out/shim-boot-0027d.img`, diag init `research/diag-init` from scratch diag-init.S with [a][b][c] markers, `cs_debug=1`; photo `IMG_20261015_201547.jpg`): output `PID [a][b]` then SIGBUS -> fault at first `strb w21,[sp]`; no code-signing messages. Cause: kernel enters a static binary with sp at argc, not necessarily 16-aligned (depends on arg/apple string lengths, differs mockfs vs HFS); EL0 SP alignment check -> EXC_ARM_SP_ALIGN -> SIGBUS (sleh handle_sp_align). QEMU does not enforce SP alignment. NOT a kernel bug: real binaries start in dyld which aligns. Fix `1a8fc15`: sweet-init aligns sp at entry. Rebuilt `research/root-hfs.img`, QEMU `research/q0027-hfs2` OK. Phone image `shim/out/shim-boot-0027b.img` SHA256 `098ba46c...c5c` (payload-0027b, ramdisk match check-0027b) ready, awaiting FASTBOOT. Lesson: Assembly `;` is a comment in Apple arm64 asm (use .macro, not ;-joined #define).
- **HFS ROOT WORKS (QEMU).** 0027 CI `38779441895` PASSED, `xnu/out-0027` SHA256 `a8643886...5f6a`. QEMU `research/q0027-hfs` (RAM disk = `research/root-hfs.img`, rd=md0): `BSD root: md0` -> `hfs: mounted SweetRoot on device b(1, 0)` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` + heartbeat, no panic. Phone image `shim/out/shim-boot-0027.img` (payload-0027 = 0027 kernel + sweet-0021.adt + root-hfs.img + rd=md0, ramdisk byte-match check-0027) ready; awaiting FASTBOOT for phone test.
- **HFS ROOT WORK (Claude), patches 0026-0027.**
  - 0026 (`f0e990c` + link fix `64c96f4`): Apple OSS **hfs-627.100.6** (commit `31d5ec238dfab485e78a9a30b8b92d13e8914f03`, paired with xnu-8796.141.3 in macos-135 release.json) staged by `xnu/patches/0026-stage-hfs.sh` into `bsd/sweet_hfs` (core + hfs_encodings; AppleKeyStore include/key prototypes guarded by CONFIG_PROTECT; SDK TargetConditionals copied). New config option `sweet_hfs` (MASTER + MASTER.arm64.sweet); 40 `optional sweet_hfs` files; Makefile.template foreach adds `_CFLAGS_ADD = -include sweet_hfs_compat.h -I...` (MUST come after kernel -D flags; compat undefs BSD/XNU_KERNEL_PRIVATE and the CONFIG_* HFS tests so kext-config.h decides: macOS profile, no content protection). `sweet_hfs_iokit.c` replaces hfs_iokit.cpp/hfs_encodings_kext.cpp: `sweet_hfs_register()` called in bsd_init after vfsinit (encodings init, vfs_fsadd VFS_TBLCANMOUNTROOT, zones, sysctls); is_ejectable 0, iterate_media none, serial KERN_NOT_SUPPORTED, OSKextGetCurrentLoadTag -> kOSKextInvalidLoadTag (renamed via compat macro). hfs_encodings' own `hfs_allocated` renamed per object (separate kexts on Apple; first CI `38777325964` failed on that duplicate at link). mockfs now validates Mach-O magic (its TODO) so non-Mach-O roots fall through to HFS (new fs entries come AFTER mockfs in vfsconf). CI `38778133720` PASSED, `xnu/out-0026` SHA256 `0b49170c...701a`, prints `SWEET HFS: hfs-627.100.6 registered`.
  - HFS+ image: `research/root-hfs.img` (8 MB, mkfs.hfsplus from AUR hfsprogs installed with user approval; loop-mounted with sudo; /sbin/launchd = research/sweet-init, /dev; fsck.hfsplus OK). QEMU `research/q0026-hfs`: `BSD root: md0` then data abort in MD5Init from hfs_getvoluuid (mount computes volume UUID).
  - 0027 (`14bf2b7`): 0020 stager also copies BearSSL hash/md5.c + codec/dec32le.c/enc32le.c; `corecrypto_md5.c` SWEET branch converts MD5_CTX <-> br_md5_context around br_md5_* calls; wrappers sweet_md5.c/sweet_dec32le.c/sweet_enc32le.c. Host test 40/40 match md5sum. CI **`38779441895`** running.
  - Local tooling: `tools/xnu-cc.py` has `XNU_CC_POST` (flags after logged ones). Sandbox `research/bt28/xnu` = 0025 CI tree + 0026/0027 edits; originals `research/pre0026`, `research/pre0027`. HFS local objects `research/hfs-objs`. Checker entries updated to bt28.
  - SHA-1 / SHA-384/512 still have no provider.
- **MILESTONE ON HARDWARE: USERSPACE PID 1 RUNS ON THE PHONE.** Boot 2026-10-15 17:16:00 UTC (`research/boot0025.log`: send OKAY0.410s, boot OKAY0.135s), image `shim/out/shim-boot-0025.img` SHA256 `9dbfa0b1...89db0`. Photo `IMG_20261015_191733.jpg`: `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> repeated `SWEET init: still alive` (5 s heartbeat), no panic. Kernel 0025 + mockfs RAM disk + built-in no-entitlements AMFI. No flashing performed.
- **NEXT (toward real iOS userland):** real root filesystem with real binaries. Options: (a) build Apple OSS `hfs` (macOS 13.5 tag `hfs-627.100.6`) into SWEET like libpthread, then an HFS RAM disk image; (b) iOS 16 dyld + libSystem/dyld shared cache from the IPSW (needs APFS or repacking onto HFS). Expected hurdles: entitlements (sweet_amfi grants none), SHA-1/MD5/SHA-384/512 providers (BearSSL), missing kexts/daemons. Current init is a static test program, not launchd.
- **MILESTONE: USERSPACE RUNS (QEMU).** 0025 CI `38774788048` PASSED, `xnu/out-0025` SHA256 `5496069b...4877`. QEMU `research/q0025-rd` (150 s, no panic): `BSD root: md0` -> `load_init_program: attempting to load /sbin/launchd` -> `*** SWEET userspace: init running as PID 1 ***` -> `SWEET init: still alive` every 5 s. Exec, ad-hoc SHA-256 code signature, syscalls, devfs /dev/console, select timeouts all work. Phone image prepared: `shim/out/shim-boot-0025.img` 16,515,072 bytes SHA256 `9dbfa0b15140c0bd733a16c4f727f6a7df44a8741f98d8e266d5f2fa4f689db0` (payload-0025 = 0025 kernel + sweet-0021.adt + research/sweet-init + rd=md0; ramdisk byte-match check-0025). Waiting for user to put phone in FASTBOOT.
- **0024 CI `38773277811` PASSED**, `xnu/out-0024` SHA256 `a0ba964b...4348`. QEMU `research/q0024-rd` and **PHONE (boot 2026-10-15 17:05:55 UTC, `research/boot0024.log`, image `shim/out/shim-boot-0024.img` SHA256 `cf3dac86...6964`, 16,510,976 bytes, payload `shim/out/payload-0024.bin` = 0024 kernel + `shim/out/sweet-0021.adt` + RAM disk `research/sweet-init` + rd=md0; ramdisk byte-match `check-0024`)** agree: `Added memory device md0`, `BSD root: md0`, `load_init_program: attempting to load /sbin/launchd`, then data abort in accelerate_entitlement_queries (PC 0x...77d2458, FAR 0x1a0) = NULL AMFI interface. Photo `IMG_20261015_190715.jpg`. RAM disk root is physically verified.
- **0025 (`2518c79`)**: new `bsd/kern/sweet_amfi.c` registers a built-in AMFI interface at EARLY_BOOT/MIDDLE: no entitlements (adjustContextWithoutMonitor succeeds without creating a context, queries KERN_DENIED, copies NULL/KERN_NOT_FOUND, get_xml/transmuted false); WithMonitor KERN_NOT_SUPPORTED; OSEntitlements_query and query_context_to_object panic explicitly (CoreEntitlements closed; no kernel caller); TrustCache version 0 (0015 keys on trust_cache_rt==NULL, img4 absent -> still unavailable); CoreEntitlements table zero (PMAP_CS only). Compiles locally; checker updated (bt27 entries). CI **`38774788048`** running. Next artifacts `xnu/out-0025`, `research/bt29`, `research/run29.log`. Real iOS binaries will need real entitlements later (no OSS CoreEntitlements exists).
- **0021-0024 RAM-disk-root iteration (Claude), QEMU only so far, no new phone boot since 0020.** Each kernel tested with `tools/mkpayload.py KERNEL research/q0021.adt OUT --ramdisk research/sweet-init --cmdline "debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress rd=md0"` then `tools/qemu-sweet.py OUT DIR --secs 150 --kernel KERNEL --fail-on-panic` (PATH needs ~/swift/usr/bin for llvm-nm). Fresh ADTs: `research/q0021.adt` (QEMU), `shim/out/sweet-0021.adt` (phone).
  - 0021 CI `38769532000` PASSED, `xnu/out-0021` SHA256 `2b7500a1...962e`, `research/bt25`/`run25.log`. QEMU `research/q0021-rd`: md0 root, then assert `iomediaClass` in IOService::publishHiddenMedia.
  - 0022 (`20ece9c`, publishHiddenMedia without IOMedia class) CI `38770666158` PASSED, `xnu/out-0022` SHA256 `a4d0e787...30c5`, `research/bt26`/`run26.log`. QEMU `research/q0022-rd`: data abort in SHA256_Init (NULL g_crypto_funcs) from vm_kernel_addrhash_internal.
  - 0023 (`c8089d1`, libkern SHA256_Init/Update/Final use built-in ccsha256_ltc_di + ccdigest_init/update on SWEET; also serves code-signing SHA-256; SHA-1/MD5/SHA-384/512 still have NO provider - BearSSL from 0020 could supply them later) CI `38771876423` PASSED, `xnu/out-0023` SHA256 `d763fed7...1003`, `research/bt27`/`run27.log`. QEMU `research/q0023-rd`: **mockfs mounted md0, `load_init_program: attempting to load /sbin/launchd`**, then panic `mockfs_fsnode_vnode failed to create fictitious pages ... rvalue = 5` (mockfs.c:351).
  - 0024 (`3293c80`): mockfs used memdev mi_base (4K page number of a VIRTUAL kernel address for IOKit RAMDisk, truncated to 32 bits) << PAGE_SHIFT as a physical address. Now zero-copy pager mapping only when mi_phys (with 4K units); virtual md uses pagein/blockmap/strategy -> memdev bcopy. memdev's own mdPhys path assumes 4K ppnums (unsafe on 16K arm64), so do NOT switch the RAMDisk to physical. CI **`38773277811`** running. Next artifacts `xnu/out-0024`, `research/bt28`, `research/run28.log`.
  - Sandboxes: bt25/bt26/bt27 contain the next patch's edited files; pristine copies in `research/pre0022`..`pre0024`.
- **PATCH 0021 (Claude): RAM disk root via mockfs -> first userspace program.** Commits `9c37771` (initial; CI `38768500280` FAILED: mockfs_fsnode.c kfree_type(mockfs_fsnode_t) typed-alloc static assert; local xnu-cc stubs `__builtin_xnu_types_compatible` so it can't catch this) and `193772f` (fix), CI **`38769532000`** running: https://github.com/dipa-studio/ios-sweet/actions/runs/38769532000. Next artifacts: `xnu/out-0021`, `research/bt25`, `research/run25.log`.
  - Kernel: `config/MASTER.arm64.sweet` FILESYS_BASE += `mockfs` (XNU's built-in FS: root device is itself a Mach-O, served as /sbin/launchd, plus /dev for devfs). Upstream mockfs bit-rot fixed: kalloc_type/kfree_type used the POINTER typedef mockfs_fsnode_t (nodes were 8 bytes) -> `struct mockfs_fsnode`. `IOService::setRootMedia` asserted IOBlockStorageDriver class exists (IOStorageFamily absent): SWEET-only, a missing class means root=NULL (same as IOSetImageBoot); Apple path keeps assert. All 21 patches apply (`research/check-patch-order.py`); 5 TUs compile locally with -DMOCKFS (`research/mockfs-objs`), imports resolve vs 0020 kernel. Sandbox `research/bt24/xnu` now holds 0021 versions of those 3 files; pristine 0020 copies in `research/pre0021`.
  - Tools: `tools/mkpayload.py --ramdisk IMAGE` appends IMAGE as an extra payload segment right after the kernel, moves kernel_end past it (shim unchanged: ADT+boot_args follow it, image stays below topOfKernelData), and adds ADT `/chosen/memory-map` `RAMDisk`=<phys,size>. Boot with `rd=md0`. Without --ramdisk output is byte-identical to existing 0020 QEMU and phone payloads (verified). `tools/sweet-init.S` + `tools/mkinit.py`: PIC static init (open /dev/console, print PID, heartbeat every 5 s via select, never exits) wrapped into a static arm64 Mach-O (__PAGEZERO, __TEXT@0x100000000, LC_UNIXTHREAD, ad-hoc SHA-256 CodeDirectory v0x20400, 4K pages). Build: `~/swift/usr/bin/clang -target arm64-apple-ios16.0 -c tools/sweet-init.S -o X.o && tools/mkinit.py X.o research/sweet-init` (ld64.lld cannot link static iOS). Signature not verified by a real codesign; the kernel will tell.
  - QEMU with 0020 kernel + RAM disk (`research/q0020-rd.bin`, rd=md0, 150 s `research/q0020-rd150`): `Added memory device md0`, **`BSD root: md0, major 1, minor 0`** (plumbing works), then the setRootMedia assert (now fixed in 0021). NOTE: QEMU needs >60 s to reach IOFindBSDRoot (60 s run showed nothing after stf0; likely RTC/inittodr wait), so use --secs 150.
  - NEXT: download 0021, QEMU 150 s with ramdisk; expect mockfs mount then init exec -> `*** SWEET userspace: init running as PID 1 ***`. Then phone boot with same payload (phone ADT shim/out/sweet-0020.adt pattern + --ramdisk + rd=md0).
- **0020 PHONE RESULT (user transcription of screen, 2026-10-15): KERNEL INIT COMPLETE, WAITING FOR ROOT.** After Skywalk self-tests PASSED, kminit, ifnet_attach lo0/gif0/stf0, screen prints `BSD`, then `Waiting on <dict><key>IOProviderClass</key><string>IOMedia</string><key>Content</key><string>Apple_HFS</string></dict>` and `Failed to write boot-picker-bringup-reason to NVRAM.` No panic. This is IOFindBSDRoot waiting for a root device (none exists); NVRAM warning is expected (no NVRAM driver). QEMU `cpu_idle` snapshot is presumably the same wait (not GDB-confirmed; milestone GDB run was cancelled by user since phone answered it). Draft `research/check-milestones20.gdb` (hbreaks inittodr/vfs_mountroot/IOFindBSDRoot/bsd_utaskbootstrap) left uncommitted/ignored.
- **NEXT MILESTONE: root filesystem -> launchd.** Plan: (1) RAM disk: shim places an image in RAM, ADT /chosen/memory-map `RAMDisk` entry, boot-arg `rd=md0` (XNU md driver). (2) HFS is a separate kext on Apple; build Apple OSS `hfs` (tag paired with macOS 13.5 in distribution-macOS macos-135 release.json) into SWEET like libpthread 0019. APFS is closed. (3) Minimal HFS image with iOS 16 launchd (later: dyld/shared cache; AMFI/code-signing absent will be a later hurdle). User's end goal is full iOS GUI.
- **0020 (AES) VERIFIED + PHONE BOOTED (Claude took over after Codex usage limit).** Actions `38765422261` (`ab9e23f`) PASSED; kernel `xnu/out-0020/kernel.development.sweet` checksum OK; buildtree `research/bt24`, log `research/run24.log`. Actual-kernel AES checks PASS (`research/check-aes20.gdb` / `.log`, 12 extra CBC cases match OpenSSL). 45s QEMU `research/q0020`: no panic, zero unknown glyphs, past old TCP/AES panic -> Skywalk self-tests PASSED -> bsd_autoconf kminit -> ifnet_attach lo0/gif0/stf0; final snapshot PC in `cpu_idle` (idle or waiting; NOT yet diagnosed, could be root-device wait). Image `shim/out/shim-boot-0020.img` 16,461,824 bytes SHA256 `775200cb02d95fc750981516b79d91dcdc96184bbe67a38f9d57c59b4a391828`, ramdisk byte-matches `payload-0020.bin` (`check-0020`). **Phone temporarily booted 2026-10-15 16:10:00 UTC**: one FASTBOOT product sweet, send OKAY0.407s, boot OKAY0.134s, total0.549s, exit0 (`research/boot0020.log`). Awaiting user photo; do not reboot the phone before it. NEXT: read photo; diagnose what QEMU waits on after stf0 (GDB backtrace of threads / longer run). Codex's STOP request below is complete.
- User requests STOP after completing the current0020 AES iteration (Actions/QEMU/phone), then leave a precise committed handoff for another AI. User says FASTBOOT ready again after0019 photo. Do not start a new blocker fix after this iteration.
- Goal: iOS16-generation XNU on Redmi Note10Pro sweet/SM7150. Always commit, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups. No userland/root filesystem boot yet.
- **Patch0020 update:** initial `e71098d` / Actions `38765012466` superseded by scalar-only compile flags. Added -mgeneral-regs-only to all six provider/BearSSL TUs and corecrypto_aes.c; object disassembly now confirms no SIMD. Updated implementation `ab9e23f`, Actions `38765422261` queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38765422261. Do not launch another run. portable BearSSL AES CBC and legacy one-block ECB wired directly into SWEET corecrypto_aes.c. Genuine bitslice implementation, no CPU AES/SIMD requirement, heap or fake global crypto table. Source fetched by `0020-stage-bearssl.sh` from official BearSSL git at immutable `7bea48e5e850ab4cafbe68d3765cdaba13a86d6f`; MIT license retained, downloaded source stays out of git. Kernel limits include adapter only. All128/192/256-bit keys, CBC encrypt/decrypt, copied contexts, in-place/out-of-place; zero block count and size overflow handled, invalid keys clear context. Seven TUs compile to arm64 objects (`research/aes-objs`), imports resolve, all20 patches apply and sources match (`research/patch0020-check.log`). Sandbox `research/bt23/xnu`, originals `research/pre0020`. NEXT: Actions then actual-kernel NIST/random CBC/ECB checks and >=45s QEMU before another phone boot. Next artifacts out-0020 / bt24 / run24.log. 0020 updated CI pending. Local sources/checks match the scalar-only patch.
- **Latest built kernel0019**, implementation `256d3f0`, patches0001-0019. Actions `38763072907` PASSED (4m5s): https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23` (no nested .git). Seven pthread source/build/header files and staged adaptations byte-match local compile inputs.
- **0019 hardware photo received** `IMG_20261015_175306.jpg`: pthread registration visible, passes mbinit and DLIL checksum/scheduling, same AES fault as QEMU: PC`0xfffffe00079174e0` (`aes_encrypt_key128`), LR`0xfffffe000767c3a4` (`tcp_init`), FAR0x78, x8=0. Disassembly proves NULL g_crypto_funcs->ccaes_cbc_encrypt. Photo processed; no more0019 observation pending. General crypto table remains absent, other hash/mode operations may still fault after0020. DO NOT bypass TCP or install fake crypto. XNU already contains SHA256/HMAC implementations; AES source there is a dispatch wrapper. Full future provider interface libkern/libkern/crypto/register_crypto.h. Apple/corecrypto default README describes evaluation-only licensing, so no external corecrypto was fetched or staged; BearSSL selected for this portable AES integration.
- **0019 pthread FIXED in QEMU and observed beyond its init on phone**: 45s QEMU `research/q0019`, zero unknown glyphs, then AES panic. Actual-kernel API checks PASS `research/check-pthread19.gdb` / `.log`, guest `research/q0019-api`: function/callback table identity, actual provider pthread_init returns, locks/global hash/threadcall/typed zones initialized, thread_selfid via syscall shim + buffer bounds, process hash init/delete via shims restores NULL. Monitor quit prints expected remote-disconnect after PASS. All fixture guests stopped.
- **0019 provider**: genuine Apple libpthread-514.100.2 commit `a6c70ca0e544347a0377babf748f831577ec24f9`, exact paired release with xnu8796.141.3 in distribution-macOS/macos-135/release.json (`research/macos-135-release.json`). 0019 shell stage runs before patches (workflow copies *.sh); three SWEET wrapper TUs use kext BSD header view, vm_fault_external, renamed provider-side pthread_kern/current_uthread; register real function table at EARLY_BOOT SECOND, real pthread_init later. Stager applies bounded address casts, zero user addresses, proper panic format. SWEET opaque ksyn storage enlarged48->56 for trailing kwe_uth, checked with provider static assertion. Local pre-CI TargetConditionals fixture was syntax-only; artifact bt23 carries actual SDK header and CI is authoritative.
- **Phone0019 temporarily booted** 2026-10-15 15:51:36 UTC: exactly one FASTBOOT/product sweet verified; send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). Image `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`. Phone ADT/payload `shim/out/sweet-0019.adt` / `payload-0019.bin` timer19, unpacked ramdisk byte-match (`check-0019`). EntryPA0xb146b488, kernelendPA0xb2000000, boot_argsPA0xb2004000/top0xb2008000. Last user FASTBOOT+USB reply preceded this boot; do not assume phone is still in FASTBOOT.
- **CPU0018 physically verified** by `IMG_20261015_173951 (2).jpg`: boot CPU0 registered, real SGI1 verified, initialization complete -> BSD/MAC/mbinit -> old pthread-table panic. SweetCPU uses legacy IOCPU, ml_processor_register/processor_start/initCPU, real SGI1 clears SIGPdisabled before max CPUs completion; no forced flags/skipped waits. CPU APIs and two-CPU rejection passed (`research/check-cpu18.gdb`, `q0018-api`, `q0018-smp`). Single core; SMP/suspend unsupported. CURRENT SWEET has NO USE_APPLEARMSMP.
- QEMU next run: generate fresh `tools/mkadt.py research/q0020.adt --qemu` (timer27), mkpayload with `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`, then `tools/qemu-sweet.py PAYLOAD OUT --secs 45 --kernel KERNEL --fail-on-panic`. 12s can miss later panics because IORTC waits30s. Runner snapshot only: panic exit2, blank/incomplete exit3; absence of panic does not mean complete boot. Qualcomm XPU/ABL/panel and phone SMC PSCI require hardware checks.
- Local checker `tools/xnu-cc.py research/run23.log research/bt23 FILTER --per-file`, XNU_CC_OBJDIR for objects. For new BearSSL TUs add XNU_CC_EXTRA with -I bt23/xnu/libkern/crypto/sweet_bearssl/{inc,src}. Patch checker `research/check-patch-order.py` uses temporary upstream index; source fixtures/artifacts ignored under research. GDB mask registers to unsigned64, use function-entry manual-call return traps, discard manipulated guests. No QEMU guest intentionally left running.

## Session log and earlier handoffs (superseded by the active summary above)

### Prior 0019 transition notes (superseded)

- Goal: iOS 16 generation XNU on sweet. Always commit completed work, use gh/Actions for kernel builds, keep this handoff current. Temporary fastboot boot only; preserve Android/backups.
- **0019 build PASSED** Actions `38763072907` (4m5s), implementation `256d3f0`. Kernel `xnu/out-0019/kernel.development.sweet`, SHA256 `a27df7568f03fb541cf0e8024c0a594fa178a85054fcf9eba29158cbd4c5ecc0`; checksum verified. Log/source `research/run23.log` / `research/bt23`; all seven patched files and staged provider adaptations match local compile inputs. Prefer bt23 as the next baseline.
- **0019 pthread FIXED in QEMU**: 45s run `research/q0019` registers provider, passes mbinit, DLIL SUM16 checks and DLIL thread scheduling. Actual-kernel GDB checks `research/check-pthread19.gdb` / `.log` PASS: function/callback table identity, real _pthread_init returns, locks/global hash/cleanup threadcall/typed zones non-NULL, thread_selfid via actual syscall shim with output bounds, process hash init/delete through actual shims restores NULL. Guest stopped after tests; no fixture left running. GDB monitor quit prints expected remote disconnect after PASS.
- **Current next blocker:** QEMU0019 panic data abort FAR0x78 at `aes_encrypt_key128` PC`0xfffffe00079174e0`, called by `tcp_init` LR`0xfffffe000767c3a4`. Disassembly confirms `g_crypto_funcs == NULL`, loading ccaes_cbc_encrypt at+0x78. General crypto registration is still absent; DO NOT bypass TCP or supply fake crypto. Next integrate a genuine compatible crypto implementation/provider (AES first needed here, other digest/mode APIs also used). XNU contains SHA256/HMAC but no AES implementation; its corecrypto_aes.c is a dispatch wrapper. Full crypto table is in libkern/libkern/crypto/register_crypto.h.
- **0019 phone image prepared and verified**, user reports FASTBOOT+USB again; exactly one device/product sweet verified. `shim/out/shim-boot-0019.img`, 16,457,728 bytes, SHA256 `19429a57e486b856880df9e27327ed488e0139345311fdb0350974e72103a9a1`; unpacked ramdisk matches phone payload (`shim/out/check-0019`, `payload-0019.bin`, `sweet-0019.adt`, timer19). EntryPA0xb146b488; kernelendPA0xb2000000; boot_argsPA0xb2004000/top0xb2008000. Usual debug cmdline cpus=1/-noprogress. **Temporarily booted 2026-10-15 15:51:36 UTC**: send OKAY0.406s, boot OKAY0.134s, total0.546s, exit0 (`research/boot0019.log`). User asked for photo after45s. Await the photo; DO NOT reboot again before observation. Bootloader acceptance only; no0019 physical progress observed yet.
- **Hardware photo confirms 0018 progress** (`IMG_20261015_173951 (2).jpg`): real phone prints `SWEET CPU: boot CPU 0 registered, SGI1 verified, initialization complete`, enters BSD/MAC, reaches `mbinit: done`, then the same missing-pthread-function-table panic as QEMU at pthread_shims.c:318. CPU completion/interrupt delivery is now physically observed. The photo was received; no further phone boot performed yet.
- **Patch0019 committed/pushed `256d3f0`; Actions `38763072907` queued/running:** https://github.com/dipa-studio/ios-sweet/actions/runs/38763072907. Do not launch a duplicate. genuine Apple OSS libpthread-514.100.2 provider (immutable commit `a6c70ca0e544347a0377babf748f831577ec24f9`), paired with xnu-8796.141.3 by Apple's `distribution-macOS/macos-135/release.json` (`research/macos-135-release.json`). `0019-stage-libpthread.sh` fetches/stages it before patches; workflow now copies shell scripts too. SWEET-only wrappers compile all three real kernel sources, rename provider-side symbols, use kext header view and vm_fault_external, register the real function table at EARLY_BOOT SECOND. Existing pthread_init then runs the actual provider initialization. No pthread wait/syscall is bypassed. Source staging includes bounded explicit address casts/zero user addresses and panic-format fixes. SWEET kernel opaque ksyn storage enlarged from48 to56 bytes to contain this provider's trailing kwe_uth, with a provider size assertion. Local compile of three provider TUs plus pthread_shims/kern_fork passed; imports resolve and provider exports do not collide with existing kernel symbols. All19 patches apply and changed sources match (`research/patch0019-check.log`). Source sandbox `research/bt22/xnu`, originals `research/pre0019`, objects `research/pthread-objs`. Local TargetConditionals fixture only has target macros for syntax; CI stages the real macOS SDK header and is authoritative. Next Actions artifacts: out-0019 / bt23 / run23.log; run QEMU >=45 seconds. 0019 CI is pending; no 0019 QEMU run yet.
- **Latest kernel implementation `e7d9550`, patches0001-0018; CI `38760004398` PASSED (3m56s)**: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. No build is pending. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; checksum verified. Source/log `research/bt22` / `research/run22.log` (baseline for patch0019; no nested .git). New driver/config sources match CI exactly.
- **CPU wait FIXED in QEMU**: SweetCPU uses legacy IOCPU, validates single boot CPU, ml_processor_register -> processor_start -> initCPU real SGI1 -> scheduler/IOKit completion -> ml_set_max_cpus. It does NOT force a flag or skip a wait. CPU APIs passed: Running CPU0, processor_array[0] association, SGI signalling enabled, name, unsupported secondary-start error (`research/check-cpu18.gdb` / `.log`, `research/q0018-api`). Single-core only; SMP and suspend unsupported. Two-CPU topology fails explicitly (`research/q0018-smp`).
- **Next blocker reproduced in 45s QEMU** (`research/q0018-long`, zero unknown glyphs): BSD initialization reaches MAC framework, network mcache and `mbinit: done`, then **`pthread kernel extension not loaded (function table is NULL). @pthread_shims.c:318`**. Do not bypass pthread_init: find/integrate the matching open-source libpthread kernel implementation and register its real function table. A 12s run `research/q0018` looked panic-free before the 30s IORTC wait elapsed; use >=45s or GDB checkpoints for the next iteration. No userland/root filesystem boot yet.
- **Phone 0018 TEMPORARILY BOOTED** 2026-10-15 **15:31:15 UTC**: exactly one FASTBOOT device verified product sweet; send OKAY0.400s, boot OKAY0.134s, total0.539s, exit0. Local log `research/boot0018.log`. This confirms bootloader acceptance only. User was asked for a photo; await it, DO NOT reboot the phone again before their observation. No flashing performed.
- Current hardware image `shim/out/shim-boot-0018.img`, **16,437,248 bytes**, SHA256 **`b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`**. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin` (timer19), unpacked ramdisk exactly matches payload (`shim/out/check-0018`). EntryPA0xb146b488; kernelendPA0xb1ffc000; boot_argsPA0xb2000000/top0xb2004000. Command line `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`.
- QEMU payload/ADT `research/q0018.bin` / `research/q0018.adt` (timer27). Run `python3 tools/qemu-sweet.py research/q0018.bin research/NEW-OUT --secs 45 --kernel xnu/out-0018/kernel.development.sweet --fail-on-panic`; fresh ADT seed for a new payload. Output fb.png/fb.txt/regs.txt/qemu.log/result.json. Visible panic exit2; blank/incomplete decode exit3; no_panic_observed is snapshot-only, not successful boot. -noprogress prevents the graphical indicator corrupting console text. Qualcomm XPU/bootloader/panel and SMC PSCI still need physical validation.
- Patches0014-0017 fixed PRNG registration/direct SHA256, explicit unavailable trust-cache service with rejected loads/no matches, built-in SweetPlatformExpert, and timer PPI from ADT (phone19/default19, QEMU27). All their checks/artifacts are preserved in the history below. CURRENT SWEET has NO USE_APPLEARMSMP; do not assume gCPUIC/gAIC/gPMGR AppleARMSMP globals exist.
- Local single-file checker: tools/xnu-cc.py research/run22.log research/bt22 FILTER --per-file, output via XNU_CC_OBJDIR. Patch checker `research/check-patch-order.py` applies all18 via temporary index, matches sandbox sources. Sandbox for0018 `research/bt21/xnu`, originals `research/pre0018`, objects `research/cpu-objs`. First compiler issues were missing machine/atomic.h and nonexistent getNameSymbol; fixed and both TUs compiled successfully before CI. Fixtures/artifacts under research are local-only/ignored.
- GDB: mask int(register)&((1<<64)-1) for unsigned kernel pointers; use function-entry manual-call return traps, discard manipulated guests. No QEMU fixture is intentionally left running.

### Earlier active handoff snapshot (superseded)


- **0018 milestone:** Actions `38760004398` PASSED (3m56s), checksums passed, new CPU/build files byte-match CI tree. Kernel `xnu/out-0018/kernel.development.sweet`, SHA256 `b3c8d59acc88f93a2c836eb2527a05ed4fbaac7c580a2ea8c3b795137f4aadf1`; log/tree `research/run22.log` / `research/bt22`. QEMU `research/q0018` 12s: boot CPU registered, SGI1 verified, CPU initialization complete, **BSD initialization entered** (copyright, MAC framework, buffer headers), no panic/zero unknown glyphs. Direct CPU API checks PASS (`research/check-cpu18.gdb`, `.log`, `research/q0018-api`): CPU0 Running, processor matches processor_array[0], real SGI enabled, CPU name correct, secondary-start returns KERN_NOT_SUPPORTED. Two-CPU ADT correctly panics before registration (`research/q0018-smp`). Longer 45s run `research/q0018-long` still running; next BSD wait/fault not yet identified.
- **Prepared 0018 phone image:** `shim/out/shim-boot-0018.img`, 16,437,248 bytes, SHA256 `b7a23595d143a76c72c9fe2cfcc5d77a8f16987b5af1a2703bbffdfa6922908c`. Phone ADT/payload `shim/out/sweet-0018.adt` / `shim/out/payload-0018.bin`, usual debug args with cpus=1 and -noprogress. Unpacked ramdisk byte-compared (`shim/out/check-0018`). Entry PA remains 0xb146b488; kernel end PA 0xb1ffc000, boot_args 0xb2000000/top0xb2004000. User reports FASTBOOT+USB ready; read-only check found exactly one product sweet. NEXT: temporary fastboot boot of this verified image, record send/boot results, then await hardware photo without rebooting again.
- Patch 0018 committed/pushed **`e7d9550`**; Actions **`38760004398`** queued/running: https://github.com/dipa-studio/ios-sweet/actions/runs/38760004398. Do not launch a duplicate run.
- Active continuation: patch **0018** implemented in `iokit/Kernel/arm/SweetCPU.cpp` + arm64 source list + exact qcom,kryo470 personality. Keeps legacy IOCPU, accepts ONLY the single boot CPU, fills ml_processor_info from parsed topology with CPU object as cpu_id, calls ml_processor_register and processor_start. initCPU sends SGI1 via ICC_SGI1R_EL1 and waits (1-second deadline) for real cpu_signal_handler to clear SIGPdisabled. Only after successful startup calls ml_cpu_init_completed/cpusRunning and publishes completion/max CPUs. Secondary startup/suspend are explicitly unsupported. Local C++ compile passed for both TUs (`research/cpu-objs`), all imports resolve, object contains dsb ishst / ICC_SGI1R / isb; all18 patches apply in order and match sources. Sandbox `research/bt21/xnu`, originals `research/pre0018`; next CI artifacts should use `xnu/out-0018`, `research/bt22`, `research/run22.log`. User has the phone available; first run QEMU, then prepare/temporarily boot useful hardware progress.
- Goal: iOS 16 generation XNU on Redmi Note 10 Pro / sweet. User wants persistent progress, commits, kernel builds via `gh` Actions, and this handoff kept current across agent switches. Temporary `fastboot boot` only; preserve Android and backups.
- Latest kernel implementation: **`aa3f991`**, patches **0001-0017**. All four new Actions builds PASSED: 0014 `38748543058` (4m0s), 0015 `38749549779` (4m3s), 0016 `38750733996` (4m3s), 0017 **`38751507437` (4m7s)**. Latest: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. No build is pending.
- **Current blocker: CPU initialization has no SWEET CPU driver.** QEMU registers SweetPlatformExpert, then kernel_bootstrap_thread waits in **kperf_init_early -> ml_wait_max_cpus**. Confirmed via actual-kernel GDB call stack (`research/locate-cpu-wait2.log` / `.symbols`) and normal-run `max_cpus_initialized == 2` (MAX_CPUS_WAIT). Do not force the flag or remove the wait. Next implement real CPU registration and completion using XNU's CPU/processor interfaces. CURRENT SWEET uses legacy IOCPU (`USE_APPLEARMSMP` is absent); enabling AppleARMSMP is a separate architectural change requiring GIC/PMGR services. No userland/root filesystem boot yet.
- Fixed this session: PC=0 unregistered PRNG callback (0014, built-in HMAC-SHA256 provider + direct entropy/write_random hashing); absent Image4/AMFI trust-cache service (0015, unavailable runtime, loads rejected and queries no-match); missing platform driver (0016, SweetPlatformExpert exact personality); incorrect QEMU timer IRQ (0017, validated ADT PPI property, phone default19/QEMU27).
- **Latest kernel** `xnu/out-0017/kernel.development.sweet`, SHA256 `055a80190ab998b4df9203f1102072dcc78faad1779a537a514e522b682b582f`. Buildtree/log **`research/bt21` / `research/run21.log`**; all nine changed C/C++/header/config files byte-match local checked sources. Checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`. Preferred baseline for patch 0018: `research/bt21/xnu` (no nested .git).
- **QEMU verified**: `research/q0017-noprogress` ran **30 seconds**, no visible panic, **zero unknown glyphs**, IRQ exceptions returned normally (4 IRQs, tickless idle). It still waits for CPU completion, so this is NOT a completed boot. Earlier 15s run `research/q0017` captured 122 IRQs, timer value27, GICR_ISENABLER0 `0x08000002`, and CPU WAIT; graphical progress overlay corrupted 13 glyphs. Add **`-noprogress`** to keep the console readable. New runner classifies incomplete/blank decoding explicitly (exit3 with --fail-on-panic), visible panic exits2. Snapshot-only; use regs/GDB to diagnose stalls.
- Current QEMU payload/ADT: **`research/q0017-noprogress.bin` / `research/q0017.adt`**. Run: `python3 tools/qemu-sweet.py research/q0017-noprogress.bin research/NEW-OUT --secs 30 --kernel xnu/out-0017/kernel.development.sweet --fail-on-panic`. Generate fresh seed with mkadt for a new payload. QEMU virt models generic ARM execution, not Qualcomm XPU/bootloader/panel or the phone's SMC PSCI conduit.
- **Prepared phone image**: **`shim/out/shim-boot-0017.img`**, 16,416,768 bytes, SHA256 `51ff7fe30b4a6668c3452ffe1da922c5ac30cb8de60625c2a652587ecbd0ec92`. Phone ADT/payload `shim/out/sweet-0017.adt` / `shim/out/payload-0017.bin` (timer19). Unpacked ramdisk exactly matches payload (`shim/out/check-0017`). Command line **`debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam -noprogress`**. NOT sent to phone this session: known CPU-driver wait should be addressed in QEMU first. Last actual phone boot remains 0013; user's latest photo `IMG_20261015_160033.jpg` confirmed the old PRNG PC=0 panic.
- Direct QEMU/GDB API checks: PRNG 600-byte chunking, buffer bounds, changing output, zero-length reads/writes, user reseed, contended refresh, generator1 init/output PASS again on latest0017 (`research/check-prng17.gdb` / `.log`, guest `research/q0017-api`). Trust-cache unavailable-service/argument/output cases PASS on0015 (`research/check-trustcache.gdb` / `.log`). Platform registration + target/product normal/truncated/zero/null/bounds PASS on0016 (`research/check-platform.gdb`, `research/check-platform3.log`). Different platform ID correctly retains IOPanicPlatform fallback (`research/q0016-negative`). Timer PPI32 and size2 correctly panic (`research/q0017-badppi`, `research/q0017-badsize`); omitted property selects19 (`research/q0017-default`). These are API/bring-up checks, not crypto certification or SMP scheduling validation.
- Local checker **`research/check-patch-order.py`** verifies all17 patches and changed source equality using a temporary upstream git index. Fixtures/logs/artifacts under research are local-only and ignored. For GDB unsigned kernel pointers, mask `int(register_value) & ((1<<64)-1)`; x30/x29 may be rendered signed. Stop at a function entry for manual-call return traps, and discard each manipulated guest after API tests. All fixture QEMU guests have been stopped.


- User wants persistent progress toward iOS 16, commits for completed changes, builds through `gh` / GitHub Actions.
- Keep this file current at every milestone so another agent can resume immediately, including when usage limits interrupt a session.
- Patch 0017 committed/pushed `aa3f991`, Actions `38751507437` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38751507437. Next artifacts: xnu/out-0017, research/bt21, research/run21.log. Do not duplicate.
- Patch 0016 kernel downloaded/checksum verified: SHA256 `d06336c54baa06e0df6561a8bd7df98a9b9f7502c9381c62d1a44c045cd1ce46`, `xnu/out-0016/kernel.development.sweet`; buildtree/log `research/bt20` / `research/run20.log`. QEMU `research/q0016` (10s) prints platform expert registered, zero unknown glyphs, no panic observed BUT stalls (timer mapping still wrong until 0017). Direct actual-kernel GDB tests passed for registered instance and target/product names, including maxLength=1/0 and NULL, sentinels intact (`research/check-platform.gdb`, `research/check-platform3.log`, `research/q0016-api3`). First two fixture attempts used premature/wrong return breakpoints; discarded, corrected fixture uses start-return observation then a function-entry return trap. No phone boot yet.
- Patch 0016 CI `38750733996` PASSED (4m3s); artifacts not yet downloaded/booted. Patch 0017 prepared to fix QEMU timer fidelity BEFORE interpreting future no-panic/stall runs: actual `qemu-system-aarch64 -M virt,gic-version=3,dumpdtb=research/qemu-virt.dtb ...` timer property has virtual PPI 11 => INTID 27, while phone uses INTID 19. Kernel formerly hardcoded 19. New optional /arm-io/gic virtual-timer-intid property selects the PPI (validate exact u32 and 16..31); missing property retains phone default 19. One RO-late global drives GIC enable and sleh_irq dispatch. tools/mkadt.py emits phone19/QEMU27. Both C TUs compile (`research/timer-objs`), ADT serialize/parse checks confirm values/addresses, all 17 patches apply and match. Sandbox `research/bt19/xnu`, originals `research/pre0017`; initial local sleh compile failed due read-only exported header not updated, fixed export and BOTH recompiled successfully. CI exports normally.
- Architecture correction for next agent: CURRENT SWEET board_config does NOT define USE_APPLEARMSMP; it compiles the legacy IOCPU path, not cpu_boot_thread/IOPMGR AppleARMSMP. Existing roadmap mentions AppleARMSMP as a future approach. Do not look for gCPUIC/gAIC/gPMGR globals in the current kernel: they are absent. Determine the actual CPU-init wait after platform registration before choosing the next driver architecture.
- Patch 0016 committed/pushed as `0dcdf5c`; Actions `38750733996` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38750733996. Next artifacts: `xnu/out-0016`, `research/bt20`, `research/run20.log`.
- Patch 0016 implemented: new `iokit/Kernel/arm/SweetPlatformExpert.cpp`, arm64 source list, built-in personality in KernelConfigTables.cpp guarded by ARM64_BOARD_CONFIG_SWEET. Matches only xiaomi,sweet at score 10000, keeps IOPanicPlatform fallback for other hardware. Uses IODTPlatformExpert base initialization/power domain and createNubs CPU logical-ID annotation; overrides top-level publishing because base requires nonexistent Apple NVRAM /options. Publishes real CPU/top-level nodes, provides bounded target/product names, and registers the platform service. GIC/PMGR and arm-io child-bus drivers remain separate work. Both C++ TUs compile (`research/platform-objs`), all imports resolve against 0015/own objects, all 16 patches apply and sources match. Sandbox `research/bt19/xnu`; originals `research/pre0016`. NEXT: full Actions/QEMU; inspect CPU boot waits after the platform registers, do not equate absence of panic with successful boot.
- Patch 0015 CI `38749549779` PASSED (4m3s), checksum verified. Kernel `xnu/out-0015/kernel.development.sweet`, SHA256 `ca1b424a596c7058550ad1659080a333e7643270f019656401d80bf2b876645f`; buildtree/log `research/bt19` / `research/run19.log`. QEMU `research/q0015` (10s, zero unknown glyphs) passes trust-cache handling and machine lockdown, then panics `Unable to find driver for this platform: "xiaomi,sweet" @IOPlatformExpert.cpp:2319` (IOPanicPlatform fallback). Next concrete work: add a built-in SWEET IODTPlatformExpert personality/class; keep the fallback for mismatched platforms. No phone boot yet.
- Direct trust-cache API checks PASSED in the actual 0015 kernel under QEMU/GDB (`research/check-trustcache.gdb`, `research/check-trustcache.log`, `research/q0015-api`): runtime pointers NULL, hash/UUID queries return NOT_FOUND, typed/untyped/legacy loads return NOT_SUPPORTED, capabilities outputs zero and bounds preserved, invalid-argument cases still reject. Second PRNG check also verifies contended refresh returns immediately (`research/check-prng2.log`, `research/q0014-api2`).
- Patch 0015 committed/pushed `8f851d4`, Actions run `38749549779` running: https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779. Do not duplicate.
- Direct PRNG API checks passed in the REAL 0014 kernel under QEMU/GDB, stopped before trust-cache init (`research/check-prng.gdb`, log `research/check-prng.log`, guest `research/q0014-api`). Invoked read_random for 600 bytes (chunking and buffer sentinel intact), repeated output differed, zero-length read/write succeeded, write_random(64-byte input) succeeded, secondary generator 1 initialized and generated distinct output. QEMU log has no exceptions during these checks; guest was discarded after the tests. This tests API behavior, not a cryptographic certification or SMP scheduling.
- Patch 0015 implemented in `bsd/kern/kern_trustcache.c`: SWEET with missing Image4/AMFI marks both runtime pointers NULL and logs service unavailability. Existing static loader handles NULL. Public load APIs return KERN_NOT_SUPPORTED; hash/UUID queries return KERN_NOT_FOUND; capabilities outputs are zero with KERN_NOT_SUPPORTED. Invalid-input checks remain, and Apple paths/available-provider initialization retain existing behavior. No trust is granted. Local arm64 compile passed (`research/trustcache-objs`), all 15 patches apply and sources match. Sandbox `research/bt18/xnu`, baseline `research/pre0015`. Next: Actions/QEMU and direct unavailable-service API checks using GDB.
- Patch 0014 CI `38748543058` PASSED (4m0s), artifact checksum passed. Kernel `xnu/out-0014/kernel.development.sweet`, SHA256 `741de20c851755d333759d7e668346f3edb4f325efac4cc7c142d80d1f5ff75c`; buildtree/log `research/bt18` / `research/run18.log`. QEMU run `research/q0014` (10s, zero unknown glyphs) prints `SWEET PRNG: HMAC-SHA256 registered`, passes commpage initialization, loads vnguard policy, THEN panics `image4 interface not available @kern_trustcache.c:253`. PC=0 fault FIXED IN QEMU. No new phone boot performed.
- Next work: SWEET currently has neither AppleImage4 nor AMFI. `trust_cache_runtime_init` unconditionally requires both; unlike BCM2837, SWEET enters this startup path. Investigate an explicitly unavailable trust-cache runtime with rejected loads/no query matches while providers are absent; preserve all Apple-platform checks. Merely skipping the startup call would leave later AMFI/IMG4 dereferences unsafe. Existing load_static_trust_cache already handles trust_cache_rt == NULL.
- QEMU runner now supports `--kernel MATCHING_KERNEL --fail-on-panic`: runtime font extraction from the payload produces exact `fb.txt`, plus `result.json`; a visible panic returns 2. Baseline 0013 re-run `research/q0013-text` detects the same NULL callback panic with zero unknown glyphs. Synthetic glyph roundtrip (including literal `?`) and invalid-VA rejection passed. Screen rows remain circular, not a full log; `no_panic_observed` does not prove successful boot. README has the invocation.
- Patch 0014 committed/pushed as `be61f99`; Actions run `38748543058` is running: https://github.com/dipa-studio/ios-sweet/actions/runs/38748543058. Do not start a duplicate build.
- 2026-10-15 active: hardware photo `IMG_20261015_160033.jpg` confirms the same PC=0 instruction-fetch abort as QEMU (LR `0xfffffe0007443fe4` = read_random). Independently reproduced with kernel 0013 in `research/q0013` (8-second run); prior allocator fix works. Latest tooling commit reviewed: `8d66d2d`.
- Patch 0014 implemented: registers a built-in HMAC-SHA256 DRBG provider at EARLY_BOOT/FIRST, before commpage creation. A shared mutex serializes output/reseed across CPUs (correctness first; no per-CPU scaling yet), initgen validates CPU identities, refresh uses try-lock and the existing entropy filter/health tests. SWEET entropy accumulation and write_random now use the built-in SHA256 directly; no incomplete g_crypto_funcs table is registered. The existing bootloader-seed requirement remains enforced.
- Local validation: both PRNG translation units compile to arm64 objects in `research/prng-objs`; no SHA256 wrapper imports remain. All 14 patches apply in CI order and resulting PRNG sources match local inputs. Sandbox `research/bt17/xnu`, originals `research/pre0014`, checker `research/check-patch-order.py`. NEXT: Actions kernel build, download to `xnu/out-0014`, run the QEMU payload before requesting another phone boot. Baseline QEMU ADT/payload are `research/q0013.adt` / `research/q0013.bin`.
- 2026-10-15 08:15 QEMU EMULATION WORKS (`tools/qemu-sweet.py`, see "QEMU emulation" below). Patch 0013 VERIFIED in QEMU: boot passes kmem_crypto_init and ulock_initialize. NEXT BLOCKER (reproduced in QEMU, expected on hardware too): `pmap_create_commpages -> random() -> RandomULong -> read_random -> prng_funcs.refresh == NULL` (instruction fetch abort at pc 0, lr read_random+0x34). Nobody calls `register_and_init_prng` (closed corecrypto kext does it on Apple). Fix = patch 0014: SWEET-registered cckprng_funcs provider (osfmk/prng/prng_random.c); note random_cpu_init also panics while !prng_ready. The 07:26 hardware boot of 0013 will most likely show this same panic.
- Previous hardware boot: patch 0013 (`a3a46e2`) CI `38686345689` PASSED (3m44s), image `shim/out/shim-boot-0013.img` was temporarily booted on 2026-10-15 at 05:26 UTC: send OKAY (0.407s), boot OKAY (0.134s), total 0.546s. Superseded by the hardware/QEMU PC=0 observation and patch 0014 work above.
- Latest kernel implementation commit: `8f851d4`. Latest successful kernel CI: `38749549779` (patch 0015), https://github.com/dipa-studio/ios-sweet/actions/runs/38749549779.
- CURRENT image: `shim/out/shim-boot-0013.img`, 16,412,672 bytes, SHA256 `110d1c46aee4b60253db24b6535e9781c4cf0fd25ca2a70e9016cf81378cea25`. Kernel `xnu/out-0013/kernel.development.sweet`, SHA256 `f0b1d375995316c550ce7014ff234d8271e9b9ac2857795ceff41b76ba2cd740`, plain arm64. CI log confirms 0013 applied; checksums passed. Entry PA `0xb146b488`, kernel end PA `0xb1ff4000`.
- Current log/buildtree: `research/run17.log`, `research/bt17` (extracted, no nested .git; preferred baseline for patch 0014). Payload/ADT: `shim/out/payload-0013.bin`, `shim/out/sweet-0013.adt` (includes /defaults). Unpacked ramdisk byte-compared with payload in `shim/out/check-0013`.
- Patch-0012 original image: `shim/out/shim-boot-0012.img`, 16,412,672 bytes, SHA256 `cf4b8ec4a65a51888d71c17d09cd0831d6b761b90e2531fdb8e575c32f4fd24a`. Kernel `xnu/out-0012/kernel.development.sweet`, SHA256 `69b78f49f6459cc63a0af44e7cf73c1779ef72130ef72b12ae86c88183ffc742`; checksums passed and sweet_early_relocate symbol present. Entry PA remains `0xb146b488`, kernel end PA `0xb1ff4000`.
- Patch-0012 log/tree: `research/run16.log`, `research/bt16` (extracted, no nested .git; preferred baseline for next patch). CI log confirms 0012 applied. Payload `shim/out/payload-0012.bin`, ADT `shim/out/sweet-0012.adt`; packed ramdisk byte-compared with payload in `shim/out/check-0012`.
- Active payload command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.
- Latest observed photo: `/home/dipa/Downloads/IMG_20261015_071346.jpg` (local only). Stages 9 (kernel framebuffer VA), 10 (TTBR0 off/TLB flush), 11 (physmap table pointers) and 12 (calling pmap_bootstrap) all visible. Persistent diagnostics are VERIFIED ON HARDWARE.
- pmap.c:1987 is the assert after SecureDTLookupEntry(NULL, "/defaults", &entry). The pmap-max-asids property itself is optional; an empty /defaults uses XNU's MAX_ASIDS. Do not bypass the assertion or guess an ASID limit.
- Previous payload-only fix image: `shim/out/shim-boot-0012-defaults.img`, SHA256 `3ff61a268853c6ea7cbf284833f1346a1d791980ca366b6e1a215a86e040512b` (16,412,672 bytes). Same kernel/CI as 0012; ADT 2516 bytes (`shim/out/sweet-0012-defaults.adt`), root /defaults present with no ASID override. Payload `shim/out/payload-0012-defaults.bin`; unpacked ramdisk exactly matches payload (`shim/out/check-0012-defaults`). This boot reached the allocator crypto NULL-pointer fault below.
- Latest hardware photo: `/home/dipa/Downloads/IMG_20261015_071608.jpg` (local only). Normal serial framebuffer console works. VM bootstrap/zone initialization, logging, scheduler, IPC, KDP and ulock_initialize print before the kmem_crypto_init data abort. gPanicBase warnings are expected because PLATFORM_PANIC_LOG_DISABLED is configured, and are not the faulting call.
- Faulting instruction: `ldr x0, [x8, #0x150]` in crypto_random_kmem_ctx_size; x8 = NULL g_crypto_funcs. Source: libkern/crypto/corecrypto_rand.c and osfmk/vm/vm_kern.c:2448. rand.h explicitly permits NON-cryptographic kmem RNGs, but requires no locking in generation and context size <=256. Do not substitute read_random here: the global PRNG provider is also unregistered and kmem generation must remain lock-free. early_random may seed contexts during single-CPU bootstrap; it uses the built-in HMAC-SHA256 DRBG with the host-generated ADT seed.
- Patch 0013 keeps the replacement entirely private to vm_kern.c: SplitMix64 state is 8 bytes per CPU/sizeclass, initialized using early_random. Uniform selection uses rejection sampling to avoid modulo bias. Other platforms retain the original corecrypto calls; SWEET's generic crypto APIs/registration remain untouched. Reference: https://prng.di.unimi.it/splitmix64.c (Sebastiano Vigna, public domain).
- Validation: vm_kern.c compiles to arm64 (`research/kmem-rng-objs`, using `research/run16.log` + `research/bt16`). Undefined symbols include early_random and NO crypto_random_* references. All 13 patches apply in CI order and match the checked source. Original saved as `research/vm_kern.pre0013.c`.
- RNG host checks: extracted actual new helper in `research/kmem-rng-check.c`; 16,384 outputs match the author's downloaded reference (`research/splitmix64-reference.c`), 147,456 bounded outputs satisfy their limits (including 1 and UINT64_MAX), and a forced rejection advances correctly. Full kernel crypto services and the registered kernel PRNG provider remain future work; this patch only supplies the allocator RNG contract.
- Patch-0011 artifacts: kernel `xnu/out-0011/kernel.development.sweet`, log `research/run15.log`, extracted buildtree `research/bt15` (no nested .git). CI log confirms patch 0011 applied; artifact checksums passed. Kernel is plain arm64, entry VA `0xfffffe000746b488` -> PA `0xb146b488`, kernel end PA still `0xb1ff4000`.
- Patch-0011 image: 16,412,672 bytes, SHA256 `29ad5cbfc752473de4af2c471a24a8b34f92da4bff5afec65c614b90cd3ad53a`. Kernel SHA256 `8ac3a956894b09f7bd0d890de8c5de38c65513287feb1e1bcd12db8ca772ee5c`. Payload/ADT in `shim/out/payload-0011.bin`, `shim/out/sweet-0011.adt`. Header unpacked/checked in `shim/out/check-0011`.
- First patch-0011 attempt timed out waiting for FASTBOOT; superseded by the successful send/boot recorded above. Do not repeat the boot before the user reports the current screen.
- Patch-0011 photo: `/home/dipa/Downloads/IMG_20261015_070218.jpg` (local only). Visible stages 1-8 and old red shim text; entry PA B146B488, boot args PA B1FF8000 / top B1FFC000. No evidence yet locating execution after stage 8.
- Patch-0012 sandbox: `research/bt15/xnu` (NO nested .git). Proposed permanent debug VA: VM_MIN_KERNEL_ADDRESS + ARM_TT_L2_SIZE, in the reserved gap below gVirtBase and above low globals; map the same PA framebuffer as Normal-NC in the final TTBR1 before arm_vm_physmap_init changes phystokv(). Keep the early panic sink until normal kprintf startup.
- Patch 0012 validation: all 4 changed C translation units compiled to arm64 objects in `research/post-ttbr0-objs`; internal header export added to osfmk/arm64/Makefile and recreated locally in EXPORT_HDRS for pe_serial.c. All 12 patches apply in CI order and match all 6 edited files. Baselines are saved under `research/pre0012/`.
- Actual mapping-helper host model (`research/early-map-check.c`, barrier stubbed only for host compilation) confirms: VA `0xfffffe0002000000`, L1 index 2016, L2 index 1; descriptor `0x006000009c000605` = framebuffer PA, Normal-NC, outer-shareable, EL1 RW, PXN+UXN. All other L2 entries preserved. The gap is excluded by ARM_LARGE_MEMORY's pmap_virtual_region(0).
- Next boot command line MUST add `-enable_kprintf_spam`: DEVELOPMENT disables kprintf_output by default even when DB_KPRT is set (`pexpert/arm/pe_kprintf.c`). Planned command line: `debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam`.

### Patch 0012 screen legend (after original stages 1-8)
- 9: kernel framebuffer VA live; 10: TTBR0 off / TLB flushed; 11: physmap pointers rebound.
- 12: calling pmap_bootstrap; 13: pmap_bootstrap returned; 14: early I/O page tables ready; 15: arm_vm_init returned.
- 16: calling serial_init; 17: fbcon config read / mapping; 18: fbcon mapping returned; 19: serial_init returned; 20: kprintf startup complete.
- Normal serial initialization clears the screen, so earlier stages may disappear before 19. If serial exists, early console disables after 20; otherwise early panic output stays enabled.
- Local source sandbox: `research/bt13/xnu` (git baseline `623b060`, patches 0001-0008 already in baseline; uncommitted export edits correspond to patch 0009). Preserve those edits when producing patch 0010.
- Previous compile log/tree: `research/run13.log`, `research/bt13`; previous kernel: `xnu/out/kernel.development.sweet`. New successful log/tree: `research/run14.log`, `research/bt14`; new kernel: `xnu/out-0010/kernel.development.sweet`.
- Current device access: patch-0012 image was temporarily started from FASTBOOT; no adb connection is expected. Never flash partitions for bring-up; use `fastboot boot` with the shim image.
- Patch `0010` lives in `xnu/patches/0010-sweet-early-framebuffer-debug.patch`. Its exact compiled sources are under `research/bt13/xnu`; generated objects are in `research/early-objs`.
- Local checks passed: all 5 changed/new translation units compiled to arm64 Mach-O objects; new console only imports `_doprnt` and `iso_font` (both exist in the previous kernel). All 10 patches applied to a temporary upstream git index in CI order, and all 7 resulting changed source files matched the local compile inputs.
- Reproduce changed-file compilation: `XNU_CC_OBJDIR="$PWD/research/early-objs" python3 tools/xnu-cc.py research/run13.log research/bt13 arm_init.c arm_vm_init.c kern/debug.c arm64/start.s osfmk/arm64/sweet_early.c --per-file` (create the output directory first). The helper now accepts explicit new source paths absent from the old artifact's Makefiles and rejects empty selections.
- Device command result: `adb reboot bootloader`, then `timeout 30s fastboot boot shim/out/shim-boot-0010.img`: send OKAY (16028 KB), boot OKAY, total 0.541s. This confirms bootloader acceptance only, not XNU progress.
- The successful boot above was on 2026-10-14. On 2026-10-15, `timeout 45s fastboot boot ...` timed out waiting for a device; no image was sent. Boot image SHA256 rechecked and unchanged. No new build is needed to repeat the trial.
- Earlier retry: `timeout 90s fastboot boot shim/out/shim-boot-0010.img` timed out (exit 124). This is superseded by the successful 2026-10-15 repeat boot recorded above; do not repeat it until the user reports the screen.
- User observation confirms MMU-on C entry, platform expert, CPU topology/bootstrap, startup bootstrap and cpu_init all complete. Failure is within arm_vm_physmap_init (non-XNU_MONITOR branch), before stage 8 / TTBR0 teardown. Old red shim text remains behind the early console; this is expected because only written rows are cleared.
- New edit/compile sandbox is `research/bt14/xnu` (extracted artifact, NO nested .git; `git diff` there would act on the parent project). Use a saved baseline file / generated unified diff, or explicitly initialize a local baseline before editing. `research/bt13/xnu` does have its own baseline git repo.
- Exact user-reported panic: `arm_vm_init.c:1606 Assertion failed: (temp_ptov_table[ptov_index - 1].va + temp_ptov_table[ptov_index - 1].len) <= physmap_end`.
- Root cause: MacOSX build sets `ARM_LARGE_MEMORY=1`; `XNU_MONITOR` is off. Block alignment in arm_vm_physmap_slide can add gaps, but the non-PPL large-memory physmap_end omitted the padding already present in the small-memory branch. Patch 0011 reserves PTOV_TABLE_SIZE*ARM_TT_TWIG_SIZE (8*32MB) in both the aperture bound and its L1 allocation; monitor/PPL builds retain zero padding. The assertion is preserved.
- Validation: `arm_vm_init.c` compiled to an arm64 object using `research/run14.log` + `research/bt14` (object in `research/physmap-objs`). All 11 patches apply in CI order and produce exactly that source. Host harness `research/physmap-check.c` extracts the real XNU slide function with page-table-write stubs: all 65,536 page-aligned slides within 1GB checked against the current kernel memory layout; old bound fails 65,504 cases, padded bound fails zero; worst overrun 0x1ffc000 bytes. Baseline source saved as `research/arm_vm_init.pre0011.c`.
- CI: https://github.com/dipa-studio/ios-sweet/actions/runs/38638702083 (success; artifacts and full log downloaded).
- New image: `shim/out/shim-boot-0010.img` (16,412,672 bytes, SHA256 `ed2c270e0081bad5ff517be415f9bfe8805463aea7866732203fa97ac737e64e`). Previous image preserved as `shim/out/shim-boot-pre0010.img`.
- New kernel SHA256: `3ee05270cc291c49589a101678f904b1b69cb2f2575e05398bce8a4e052f409a`. Artifact checksums passed; arm64 (not arm64e), early-console symbols present. Payload entry VA `0xfffffe000746a488` -> PA `0xb146a488`; kernel end PA `0xb1ff4000`. Command line remains `debug=0xc serial=3 cpus=1 keepsyms=1`.

### Patch 0010 screen legend
- Bottom-left white 64x32 tile: assembly entered `start_first_cpu`, before page tables/MMU.
- Text `SWEET EARLY 1`: entered `arm_init` with MMU on; 2: platform expert done; 3: CPU topology done; 4: CPU bootstrap done; 5: startup bootstrap done; 6: CPU init done; 7: entering `arm_vm_init`; 8: leaving bootstrap TTBR0.
- `SWEET EARLY PANIC:` prints a copy of panic arguments before normal panic handling needs per-CPU/thread state.
- In patches 0010/0011 the console disabled before TTBR0 invalidation; patch 0012 replaces that with a persistent kernel VA alias and diagnostics through normal serial/kprintf startup (see its legend above).
- Screen contents require a physical observation from the user: adb cannot capture a framebuffer after Android has been replaced by a bare-metal kernel.

## QEMU emulation (2026-10-15)
- `tools/mkadt.py OUT.adt --qemu` = same ADT with QEMU virt GICD 0x08000000 / GICR 0x080a0000 / CNTFRQ 62.5 MHz.
- `tools/qemu-sweet.py PAYLOAD OUTDIR [--secs N] [--hmp "x /8gx ADDR"] [--gdb]`: host-side copy of shim/loader.c
  (segments + ADT + boot_args at their PAs, 6-instruction stub sets x0 and jumps), `-M virt,gic-version=3 -cpu cortex-a76`
  (same ID_AA64MMFR0 as Kryo 470), 4G RAM so 0x9c000000 fb and 0xb0000000 kernel are plain RAM.
  Outputs `fb.png` (the screen), `regs.txt`, `qemu.log` (exceptions with ESR/FAR/ELR). `--gdb` halts with a stub on :1234
  (system `gdb` + `set architecture aarch64`, `hbreak *VA` works with the MMU on).
- Not emulated: Qualcomm XPUs, ABL, real panel, PSCI conduit (QEMU virt uses hvc). Hardware still decides those.
- Example: `python3 tools/mkadt.py /tmp/q.adt --qemu && python3 tools/mkpayload.py xnu/out-0013/kernel.development.sweet /tmp/q.adt /tmp/pq.bin --cmdline 'debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam' && python3 tools/qemu-sweet.py /tmp/pq.bin /tmp/q`

## Layout
- `backup/`  partition dumps + full sdb..sdf LUNs, `SHA256SUMS` (all verified on-device == local)
- `dtb/`     live FDT (from OrangeFox), PixelOS boot.img dtb, dtbo, dts versions
- `shim/`    bare-metal boot shim (`./build.sh` -> `out/shim-boot.img`)
- `research/` mainline sm7150 dts, XNU pe_fiq.c etc, PocketDarwin patches
- `tools/unpack_bootv2.py`

## Device access
- No root in PixelOS 17 (user build, adb root disabled). Root = `fastboot boot recovery/recovery.img` (OrangeFox R12.0_2, temp boot, not flashed).
- `fastboot boot` works for stock boot.img, OrangeFox, and our shim.
- Shim resets itself via PSCI SYSTEM_RESET; IMEM restart_reason 0x77665500 is seen
  (bootreason=bootloader) but ABL still boots Android, so it does not stop in fastboot.

## Hardware facts (live DT + shim measurements)
- Framebuffer (ABL cont splash): 0x9c000000, 1080x2400, stride 4320, a8r8g8b8, panel is DSC *video* mode (no kick needed).
- RAM: 0x80000000+2G, 0x100000000+0xfcc00000. Live reserved-memory = PixelOS base dtb + sweet dtbo fixups.
- GICv3: GICD 0x17a00000, GICR 0x17a60000 (stride 0x20000, 8 PEs). GICD_TYPER 0x007B041D: SecurityExtn=1 (DS=0).
  ABL leaves GICD_CTLR = 0x10 (ARE_NS on, groups off). Writing 0x13 reads back 0x12: EnableGrp1A (bit1) is the one that matters.
- GIC Group 1 VERIFIED (shim 2c): vtimer INTID 19 = 30 IRQs/300ms, ptimer INTID 18 = 30, SGI 1 to self = 10/10.
  ICC_SRE=1 already, ICC_CTLR 0x8440, priority/enable writes stick. GICR_IGROUPR0 and GICD_IGROUPRn read 0 from NS
  even though Group 1 delivery works (RAZ in NS view) - do not use them as a health check.
  INTID 28 shows pending constantly (unknown PPI 12).
- Timer 19.2 MHz. Qualcomm PPI numbering: secure-phys/phys/virt/hyp = PPI 1/2/3/0 -> vtimer INTID 19, ptimer 18 (NOT 27/30).
- PSCI 1.1 via SMC, SMCCC 1.1. CPU_ON ok; SYSTEM_SUSPEND and SYSTEM_RESET2 unsupported.
- SMP: CPU_ON works for all 7 secondaries (MPIDR 0x81000n00).
- Entry EL1, MMU off, x0 = DTB (magic ok). ID_AA64MMFR0 = ...101122: 16K granule YES, 4K YES.
- No serial console: debug UART SE is in SPI mode on sweet. Screen is the only debug channel.

## XNU implications
- XNU GICv3 path (pexpert/arm/pe_fiq.c, VMAPPLE) puts the timer (PPI 27) in Group 0 = FIQ. With SecurityExtn=1,
  Group 0 is secure -> impossible from NS EL1. Need: Group 1 IRQ, ICC_IGRPEN1, INTID 19, and the timer handled in the IRQ path.
- XNU VMAPPLE PSCI uses `hvc`; sweet needs `smc`.
- PocketDarwin NonAppleGenericCpu.patch only swaps -mcpu=apple-h7 for -march=armv8-a.

## Milestone 3 (2026-10-14): 16K MMU verified
- ABL loads the Image at 0x80080000 (base 0x80000000 + 0x80000) regardless of text_offset=0.
- 16K granule, T0SZ=28 (L2 start, 32MB blocks), MAIR 0x44ff00, TCR 0x1409CB51C, PARange=2 (40-bit PA).
- Only own image pages WB (Qualcomm XPUs: never map carve-outs cacheable); fb Normal-NC; rest Device.
- AT S1E1R checks all as expected; unmapped -> translation fault L2.
- Fill fb: 110 ms (MMU off) -> 3.5 ms (NC). Memory loop 70 ms -> 0.7 ms. vtimer + SGI IRQs still fine with MMU on.

## XNU loader design notes (xnu-8796)
- Entry: `_start` -> `start_first_cpu`, x0 = boot_args (PA), MMU off, EL1. boot_args: Revision/Version 2,
  virtBase/physBase/memSize/topOfKernelData, Boot_Video (fb 0x9c000000, rowBytes 4320, 1080x2400, depth 32),
  deviceTreeP/Length (ADT), CommandLine[608], bootFlags, memSizeActual.
- start.s maps [kernel mach header .. physBase+memSize) with cacheable BLOCKS. On Qualcomm every XPU carve-out
  must therefore lie below the kernel: use physBase = 0xb0000000 (above ramdump_fb 0xaf000000+16M,
  cdsp_sec, qseecom), end before rmtfs 0xfde01000 -> memSize ~0x4d000000 for bring-up.
- Base ADT: iPhone 8 d20ap DeviceTree from iOS 16.7.16 IPSW (tools/remotezip.py + tools/adt.py; LZFSE payload).
  Template values are empty: the loader must fill chosen/*, memory-map, cpu*/reg etc. like iBoot.
- XNU build: GitHub Actions (dipa-studio/ios-sweet, xnu.yml) via blacktop/darwin-xnu-build, MACOS_VERSION=13.5.
  New-clang fixes in xnu/patches; Xcode 16 iig is incompatible (IORPC.kernelContent) -> macos-14 runner, oldest Xcode.

## Kernel architecture plan (SWEET machine config)
- First stock build (VMAPPLE) is arm64e (PAC). Kryo 470 = ARMv8.2, no PAC -> SWEET must build plain arm64
  (HAS_APPLE_PAC is only defined for __arm64e__, so arm64 drops PAC automatically).
- Template: VMAPPLE (16K pages, GICv3 code in pe_fiq.c) minus APPLEVIRTUALPLATFORM hypercalls/paravirt PAC,
  plus BCM2837 (generic ARM: no APPLE_ARM64_ARCH_FAMILY Apple sysregs). Do not link the KDK lib<cfg>.os.*.a.
- Timer: XNU expects it on FIQ (sleh_fiq -> rtclock_intr). SWEET: GIC Group 1, so sleh_irq must ack ICC_IAR1,
  route INTID 19 to the same timer path, SGIs to cpu_signal_handler, EOI via ICC_EOIR1.
- SMP/interrupts: open-source AppleARMSMP (USE_APPLEARMSMP) needs an IOInterruptController (AIC role) and an
  IOPMGR (CPU power -> PSCI CPU_ON via SMC). Plan: built-in IOKit classes (SweetGIC, SweetPMGR, platform
  expert) compiled into the kernel and matched via iokit/KernelConfigTables.cpp -> no closed kexts needed.
- Debug: xnu patch 0003 sweet-fbcon = kprintf drawn on the framebuffer (ADT node "sweet-fbcon").
- ADT /arm-io ranges must not map to parent 0 (pe_arm_get_soc_base_phys()==0 disables serial): use parent 0x1000000.

## Status 2026-10-14 late: first XNU boot attempt
- SWEET kernel builds (CI run 38635343732, patches 0001-0009). Verified offline: arm64, no PAC, no >v8.2 code,
  70300 classic relocs all in range (slide 0 = no loader work), entry = __start.
- Boot: shim loader worked (initrd 0x846F0000-0x855FE3E0, BOOTARG 0xB1FF8000, JUMP 0xB146A488) but screen stayed
  red -> xnu died/hung before serial_init (fbcon). kprintf is a no-op before STARTUP_SUB_KPRINTF.
- Historical next-step plan (patch 0010, now implemented and built; see active handoff above): early fb debug channel
  1. start.s start_first_cpu (after mov x20,x0 / mov x21,#0): PA marker band (MMU off, direct store to 0x9c000000).
  2. start.s after both create_bootstrap_mapping calls: add ONE block entry to the existing V=P L2 table
     (x25 + 2*PGBYTES; do NOT call create_bootstrap_mapping again: fb and RAM share L1 entry 0, it would replace
     the L2 table). Entry = TYPE_BLOCK|VALID|SH(OUTER)|ATTRINDX(CACHE_ATTRINDX_WRITECOMB=1)|AF|PNX|NX|0x9c000000,
     index = (va & ARM_TT_L2_INDEX_MASK) >> ARM_TT_L2_SHIFT.
  3. new osfmk/arm64/sweet_early.c (+files.arm64 entry): sweet_early_mark(n) colored bands at screen bottom and
     sweet_early_putc using iso_font via VA=PA while the bootstrap TTBR0 is live; disable before
     arm_vm_init's set_mmu_ttb(invalid_ttep) (arm_vm_init.c:2148).
  4. markers in arm_init after PE_init_platform, ml_parse_cpu_topology, cpu_bootstrap, kernel_startup_bootstrap,
     cpu_init, before arm_vm_init.
  5. panic hook at top of panic_trap_to_debugger: va_copy + _doprnt(fmt, &copy, sweet_early_putc, 16).
  Verify with tools/xnu-cc.py (compile+symbols) and patch-order simulation before the single CI run.
