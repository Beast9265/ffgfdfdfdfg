# MARBLE SE4 GPI touch transport v6

Starting HEAD: `e545d4198f5a3baef4c2e5162889cf5e47be1845` (v5 HWCG fix).
That source passed CI39961658578. The user redirected work to GPI before a
v5 image was packaged. V6 includes that clock fix. Physical v4 observation
remains no touch at S_AHB `0x80000002`; the overlay is physically confirmed
readable and stable. No newer physical success is claimed. No local physical
hwdiag file was found at the requested paths. No phone commands were executed.

## Provenance

| Pinned source | Function / definition | V6 consequence |
|---|---|---|
| MARBLE live OEM DTS, read-only local dump | spi@990000, gpi-dma@900000, apps-smmu phandle5d | Board resource, static GPII, SID and IOVA constraints below |
| [Pzqqt cf63f539](https://github.com/Pzqqt/android_kernel_xiaomi_marble/tree/cf63f53980e17b503e595501b359697595fe8b24) | drivers/dma/qcom/gpi.c: gpi_of_dma_xlate, gpi_find_static_gpii | Argument4 is a bitfield: static slot1 selects GPII0, priority0; corrects the earlier v4 dynamic/priority2 interpretation |
| Same vendor commit | msm_gpi_mmio.h; gpi_probe | EE base is resource minus10000; only GPII0 context/command/doorbell writes |
| Same vendor commit | gpi_alloc_ring, gpi_alloc_ev_chan, gpi_alloc_chan, gpi_start_chan | Aligned64-TRE TX/RX rings,256-event ring; allocate before context writes, event doorbell, both channel allocations, both starts |
| Same vendor commit | gpi_send_cmd, gpi_handle_irq, gpi_process_events, gpi_ring_* | Raw control completion plus state checks; event producer/pointer validation; one empty ring slot; wrap and recycling semantics |
| Same vendor commit | include/linux/msm_gpi.h | Exact DMA-buffer, CONFIG0 and GO dwords; channel scratch pairing/SPI/SE4 |
| Same vendor commit | spi-msm-geni.c: select_xfer_mode, setup_config0_tre, setup_go_tre, setup_dma_tre, setup_gsi_xfer | FIFO-disabled selects GSI; TX CONFIG0/GO/DMA plus paired RX DMA; no lock/unlock or fragmentation; source-proven internal SPI_LOOP bit |
| Same vendor commit | platform/msm/msm-geni-se.c: geni_se_select_gsi_mode; include/linux/msm-geni-se.h | DMA mode plus GSI events, local IRQ route disabled; no SE-local DMA pointers |
| [Linux734bef548](https://github.com/torvalds/linux/tree/734bef548a96e8774d6eef5dfa2026c6edc4e80b) and [iLtanaka ed120558](https://github.com/iLtanaka/linux-marble/tree/ed120558cd2c5f970edc44e1273a8d7b6caed825) | arm-smmu.c/h: context bank program order, SMR/S2CR, TLBI/ATS; io-pgtable-arm.c | Architected SMMUv2 stage1,4KiB tables independent of CPU16KiB pages, fault/readback/TLB handling |
| [UniXNU ArmSmmu4K4d0d6598](https://github.com/UniXNU/ArmSmmu4K/tree/4d0d6598b1a36aeec3de01091893fa6660e49388) | Context, Program, Streams, table builder | Cross-check of AArch64 context image, private table leases, readback, publication ordering; no SM8550 addresses copied |
| [NativeGeniSpi b5399b56](https://github.com/UniXNU/NativeGeniSpi/tree/b5399b5646c4d7415deec6d887fd51715a97a024) | GeniSpi.c | Cache/transport architecture comparison; its SE-local DMA is not used |
| Pzqqt cf63f539 and historical f552724a/fa376fbb/d4a2fc8b | goodix_9916r SPI/hardware/core sources | Existing Berlin-D framing, rail/reset order, confirm, version checksum and event format retained; version checksum retries follow brl_read_version |
| [iLtanaka firmware eb8f66da](https://github.com/iLtanaka/firmware-xiaomi-marble/tree/eb8f66daf42b856e5e1845848e2b42ea4eea2cdb) | Firmware inventory reference | No firmware/config updater or upload added |

The live dump is not committed. Prior v3/v4 documents retain the historical
Goodix adaptation/voltage and board-DT lineage. The static GPII interpretation
in this document supersedes their earlier incorrect priority/dynamic claim.

## Topology and ownership

DMA tuples `<0 4 1 0x40 2>` and `<1 4 1 0x40 2>` mean TX0/RX1,
SE4/SPI,64 TREs, static GPII0, priority0. Resource900000/60000 with EE offset
10000 gives conceptual EE base8f0000:

| GPII0 register | Physical address |
|---|---:|
| CH0 / CH1 context | 910000 / 910080 |
| Event0 context | 911000 |
| CH0 / CH1 doorbell | 912000 / 912008 |
| Event doorbell | 912100 |
| Channel / event command | 913008 / 913010 |

GPII0 SPI interrupt244 means GIC INTID276. V6 uses bounded polling and leaves
the external GPII0 type IRQ mask zero; it polls the same raw control and IEOB
sources as the vendor IRQ handler. No GIC subsystem change is required.

Only GPII0 is programmed. Before retargeting the shared GPI SID, the other
DT-enabled APSS instances1..6 are checked **read-only** for an unallocated
state. No other instance is selected, reset, started, or written. Busy,
unreadable, or mismatched SE/protocol state refuses initialization. Matching
inactive GPII0 allocations may be reset/deallocated using bounded vendor
commands; inherited rings are never submitted or reused.

## SMMU and memory

Apps SMMU is qcom,qsmmu-v500 at15000000/100000. GPI uses SID5b6/mask0;
QUP wrapper SID5a3 is untouched. CPU allocations are16KiB pages; the SMMU
granule is independently4KiB, required by ID2 capability. ID1 determines
register-page spacing and context-bank base; live DT overrides bound available
NS banks/SMRs to78/120.

V6 scans actual SMR/S2CR state, rejects duplicates/wildcards, records the old
context, and claims only an unreferenced disabled bank with empty roots.
ASID selection excludes inherited TTBR and AArch32 CONTEXTIDR ASIDs. It never
overwrites inherited page tables or resets a global SMMU. The exact SID route
is faulted while the private bank is prepared. A previously invalid stream
slot is published only with the exact new SID, including correct EXID order.

One permanent96KiB contiguous allocation is physically verified at each CPU
page. Its first16KiB holds three4KiB table pages and an unused guard. Only one
4KiB subpage of each remaining dedicated16KiB page is exposed:

| IOVA | Allocation PA offset | Purpose / ring bytes |
|---|---:|---|
| 100000 | 4000 | TX ring /1024 |
| 101000 | 8000 | RX ring /1024 |
| 102000 | c000 | Event ring /4096 |
| 103000 | 10000 | TX payload /max1032 |
| 104000 | 14000 | RX payload /max1032 |

All other IOVAs, including the rest of the live1MiB pool, remain unmapped.
Page tables are not exposed to GPI. Leaves are RW/unprivileged, normal WB,
inner-shareable, AF/nG, PXN/UXN; table walks are coherent WBWA. SCTLR fault
reporting is polled. Writes/readbacks, page-table readback, context-local
TLBI+TLBSYNC and barriers precede stream publication. Where ID0 supports ATS,
all five mappings and an unmapped guard are checked by hardware translation.
No global CR0/TLBI, global bypass or identity mapping is added. Memory/table
leases remain pinned after any failure; initialization cannot be retried into
unknown ownership.

## SPI and Goodix

CONFIG0 follows the vendor mode0,CS0,8-bit/MSB,TX/RX-pack settings. It uses the
already verified GENI source level and divider2 (XO19.2MHz ->9.6MHz, below the
panel15MHz limit). TX ring receives CONFIG0,GO,TX DMA; reads additionally
submit RX DMA. The GO link_rx bit pairs them. No CS fragmentation or explicit
lock/unlock is added. A one-time16-byte internal loopback uses the vendor's
GSI_LOOPBACK_EN flag; the next CONFIG0 restores normal mode.

Goodix reads remain `F1 BE32 FF FF FF`, RX offset8, one transfer/CS interval;
writes remain `F0 BE32 payload`. Confirm remains write/read8xAA at10000,
three attempts. Power remains reset-low,IOVDD1.8V/30ms,AVDD3.224V/15ms,
reset-high/100ms. Version10014 keeps checksum semantics and gets the vendor's
bounded retries; uncertain DMA is never retried. IC-info10070, frame parser,
IRQ21 polling, coordinates, ACK policy and marble_hid_touch ABI are unchanged.
No exact firmware VID is required. No firmware/config flashing or upload.

## Diagnostics and validation

Existing IDs are unchanged; appended stages22..30 identify SMMU,memory,event
ring,TX,RX,start,config,transfer,event. Appended reasons40..52 identify GPI
ownership/capability/readback/fault/TLBI/command/context/ring/event/timeout/
loopback failure. The existing512-record and64KiB file bounds remain. A tail
reservation preserves a terminal register/TRE/event snapshot even after the
history fills. Successful confirm/version/IC-info are checkpointed before IRQ
polling. Overlay and file format remain version4; record
`TOUCH_TRANSPORT_BUILD/IRQ = 6 /276` identifies this transport build.

New host tests execute actual source state machines with MMIO/cache/DMA
boundaries modeled: exact Qualcomm TRE vectors; eight EE address assertions;
static tuple decode; ring capacity/wrap; dedicated page tables/unmapped guard;
translated SID/free-bank/ASID leases; wildcard/duplicate/busy refusal; EXID
publication; noncontiguous allocation; register/ATS/TLBI faults; command and
transfer timeouts; internal loopback; full-duplex/TX-only transfers through
1032bytes;200 transfers exercising ring wrap;
malformed events and strict GPII0-only writes. Actual Goodix functions prove
Berlin-D offset8 and exact confirm bytes. Existing parser/FIFO/power/clock
tests and diagnostic bounds tests remain enabled. Physical success awaits
the user's boot.

No root image rebuild. Final artifact results follow below.

Local release validation passed: full82-patch replay, strict0082 and all89
generated files equal the tested work tree; actual CI-header compilation of
marble_touch.c, marble_gpi.c, marble_gpi_smmu.c and marble_hwdiag.c produces
arm64 Mach-O objects. Complete modified-object symbol closure passes against
the linked v4 kernel plus new definitions. Sixteen preprocessing comparisons
for SWEET/VMAPPLE/BCM2837/T8103 pass; all generated frozen-component sources
are byte-identical to v4. ASan/UBSan actual-source tests above, retained
Goodix/FIFO/power/clock and diagnostic-bound tests, and10Python unit tests pass.

## Exact CI and preserved package

Implementation source `c1ae515efec3c59f34cf8ed056739bb0a3adce23` passed
[CI39988871978](https://github.com/Beast9265/ios-marble/actions/runs/39988871978).
Verified xnu.yml /marble/workflow_dispatch, exactheadSha, success. All89 CI
generated source sections byte-match the tested replay. Four new/modified
units compiled in CI; full linked arm64 Mach-O has zero undefined symbols.
New transport, SMMU init/table/TLBI and diagnostic bodies are present in the
linked kernel. The documentation follow-up also adds an explicit maximum1032
byte transfer case to the host test; it changes no kernel source.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| kernel.development.marble | 17861560 | `89e1c087e9fb16d1458e5c141f62f9ac36e247a5e4dfc5c058e8fb5238e60066` |
| Exact Hello ADT | 6920 | `35f0bff762c339e86a0e67392267ed148ae06b24703b682ce2327c9296ed84e3` |
| marble-xnu-touch-gpi-v6.payload | 17246912 | `fbc02940ca5f268dc66f30e9cc9263a7cb84a54b5437eb2abb66a389cbe40b64` |
| latest-marble-xnu-touch-gpi-v6.img | 17334272 | `893ee666a4b94f3f594f31ebafd7f9278a05b6d6a056dedf10b5c5409c67e70b` |

Kernel artifact directory: `xnu/out-marble-ci-39988871978`.
Final image: `shim/out/marble-xnu/latest-marble-xnu-touch-gpi-v6.img`.
Local manifest: `shim/out/marble-xnu/marble-touch-gpi-v6-39988871978.json`.
All payload segments/fixups, exact ADT embedding, stock boot-v4 metadata,
padding/footer/bounds, bootstrap code/stacks/tables/aliases/capacity and CPU0
timer audit pass. Exact known-good shim bytes reused (SHA256
`586713d3b4c5862f73443cb1e5f555e465a9ffa5f3e2662672d41fff1715ee05`).

Payload command line:

```text
debug=0xc serial=3 cpus=1 keepsyms=1 -enable_kprintf_spam rd=ufsroot0 unentitled_ios_sim_launch=1 ignition_level=1 ufsrw=1 rootrw=1 launchd_unsecure_cache=1 marbleguidiag=1 marbletouchinit=1 marblehwdiag=1 marbleusb=0 marbleusblog=0
```

All eight prior boot images rehashed unchanged. Primary rollback remains
`hello-known-good-marble-xnu.img`, SHA256
`789377d9cc9de5027038b074e3c0c61121f2229594e7895282933a44b1eb6242`.
V3 remains `bb9d52f1e14bfe438dfc4491fa2af53599f68b8bb8d233355bba867990003a31`;
v4 remains `4a3096469c3099c0053ef3f4dbc08dc43d4e7fe25b9e87ce85c831c067890c34`.
No phone operation, root rebuild, userdata change or retention cleanup.

## Physical handoff

Expected progression is clock/HWCG validation, GENI identity, power/reset,
GPI SMMU/memory/event-ring/TX/RX/start, `GPI_LOOPBACK_OK`, confirm8xAA,
version/IC-info, then physical IRQ/event delivery through the existing HID path.
Physical success remains unverified. A capability/ownership or hardware
completion failure stops safely with a specific stage/reason/gate.

If blocked, return the full `/private/var/tmp/marble-hwdiag.txt`, especially
failed_at/reason/errno/gate, GPI0 context0..7, scratch/IRQ/error state,
SID SMR/S2CR and contextbank/SCTLR/TTBR/TCR/MAIR/FSR/FAR, last TREs/event/bytes,
loopback and Goodix confirm/version/IC-info records. Automatic file snapshots
start90s after worker startup and repeat at120/180/300s. The already stable
overlay remains unchanged: both volume keys2s toggle, release,up/downpages,
both2s returnsGUI. No physical boot command is supplied in this handoff.
