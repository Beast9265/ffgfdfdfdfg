# MARBLE Stage-0 Diagnostic Shim

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

## Scope and hardware facts

Target: POCO F5 / Redmi Note 12 Turbo (`marble`, Qualcomm SM7475).
The values below are authoritative user-supplied facts, encoded in the board
configuration where needed. Latest physical observations are recorded below; earlier results are historical.

| Component | MARBLE values |
| --- | --- |
| Retained ABL framebuffer | PA `0xb8000000`, reservation `0x02b00000`, 1080×2400, 32 bpp, expected stride 4320 bytes |
| GIC distributor | `0x17100000`, size `0x10000` |
| GIC redistributors | `0x17180000`, size `0x200000`, stride `0x40000` |
| Virtual timer | Live DT PPI 11 / INTID 27; Android boot log reports 19.20 MHz (virt/virt) |
| PSCI | `arm,psci-1.0`, `smc` |
| UFS host / PHY | `0x01d84000` (size `0x3000`) / `0x01d80000` |
| Userdata GPT name | `userdata` |
| Future XNU RAM window | base `0x840000000`, size `0x100000000` |
| Restart reason | IMEM `0x146aa65c`; existing bootloader-request value `0x77665500` is unverified on MARBLE |
| Stock images | boot header v4; vendor_boot header v4 with 4096-byte pages; DTB supplied by vendor_boot |

## Build and behavior

```sh
BOARD=marble shim/build.sh
# SWEET compile-only regression check, without its private DTB:
SHIM_RAW_ONLY=1 BOARD=sweet shim/build.sh
```

Requires GNU AArch64 GCC/binutils and GNU awk. MARBLE outputs
`shim/out/marble/{Image,shim.elf}` only. Payload arguments are rejected.
SWEET remains the default with its existing v2 packaging and XNU loader.
No workflow, kernel patch or ADT generator changes are needed for stage 0.

MARBLE draws the existing console into ABL's splash buffer, reports PSCI and
SMCCC versions/reset support, tests GIC Group 1 virtual-timer interrupts and
SGI-to-self, then pauses 20 seconds for a photo. The UFS page runs with the MMU
off and stays visible for 40 seconds. It preserves every existing UFS readiness,
idle-doorbell and transfer-list readback check. MARBLE first reads retained fDeviceInit with READ_FLAG only as described
above, then only TEST UNIT READY (0x00),
READ CAPACITY(10) (0x25), and READ(10) (0x28) are sent, on LUN 0. Host-controller
register writes and DMA into shim-owned buffers are required; no storage writes
are issued. No PHY, GPU, touch, Wi-Fi, audio or modem initialization occurs.

The final page enables the existing 16K MMU design. The low 8 GiB stays mapped;
MARBLE additionally maps `[0x840000000, 0x940000000)` as Device, execute-never.
Only shim image pages become write-back cacheable. Framebuffer mappings are
Normal-NC for `FB_VISIBLE_SIZE = FB_STRIDE * FB_H` (10,368,000 bytes),
statically checked against the reservation and rounded to 32 MiB block boundaries.
Only the block at `0xb8000000` becomes Normal-NC; `0xba000000` stays Device. `AT S1E1R` checks both ends of
the high window without accessing its RAM. The 12 GiB hole remains unmapped.
MARBLE `now()` uses `cntvct_el0`, matching the virtual timer; SWEET keeps
`cntpct_el0`. The UFS probe retains its existing `cntvct_el0` behavior.
Reset follows after 40 seconds using only PSCI_SYSTEM_RESET: MARBLE writes
neither IMEM_RESTART_REASON nor PSHOLD. The IMEM address is verified, but the
bootloader-request value is unverified on MARBLE. If reset returns, the shim
executes WFE forever. XNU and secondary CPU code are excluded.

## Deterministic boot-v4 packaging

MARBLE requires Android boot header v4 with fixed 4096-byte pages, a generic
ramdisk and DTB/vendor ramdisks supplied separately by installed vendor_boot.
SWEET's existing v2 mkbootimg command is unsuitable and remains unchanged.
The separate standard-library tool is `tools/mkbootv4_marble.py`.

```sh
python3 tools/mkbootv4_marble.py inspect marble-boot-backup-clean/boot_a.img
python3 tools/mkbootv4_marble.py control marble-boot-backup-clean/boot_a.img shim/out/marble/control-stock-v4.img
python3 tools/mkbootv4_marble.py inspect shim/out/marble/control-stock-v4.img
python3 tools/mkbootv4_marble.py repack marble-boot-backup-clean/boot_a.img shim/out/marble/Image shim/out/marble/shim-marble-stage0.img
python3 tools/mkbootv4_marble.py inspect shim/out/marble/shim-marble-stage0.img
python3 -m unittest discover -s tools -p test_mkbootv4_marble.py -v
```

Outputs must not already exist (exclusive creation protects existing files).
Treat generated images as private artifacts: they contain the stock ramdisk.
The parser checks exact magic/version/header size and uint64-bounded offsets,
nonzero uint32 kernel length, component bounds, nonoverlap and required padding.
It reads the 1584-byte little-endian header at offset zero; it never searches
for component magic. All valid header bytes except kernel size are retained,
including packed OS version/patch, reserved words and the full cmdline field.
Repacking accepts only signature_size=0; it never invents or reuses a signature.
Inspection also supports bounded nonzero signature components.
Each component is padded to 4096 bytes with zeroes. Bytes after the calculated
structure (partition padding/AVB footer) are excluded. Post-write verification
uses a separate byte-slice/page-count decoder and checks exact header, component
lengths/hashes, zero format padding and exact output length.

Offline validation (2026-10-21): raw MARBLE build passed; control kernel and
ramdisk hashes matched stock and the entire 48,185,344-byte boot-v4 region was
byte-identical. The 201,326,592-byte stock partition's 153,141,248 trailing bytes
were excluded. MARBLE output is 3,731,456 bytes, kernel 180224 bytes at 4096,
ramdisk 3544657 bytes at 184320; both extracted component hashes matched their
inputs. Header: v4, size 1584, OS 17.0.0, patch 2026-10, empty cmdline,
signature size zero. Synthetic rejection/corruption and determinism tests pass.

`shim/out/marble/shim-marble-stage0.img` is intended only for a later reviewed
temporary `fastboot boot`, **not flashing**. Installed vendor_boot remains
untouched; no replacement is generated. No partition is modified. No device
commands or GitHub Actions were run. The first physical boot was accepted and reached the GIC priority-window abort
described below; the corrected image has not been physically tested.

## Remaining hardware unknowns

The first physical boot establishes boot-v4 acceptance, framebuffer output and
shim execution. Exact ABL Image placement, entry cache state, DTB handoff and
non-overlapping reserved-memory ranges still need confirmation. Confirm shim DMA buffers are accessible to the retained
UFS controller (including address-width/IOMMU constraints), LUN 0 uses 4096-byte
blocks, retained framebuffer pixel order/stride, GIC security state and reset
behavior. The existing probe assumes 4 KiB UFS blocks; its results are diagnostic,
not confirmation of filesystem or GPT validity. Preserve vendor_boot unchanged.
Keep original images, DTBs and device identifiers private and outside git.

## Physical test procedure (after packaging review)

1. Review the diff and privately verify the packaging inputs above. Back up
   original images; establish a known working way to return to the bootloader.
2. Prepare and inspect a temporary v4 boot image containing only the diagnostic
   Image. Reuse the installed vendor_boot; do not replace it or flash partitions.
3. With explicit user authorization, temporarily boot the reviewed image.
   No device command was run as part of this implementation.
4. Film all three console pages. Expect CNTFRQ `0x124f800`, roughly 30 virtual
   timer IRQs and 10 SGI IRQs, with zero unexpected IRQs. Record actual counts,
   PSCI results, UFS status, GPT output, and any blue panic ESR/ELR/FAR/stage.
5. Expect MMU rc zero; PAR bit 0 clear for image/framebuffer/GIC/high-window
   endpoints and set for the hole. Record reset behavior and verify Android
   still boots. Do not infer storage accessibility from translation alone.

## Local validation

Both raw builds pass without compiler warnings. C objects contain zero ABS64
relocations; both linked ELFs have no relocations. The sole start.o ABS64 is
the expected Image header size. The AArch64 little-endian Image is 180224 bytes
(`0x2c000`), with ARM64 magic and matching image_size. Current MARBLE SHA256:
`d6f4da538a362e9f23c28dc6a4bc84486a0579aa766e25123353e5e7e84a1233`.
Symbol inspection confirms no loader or secondary entry/main. UFS request construction is unchanged; response diagnostics are now added. A temporary host harness extracted the actual MMU
table construction and checked every L2/L3 entry for low, high and block-crossing
image placements for both boards, plus rejection beyond 64 GiB. It also asserts
exactly one Normal-NC L2 block per board and explicitly checks MARBLE
`0xb8000000` as Normal-NC and `0xba000000` as Device. This validates
table construction, not hardware behavior. No CI run, boot, flash, commit or push.

## First physical boot and priority diagnostic correction (2026-10-21)

User-reported physical observation: boot-v4 accepted, framebuffer works, and
shim executes through PSCI, GIC distributor setup and redistributor discovery.
The first GIC failure was a synchronous current-EL Data Abort / synchronous
external abort (SEA): stage `gic config`, ESR `0x96000010`, FAR `0x17190400`,
MPIDR `0x81000000`. FAR is GICR `0x17180000` + SGI `0x10000` + IPRIORITYR
`0x400`, matching the priority read at offset 16. Timer IRQ testing was not
reached; neither timer IRQ nor SGI delivery success is established on MARBLE.

MARBLE now skips all GICR priority reads/writes and prints
`PRIO skip protected GICR priority window`. It still enables virtual timer
INTID 27 and SGI INTID 1, with ICC_PMR_EL1 `0xf0`. MARBLE stages are
`gic group`, `gic enable`, `gic cpuif`, `gic vtimer`, and `gic sgi`.
SWEET priority operations and stage names remain unchanged. Exception handling,
XNU, UFS, framebuffer and MMU code are unchanged.

Both requested raw builds passed without warnings; both existing boot-v4 tests
passed. Preprocessed MARBLE has no GICR priority accesses; SWEET object binary
contents match the source before this correction. Repacked using private clean
`marble-boot-backup-clean/boot_a.img`; inspection and an independent byte-slice
extraction verify the kernel SHA256 equals the current raw Image hash above.
Ramdisk SHA256 remains
`3522298cddcdae5a11741a3e75a425e9ea706418d4aa68a171b794d3c5fb1eb0`.
Output `shim/out/marble/shim-marble-stage0.img`: 3,731,456 bytes, SHA256
`958cc268268f1bba13953adbce1675b8ac5a3c55e321e6e708c9b49d717c03d2`.
Header v4/1584, kernel 180224 bytes at 4096, ramdisk 3544657 bytes at 184320,
zero signature, zero trailing bytes. Prior image preserved privately as
`shim-marble-stage0-before-prio-skip-28bf49fc7d5e.img` in the same directory.
No fastboot/device commands, CI runs, commits or pushes in this correction.
Next: user review and a separately authorized physical test of this image.
