# MARBLE diagnostic RAMDisk root

Physical run (user observation, 2026-10-22), source
899bfb1f59c66e9091d5bd16376899ac66aec219, Actions 39728864936:

- RAMDisk discovery PASS
- md0 creation PASS
- BSD root md0 PASS
- setRootMedia entered PASS
- publishHiddenMedia FAIL: missing IOMedia class assertion at IOService.cpp:5130

Kernel SHA256: 55f32622881732e32aa488283930d3c678425d1c005df25f5a1d974535f22026
Init/root: f39a3fad30988599af8ed3c2d4d882d21f59f6478113bff8edef458d1476b40b
Payload: fa98545b33b3ec474aeba86e51c06a416160039a584309c81d0973d017bf5d45
Boot: 54f4375a0e0d83eb48ccdd4e736e5b977e670c34e92e95b78cae4d8e0b88a277

The new MARBLE-only guard returns immediately after a missing IOMedia lookup,
before the existing assertion. SWEET behavior is preserved. This correction's
physical behavior remains untested; mockfs mount and PID 1 are not yet proven.

## Root format and source audit

Pinned XNU is xnu-8796.141.3, with patches 0001..0081 replayed and 0082 applied
with `git apply --whitespace=error --check` followed by strict application.
`config/MASTER.arm64.marble` FILESYS_BASE includes mockfs; generated MARBLE BSD
Makefile contains mockfs_fsnode/vfsops/vnops and memdev objects. memdev.c is
standard in bsd/conf/files. IOKitBSDInit discovers `/chosen/memory-map/RAMDisk`,
calls mdevadd with the virtual address (4K page units), and `rd=md0` selects
mdevlookup(0), bypassing IOMedia matching. It still calls setRootMedia.

Like SWEET, MARBLE supplies no IOStorageFamily/IOBlockStorageDriver/IOMedia.
0082 extends only the two existing absent-class compatibility guards in
IOService.cpp to SWEET || MARBLE: setRootMedia's block-driver lookup and
publishHiddenMedia's later IOMedia handling. The new early MARBLE return fixes
the assertion preceding that later handling. Other SWEET guards, notably UFS, are
unchanged. Patch 0024 is already board-independent: virtual memory devices
use device I/O rather than treating a virtual page number as physical memory.
Its physical-page conversion stays 4K independent of kernel PAGE_SHIFT.

mockfs_check_macho reads the backing device's first sector. The root is the
**raw signed static Mach-O**, not HFS, APFS, cpio or a partition image. mockfs
creates its own root/dev/executable nodes, aliases sbin to the root directory,
and provides the backing bytes as /sbin/launchd. devfs supplies /dev/console.
No UFS access, rootrw, storage-write support or hardware changes are added.

## Reproduce

From the repository root:

```sh
mkdir -p shim/out/marble-xnu
clang -target arm64-apple-ios16.0 -DMARBLE_INIT -c tools/sweet-init.S \
  -o shim/out/marble-xnu/marble-init.o
python3 tools/mkinit.py shim/out/marble-xnu/marble-init.o \
  shim/out/marble-xnu/marble-init
tools/marble-ci-build.sh --ramdisk shim/out/marble-xnu/marble-init \
  --cmdline-extra 'rd=md0' 'MARBLE: bring up static PID 1 on mockfs RAMDisk'
```

The init is deterministic, 16635 bytes, arm64 (not arm64e), LC_UNIXTHREAD entry,
no interpreter/dylib commands, an ad-hoc SHA256 signature and no relocations.
It aligns the user stack, opens /dev/console, prints
`*** MARBLE USERSPACE: PID 1 RUNNING ***`, reports getpid (one digit, PID 1
expected), and loops on select's five-second timeout and a console heartbeat.
There is no dyld, shared cache, framework or disk dependency. Without
MARBLE_INIT the existing SWEET text and machine code remain identical.

The helper's default command line and rootless behavior remain unchanged.
Options are passed as array arguments (including paths with spaces). With
this diagnostic the exact command line is:

```
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=md0
```

The Android boot-v4 generic ramdisk carries the shim's SWEETXNU payload plus
MRBLXNU1 locator footer. The XNU root is a separate segment **inside** that
payload. mkpayload rounds it to 16K, appends after every kernel segment,
advances kernel_end and inserts two little-endian u64 values (PA, padded
size) in the payload's ADT. The original input ADT is intentionally unmodified.
The shim copies/zero-fills the root segment, then places ADT, aligned boot_args
and topOfKernelData after it. The sparse mapper already maps this entire owned
tail WB/XN; the 160-page early allocator starts after the enlarged top.

`tools/marble-ramdisk-audit.py KERNEL PAYLOAD INIT` checks the actual packed ADT,
root bytes, segment placement, command line, Mach-O commands, nonoverlap and
bounds, then invokes the existing sparse audit with padded RAMDisk size.
The helper runs it on the exact downloaded kernel before building the shim.
`marble-bootstrap-audit.py --ramdisk-size N` also supports standalone checks;
N is the unpadded root file size. Without the option its calculation is unchanged.

## Failure boundaries

Expected physical order:

```
MARBLE ROOT: RAMDisk property present
Added memory device md0
BSD root: md0, major 1, minor 0
MARBLE ROOT: setRootMedia begin
MARBLE ROOT: no IOMedia class, skip hidden-media publish
MARBLE ROOT: setRootMedia complete
MARBLE ROOT: mockfs mount begin
MARBLE ROOT: mockfs mount result 0
load_init_program: attempting to load /sbin/launchd
MARBLE ROOT: PID 1 codesigning result 0
*** MARBLE USERSPACE: PID 1 RUNNING ***
PID 1 ***
MARBLE init: still alive
```

A missing RAMDisk property or configured-memory-device panic identifies discovery
or selection. setRootMedia brackets identify that compatibility boundary.
mockfs reports Mach-O probe failure and final mount errno. Existing
load_init_program attempt/failure messages and its final errno panic identify
exec. The new PID 1 signature-result message identifies process_signature's
return status; earlier Mach-O/signature-load failures can instead return through
exec's errno path. Codesign page-validation failures may occur on first page-in
and retain XNU's normal code-signing failure diagnostics. No signing enforcement
is disabled. Console-open failure deliberately executes `brk #0x434f` in this
MARBLE-only init, with errno still in x0; the init-death exception PC can be
matched to `llvm-objdump -d marble-init.o` plus executable entry 0x100000400.
Thus a trap there means exec reached userspace but opening the console failed.
A visible banner proves console open and userspace execution; heartbeat proves
continued execution. Timing and physical behavior require the manual boot.

## Local validation

All four changed XNU units compile to arm64 Mach-O using actual generated
XNU headers: IOService.cpp, IOKitBSDInit.cpp, mockfs_vfsops.c, kern_exec.c.
SWEET before/after preprocessing differs only in __LINE__ literals and generated
identifiers containing those line numbers. Default SWEET init bytes are identical.
Existing 0082 content preceding these appended root diagnostics is byte-identical,
so sparse map/allocator/MMU/OSLAR/CNTV/GIC/CPU/platform/framebuffer fixes remain.
Timer27/SGI1/Group1 and skipped GICR group/priority MMIO are rechecked from
MARBLE preprocessing; linked code is scanned for physical CNTP instructions.
The exact new linked kernel/payload are re-audited after CI.

No physical phone commands are part of this workflow. Boot manually only:

```sh
fastboot boot ~/ios-marble/shim/out/marble-xnu/latest-marble-xnu.img
```

## Missing-IOMedia correction audit

setRootMedia finds no IOBlockStorageDriver class, sets root NULL, skips its
provider loop, records NULL as root parent and calls publishHiddenMedia(NULL)
when unhide is true. Missing IOMedia now logs and returns before locks, instance
iteration or assertion; setRootMedia then returns. Existing SWEET compatibility
and the later missing-class guard are retained. IOFindBSDRoot's md0 branch
bypasses IOMedia matching. vfs_mountroot and mockfs use vnode/device operations;
no additional immediately reached storage-family metaclass assertion was found.

Validation: full replay 0001..0081, strict 0082, real-header MARBLE IOService.cpp
compile; preprocessing proves return before assertion. Object has CBZ after
getMetaClassWithName to the log/return path. Non-MARBLE assertion conditional
is unchanged (SWEET already excluded it). SWEET preprocessing is equivalent
except shifted __LINE__ values; raw byte identity was not obtained. Only this
six-line guard changes generated XNU source; mockfs, rd=md0, init/root bytes,
bootstrap, timer27/SGI1/GIC protections remain unchanged. The helper rebuilds
the known static test init after CI before packaging. Exact linked kernel and
payload checks are repeated after CI; no physical phone command is automated.

## Verified correction build

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
