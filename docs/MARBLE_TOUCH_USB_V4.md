# MARBLE touch/USB v4

Software validation is separate from physical success. No phone commands were
executed. Starting HEAD: `5448620036ce4a7e8ca4a2bc6489fea6c0de872d`.
V3 source: `d5adb94de8e1a02442e844bcd5a5ebe7af890000`, CI39946450245.

## Physical v3 result (user observation)

Hello and physical keys work; no physical touch and no Linux USB attach.
`/private/var/tmp/marble-hwdiag.txt` was written successfully:
`MARBLE HWDIAG v3 file_error=0 writes=4`.
Touch: stage17, failed_at2, reason14, errno-1, gate
`GCC SE4/AHB branch timeout`. GCC62008 changed400283c0 to4002c3c0.
GPIO16..21 initially cfg1/io0. Goodix was **never contacted**.
USB: stage20, failed_at10, reason14, errno-1, gate
`USB probe refused (see register snapshot)`. Hardware preparation completed,
including BCR, rails, GPIO7, reference clock, 28 PHY steps and QSCRATCH.
The post-QSCRATCH gate was ambiguous; v3 cannot identify its actual cause.

## Source ledger

All facts below were inspected before editing; public references are pinned.
The live dump `/tmp/marble-live.dts` is read-only and excluded from git.

| Source / revision | File / function | Evidence and consequence |
|---|---|---|
| Live OEM DTS; user Linux observations | spi@990000, gpi-dma@900000, apps-smmu@15000000, ssusb@a600000 | Board evidence described below; runtime SMMU state remains unknown |
| [Linux 734bef548a96e8774d6eef5dfa2026c6edc4e80b](https://github.com/torvalds/linux/tree/734bef548a96e8774d6eef5dfa2026c6edc4e80b) | drivers/clk/qcom/gcc-sm8450.c; clk-rcg2.c; sm8450.dtsi; qcom,gcc-sm8450.h | S4 parent RCG, branch vote/halt registers, IDs and DFS layout |
| [Pzqqt cf63f53980e17b503e595501b359697595fe8b24](https://github.com/Pzqqt/android_kernel_xiaomi_marble/tree/cf63f53980e17b503e595501b359697595fe8b24) | drivers/clk/qcom/gcc-waipio.c; clk-rcg2.c | Safe parent enable, ROOT_EN/UPDATE/ROOT_OFF, HW_CLK_CTRL; source then branches |
| Same Pzqqt revision | drivers/platform/msm/msm-geni-se.c: se_geni_clks_on; drivers/spi/spi-msm-geni.c | M_AHB then S_AHB then SE clock; protocol configuration follows resource enable |
| Same Pzqqt revision | drivers/dma/qcom/gpi.c: gpi_of_dma_xlate, gpi_find_dynamic_gpii, gpi_alloc_ring; msm_gpi_mmio.h; include/linux/msm_gpi.h | Five-cell ABI; dynamic GPII allocation; coherent aligned rings, channel/event contexts, scratch protocol association; EE offset subtraction |
| [Vendor five-cell binding blob bb4a7ca3ae3106788e09975a8f809ec9f6c67312](https://android.googlesource.com/kernel/msm-extra/devicetree/+/refs/heads/android-msm-redfin-4.19-android11-qpr1/bindings/dma/qcom_gpi.txt) | qcom_gpi.txt | channel, SE, protocol, TRE count, priority; corroborated by actual vendor driver |
| Same Pzqqt revision | drivers/usb/dwc3/core.c: dwc3_core_is_valid; core.h; dwc3-msm-core.c; dwc3-msm-ops.c | OEM glue and recognized Synopsys families; vendor glue differs from mainline device model |
| Linux revision above | drivers/usb/dwc3/core.c; core.h | GSNPSID5533,3331,3332; latter two read VER_NUMBER/VER_TYPE; GCTL role and PHY fields |
| [iLtanaka Linux ed120558cd2c5f970edc44e1273a8d7b6caed825](https://github.com/iLtanaka/linux-marble/tree/ed120558cd2c5f970edc44e1273a8d7b6caed825) | marble DTS, GCC, PHY and USB sources | Working-board reference; v3 hardware sequence retained |
| [iLtanaka firmware eb8f66daf42b856e5e1845848e2b42ea4eea2cdb](https://github.com/iLtanaka/firmware-xiaomi-marble/tree/eb8f66daf42b856e5e1845848e2b42ea4eea2cdb) | repository firmware inventory | No controller firmware upload added; clock failure precedes Goodix contact |
| [cupid DT ea5040868ed32ff5a9344d47f26490002a846092](https://github.com/cupid-development/android_kernel_xiaomi_sm8450-devicetrees/commit/ea5040868ed32ff5a9344d47f26490002a846092) | marble device-tree changes | Supporting board lineage; live OEM dump takes priority |
| Pzqqt and Linux revisions above | SNPS eUSB2 PHY source, blob af4fa17ac6cbcbac0cbf1e89372d7dd21c931ba3 | Already ported in v3; no PHY/repeater sequence changes in v4 |

V3 research document retains Goodix adaptation/regulator ancestry and U-Boot
research. No Goodix protocol, firmware/config, event parser or HID change is
justified by the physical v3 clock failure.

## Exact live OEM topology

GCC phandle24 is clock-controller@100000, compatible qcom,cape-gcc/syscon,
size1f4200. SE4 clock IDs94/134/135 map to S4/M_AHB/S_AHB:

| Resource | Vote GCC62008 | Halt register | Parent |
|---|---:|---:|---|
| S4 | bit14 | 274dc | RCG274e4, CFG274e8, DFS274f8 |
| M_AHB | bit6 | 27004 | inherited GCC wrapper parent |
| S_AHB | bit7 | 27008 | inherited GCC wrapper parent |

There is no power-domains property on the live SPI node. No new CX vote added.
The provider has supply dependencies; absence of a node property alone does
not prove all provider power dependencies irrelevant.

V4 snapshots all seven registers independently before/after. Non-DFS prepares
XO/div1/integer/HW_CLK_CTRL, bounds UPDATE and ROOT_OFF waits, then enables and
polls M_AHB, S_AHB, S4 separately. Temporary ROOT_EN is released after branch
handoff if v4 acquired it. DFS tables are not rewritten: select a validated XO
level and set GENI selection only after branches run. Each timeout has its own
reason and exact gate. No gated GENI reads precede successful clock validation.
This fixes a source-backed ordering error; physical effectiveness is untested.

GPI phandlec8: qcom,gpi-dma@900000, size60000, #dma-cells5;
12 GPIIs, interrupts GIC SPI244..255/level-high4; static mask1, dynamic mask7e,
event factor2, EE offset10000, coherent DMA, statusok.
TX `<0 4 1 0x40 2>` = TX/SE4/SPI/64 TREs/priority2.
RX `<1 4 1 0x40 2>` = RX/SE4/SPI/64 TREs/priority2.
SE4 is not a raw GPII index. Vendor allocation selects an available dynamic
instance1..6. `qcom,smmu-cfg` and `qcom,iova-range` are absent.
The GPI IOVA pool is100000/100000: [1MiB,2MiB).

Vendor EE base is mapped base **minus**10000. Channel context0 offset20000 +
4000*GPII +80*channel; doorbell22000, commands23008, event context21000,
channel scratch20060. Context encodes protocol/direction/EE/event association,
ring length/base/read/write pointers. Commands allocate/start/stop/reset/free;
TRE/event layout and coherent aligned allocation are defined in the pinned
vendor headers/driver. Linux software ownership and its IOVA allocations cannot
be reused by XNU. No safely owned context/domain has been established.
V4 therefore never writes GPI contexts, rings or doorbells. On FIFO refusal it
captures dynamic GPII TX/RX context0/length/base/scratch, event context0 and
matching SID5b6 SMR/S2CR state read-only, bounded inside the mapped range.
FIFO is not forced on. Existing idle/FIFO/DMA refusal policy remains.

IOMMU phandle5d is qcom,qsmmu-v500 apps-smmu@15000000, size100000,
second region151ce000/20, #iommu-cells2; skip-init, three-level tables,
context-bank override4e, SMR override78, handoff SMRs2800/402, coherent.
GPI uses SID5b6/mask0; DWC uses SID0/mask0. USB pool90000000/60000000 is
[90000000,f0000000), atomic DMA. These declarations do not establish inherited
runtime bypass. V4 retains read-only SID0 bypass validation; translated,
faulting, ambiguous or unreadable state refuses DMA. No SMMU writes.

OEM SPI binds gtx8_spi to goodix,gt9916S with GPIO21 edge IRQs observed in
thousands under working Linux. OEM USB binds msm-dwc3 and dwc3, both active.
USB clock IDs169/20/12/171/174 map respectively to master49018,
cfg-NoC49084, aggregate49088, mock-UTMI49024, sleep49020.
Reset ID26 is core BCR49000. These agree with the physically completed v3 path.

## USB changes and preserved behavior

V4 retains byte-identical marble_usb_hw.c and marble_touch_power.c: GDSC,
source/branches/BCR, GPIO7, ldob5/880mV, ldoc10/1200mV, smpb10/1800mV,
ldob2/3080mV, repeater reset, eUSB gate9c00c, 28-step PHY initialization and
QSCRATCH. The separate USB3 reference9c010 is recorded, not required for HS.

After QSCRATCH, all eight post-clock registers are saved before validation.
Every required clock and GDSC gets a unique failure; eUSB gate checks enable
bit0. DWC mapping is increased fromd000 to10000 for the OEM child ranged93c.
Map result/size and all requested core/event registers are persisted before
writes. Recognized DWC3/31/32 families retain strict identity validation; newer
families save and validate version registers. Unsupported DWC4 remains refused.
The v3 5533-only check was narrower than both vendor and upstream validation;
this is a candidate failure, **not a physically proven cause**.
GCTL device-role and GUSB2PHYCFG writes have distinct masked readback failures.
Allocation/address-width/physical lookup/reset/EP0/RUN/event errors have exact
reasons. Generic failure overwrites are removed; RAM preserves first failure.
Gadget descriptors, networking and host setup are unchanged.

## Diagnostics and overlay

RAM512-record and <=64KiB file bounds retained. VFS path remains
`/private/var/tmp/marble-hwdiag.txt`, normal vnode writes, no-follow/regular-file
checks, finite attempts, fsync/close; file failure never gates boot.
Header version4; existing enum values preserved, new stages/reasons appended.

The overlay uses exactly the console's `glyph[gy] & (1u << gx)` convention.
Only vsync renders; present only suppresses GUI copies while active. A bounded
70x65 character cache draws changed cells only. Full background fill happens
once on entry; unchanged revision/page does no pixel writes. Normal inactive
presentation and physical/logical geometry remain unchanged.
Both volume keys held2s toggles; release, up/down navigate; both2s returns GUI.
No physical key driver changes. File remains primary evidence.

## Validation and artifacts

Local checks passed: all82 patches replayed, strict0082, all86 generated
files equal tested tree; four modified units compile using actual CI headers
to arm64 Mach-O; undefined symbol closure checked against the linked v3 kernel
plus new object definitions. Twenty shared-source preprocessing comparisons
pass for SWEET/VMAPPLE/BCM2837/T8103. Original Goodix/FIFO/power/USB tests,
100000-case touch and EP0 fuzzing, V3 extracted PHY/SPMI/diagnostic tests and
focused V4 clock/core fault injection pass under ASan/UBSan. Overlay bounds,
font orientation, unchanged-frame no-write behavior and first-failure retention
pass. Ten Python unit tests pass. Physical v4 test remains user-only.

Unresolved safety gates: FIFO-disabled GPI needs owned rings/channel/domain;
translated USB SID0 needs an owned mapping. V4 reports these and never forces
bypass. No claim of touch contact, USB attach or enumeration before testing.
