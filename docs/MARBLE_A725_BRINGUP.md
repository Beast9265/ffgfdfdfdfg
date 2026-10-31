# MARBLE Adreno 725 bring-up boundary

This document records the evidence and the exact safe implementation boundary
for the first post-probe A725 change.  It does not claim GPU command execution.

## Pinned sources

- Physical source baseline: `22f219d4a033ec7e5019e6698278f029c859e6a8`
  (CI run `40502438219`, physically verified eight-core boot).
- Local factory DT: `/home/beast/marble-dump/live.dtb`, SHA-256
  `3488ef1d4291cab4c051514342d93d4746095169b83c3e8c49ea3bdd6bd7088d`;
  decompile: `/home/beast/marble-dump/live.dts`.
- Xiaomi/Qualcomm DT source: LineageOS
  `android_kernel_xiaomi_sm8450-devicetrees` commit
  `2e649a7f3e762903eedad43d8256b91e28b512d8`, notably
  `qcom/cape-gpu.dtsi` and `qcom/marble-sm7475.dtsi`.
- Qualcomm downstream graphics driver: LineageOS
  `android_kernel_qcom_sm8450-modules` commit
  `51cf4da5f05c82122a22413f0fe310023abb80ee`, directory
  `qcom/opensource/graphics-kernel/`.
- Mesa freedreno: `c2d85dae149800530ada5bd8adedeea1cc08eb2d`,
  `src/freedreno/common/freedreno_devices.py`.
- UniXNU `Adreno740`: `5c8c1453c67d6ef6b10ec43ab1f8fc570a2f33e1`.
- Same-device physical evidence: `jebbranch/ios-port-marble` commit
  `7ec000406684414df5f3c1a4c61cfa246bcedd16`, documents
  `gpu-feasibility.md`, `gpu-probe.md`, and `smmu-dead-ends.md`.

## Hardware contract from the factory DT

`/soc/qcom,kgsl-3d0@3d00000` identifies `Adreno725v1`, chip ID
`0x07030002`, compatible `qcom,adreno-gpu-gen7-4-0`.

| Resource | Physical range | Factory DT name |
|---|---:|---|
| GPU core | `0x03d00000 + 0x40000` | `kgsl_3d0_reg_memory` |
| CX DBGC | `0x03d61000 + 0x800` | `cx_dbgc` |
| GPU RSCC | `0x03d50000 + 0x10000` | `rscc` |
| isense | `0x03d8b000 + 0x2000` | `isense_cntl` |
| CX misc | `0x03d9e000 + 0x1000` | `cx_misc` |
| QDSS GFX | `0x10900000 + 0x80000` | `qdss_gfx` |
| RDPM CX | `0x00634000 + 0x1000` | `rdpm_cx` |
| GMU | `0x03d68000 + 0x37000` | `gmu` |
| GMU PDC | `0x0b290000 + 0x10000` | `gmu_pdc` |
| GMU AO block decoder | `0x03d40000 + 0x10000` | `gmu_ao_blk_dec0` |
| GPUCC | `0x03d90000 + 0xa000` | `qcom,cape-gpucc` |
| GPU SMMU global | `0x03da0000 + 0x40000` | `qcom,kgsl-smmu-v2` |

GPU IRQ is SPI 300.  GMU HFI and fault IRQs are SPIs 304 and 305.  The GPU
SMMU users are SID 0 (user), SID 1 (LPAC), SID 2 (secure), and SID 5 (GMU),
all with DT flag `0x400`.  The GPU node references the CX GDSC and the GMU
references both CX and GX GDSCs.  GMU boot also depends on `gmu_clk`, `cxo_clk`,
`axi_clk`, `memnoc_clk`, `ahb_clk`, `hub_clk`, `apb_pclk`, an AOP mailbox,
interconnect bandwidth, PDC/RSCC microcode, and an SCM CX initialization call.

The DT reserves a zap-shader region and names three stock firmware components:
`gmu_gen70000.bin`, `a730_sqe.fw`, and `a730_zap.mdt` (with its associated ELF
segments).  The checked local firmware extraction does not contain these files,
so no hashes are claimed here.

Upstream linux-firmware currently provides two redistributable reference files:
`gmu_gen70000.bin` SHA-256 `b2d3f0e2a98fd6259ab9ffef16df63265542e6cc9a970d53d476e823d432042a`
and `a730_sqe.fw` SHA-256
`4f8b288f340ff5b4881bed8dfea90bb4a1b967556ca2df6d07f4ed4e4a28d071`.
Both pass the structural validator.  They are not asserted to match the
phone's factory build, and linux-firmware does not supply the signed zap MDT
and segments required by this device, so they are not packaged in a test ADT.

Mesa maps `0x07030002` to FD725, A7xx generation 1, four CCUs, A730 magic
registers, and `highest_bank_bit = 16`.  Qualcomm's Gen7.4 table independently
selects 2 MiB GMEM, GMU firmware protocol version 4.0.7, the same three firmware
names, the Gen7.0 HWCG/GBIF/protection tables, and highest bank bit 16.  A740
generated constants are therefore not a valid substitute.

## Implemented milestone

Patch `0100-marble-a725-firmware-preflight.patch` preserves `marblegpu=1` and
adds default-off modes 2 and 3.  Before either mode can perform any GPU MMIO
write, it requires an `/arm-io/a725-firmware` ADT node for chip `0x07030002`,
validates all three blob structures, recomputes SHA-256, and compares it with
the identity embedded by `tools/mkadt.py`.  The GMU parser bounds every
Qualcomm block header and permits only the downstream Gen7 GMU virtual ranges.
SQE must be an aligned nonempty dword stream with a valid version word; zap MDT
must be little-endian ELF32 with bounded program headers.

`tools/marble-a725-firmware.py` recursively inventories an extracted stock
firmware directory and performs the same structural checks.  It also requires
every nonempty ZAP program segment (`a730_zap.bXX`), checks each size against
its ELF program header, and verifies that the MDT is exactly the standard
`b00` metadata plus embedded Qualcomm hash segments.  Supplying
`--marble-gpu-firmware DIR` to `mkadt.py` embeds the three primary blobs, all
three split ZAP segments, and a SHA-256 for each only in the generated ADT.
Proprietary blobs remain outside git.  The current kernel preflight validates
the MDT but does not attempt secure loading or claim that the device
authenticated the transported segments.

After firmware validation, patch 0101 lets modes 2/3 perform a bounded RPMh
ARC transport test, then releases its votes and stops before GPUCC writes.
It does not advertise a ring, fence, SMMU context, command execution, or
userspace service.

Patch 0102 adds an independently gated photographic result screen.  It runs
only with both `marblegpu=2` and `marblegpuvisual=1`, records the actual MX/CX
vote and reverse-order release return codes, and labels each operation
`ACKNOWLEDGED`, `FAILED`, `TIMEOUT`, or `NOT ATTEMPTED`.  The summary uses the
already initialized 2x `sweet-fbcon` console; it creates no framebuffer map and
does not change the framebuffer address, memory attributes, or display setup.
The approximately ten-second delay occurs only after all safe release
operations have completed.  An acknowledgement means only RPMh transport
completion, never GPU power or execution.  All boots lacking both exact
arguments retain their prior timing and behavior.

This is more than the original resource probe: it establishes the firmware
transport and rejects corrupt, wrong-chip, malformed, or partial inputs before
a loader can act.  It is not yet GMU power-up.

## Why power writes are not in this patch

The downstream first-boot sequence is not a GPUCC-only operation.  In order it
requests KGSL AWARE state, sends ACD state to AOP, enables CX GDSC, enables the
GMU clock bulk set, enables AHB timeout detection, initializes the CX timer,
loads GMU firmware and PDC/RSCC microcode, performs secure CX initialization,
configures registers and IRQs, votes minimum DDR bandwidth, starts CM3, starts
HFI, then asks firmware to manage GX.  The current MARBLE port has no validated
owner for this complete RPMh/AOP/SCM/interconnect sequence.  Writing CX/GX
GDSCR or clock branch bits alone would skip required parents and rollback.

Same-device tests also show that SMMU SMR and translation S2CR writes stick,
while BYPASS is forced to FAULT.  More importantly, context-bank register
access has reset the entire phone.  Consequently this patch performs no SMMU
writes and does not access context-bank pages.  Those accesses remain gated
behind a physically demonstrated CX/GMU power state.

## Required next evidence

First obtain the exact stock firmware set from the phone's matching vendor
firmware package and run:

```sh
python3 tools/marble-a725-firmware.py /path/to/extracted/vendor --json
python3 tools/mkadt.py /tmp/marble-a725.adt --marble --marble-cpus 8 \
  --marble-gpu-firmware /directory/containing/the/three/files
```

The next implementation patch must add and independently test the AOP/SCM and
clock/GDSC ownership layer with rollback.  Only after logs prove CX and the
GMU register aperture are live may it load CM3, negotiate HFI, and approach the
GPU SMMU context banks.  A command self-test remains blocked on that result and
must not report PASS before a fence and guarded result-buffer mutation agree.

## RPMh ARC prerequisite stage (0101)

Patch `0101-marble-a725-rpmh-power.patch` supplies the first missing power
controller primitive without pretending to own GPUCC. After the unchanged
mode-2/3 firmware validation, it resolves `mx.lvl` and `cx.lvl` from MARBLE's
captured command DB, validates that both are ARC resources, parses their
zero-padded little-endian VLVL tables, and sends the corresponding highest
valid **HLVL index** through the existing DRV2 ACTIVE-TCS owner. It votes MX
then CX and releases CX then MX. Each transaction requires an unused ACTIVE
TCS, preserves its payload and IRQ mask, waits at most 100 ms for issued and
complete status, and quarantines uncertain state rather than resetting or
retrying it.

The HLVL/VLVL distinction is important. Qualcomm
`drivers/regulator/rpmh-regulator.c` defines ARC request data as the
resource-specific hardware-level index; the command-DB auxiliary table maps
that index to a common voltage level. Qualcomm KGSL
`adreno_rpmh_arc_cmds()` independently treats the auxiliary data as a u16
VLVL table. Mondrian's current experiment sends the maximum VLVL value
directly, so its numeric vote was not copied.

The stage reads `CX_GDSCR` only after acknowledged rail votes, labels its owner
as unclaimed, releases both votes, and stops at `CX_GDSC_OWNER_MISSING`.
It performs no GDSC, GPUCC, GMU, GPU-core, AOP-mailbox, SCM, interconnect, or
SMMU write. Consequently `RPMH_ARC_TRANSACTION_COMPLETE` means only that the
RSC accepted and completed the two votes and releases; it is not GPU-power
PASS. Modes 0 and 1 retain their previous paths.

### SM7475 dependency table

| Dependency | SM7475/Cape authority | Ownership in 0101 |
|---|---|---|
| `mx.lvl`, `cx.lvl`, `gfx.lvl` ARC resources | `waipio-regulators.dtsi`; KGSL `adreno_gen7_rpmh.c` | MX/CX temporary ACTIVE votes only; no GFX vote |
| CX GDSC `0x9108`, HW control `0x953c` | `waipio-clock.dtsi` | Read status only; no claim/write |
| GX GDSC `0x905c`, domain `0x9504` | `waipio-clock.dtsi` | Read only in mode 1; never written |
| GMU bulk clocks | `cape-gpu.dtsi`: CX_GMU, CXO, DDRSS_GPU_AXI, GPU_MEMNOC_GFX, AHB, HUB_CX_INT, APB | Not enabled |
| AOP ACD mailbox | `cape-gpu.dtsi`; KGSL `gen7_gmu_aop_send_acd_state()` | Missing |
| CX secure initialization | KGSL `gen7_scm_gpu_init_cx_regs()` | Missing SCM transport |
| First-boot order | KGSL `gen7_gmu_first_boot()` | Stops before CX GDSC; later steps remain theoretical |

G313's RBBM/CP/performance-counter offsets are standard generated Adreno
register indices and are useful only after clocks and GX are proven. Their
unconditional accelerator-service call is not imported. Jebbranch's physical
result remains the safety boundary: no GPU SMMU context-bank page is accessed.
The next implementation must add a bounded CX GDSC and seven-clock owner with
rollback, plus AOP ACD and SCM dependencies, before any GMU register read or
firmware load.

## Opt-in CX ownership stage (0103)

Patch 0103 resolves the previously missing CX owner without changing modes
0--2.  It is entered only with `marblegpu=3`; the existing screen is additionally
gated by `marblegpuvisual=1`.  The source contract is pinned Cape DT commit
`2e649a7f3e762903eedad43d8256b91e28b512d8`, graphics commit
`51cf4da5f05c82122a22413f0fe310023abb80ee`, and Qualcomm/Xiaomi core-kernel
blob commit `992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0` (`qcom_aoss.c`,
`msm_qmp.c`, `qcom-ipcc.c`, and `gdsc-regulator.c`).

The exact downstream first-boot order is MX/CX parent votes, AOP ACD message,
CX regulator enable, then the seven GMU clocks.  This patch implements only
through a temporary CX transition:

| Resource | Cape address / value | Implemented mode-3 operation |
|---|---:|---|
| AOSS QMP message RAM | `0x0c300000 + 0x400` | Validate `MAIL`/v1 descriptor, negotiate link/channel with 1 s bounds, send `{class: gpu, res: acd, val: 1}`, require mailbox consumption |
| APSS IPCC | `0x0ed18000`, SEND_ID `+0x0c` | Ring Cape's `(AOP=0, GLINK_QMP=0)` doorbell; no interrupt-controller reconfiguration |
| CX GDSCR | GPUCC `+0x9108` | Refuse an already-on/HW-controlled domain; clear HW-control/override, program DT `CLK_DIS_WAIT=8`, clear `SW_COLLAPSE` |
| CX status | GPUCC `+0x953c` | Require `PWR_ON[31]` within two bounded 500 us polls |
| CX retention | GDSCR `RETAIN_FF[11]` | Set only after verified ON, as required by `qcom,retain-regs` |
| Rollback | GDSCR `SW_COLLAPSE[0]` | Reassert once, wait the DT's no-status-check disable interval, make a bounded read-only OFF observation, restore the complete original GDSCR, then release CX and MX |

The AOP acknowledgement proves only that AOP consumed the ACD configuration
message.  CX success requires the independent hardware-control `PWR_ON` bit;
register write/readback alone is not success.  A rollback timeout is reported
even though Cape explicitly marks disable as `qcom,no-status-check-on-disable`.
The original GDSCR and both ARC votes are still restored/released when their
transactions are known to have completed.  An uncertain RPMh timeout is not
retried.  A cold reboot is the recovery for an AOP timeout or any physically
observed hang.

Mode 3 does not map or access a GPU SMMU context bank, does not touch GX, does
not enable a GMU clock, and does not invoke SCM or load/start GMU firmware.
Those remain later milestones.

## GMU clock ownership stage (0104)

Patch 0104 adds only `marblegpu=4`.  Modes 0--3 retain their existing paths.
The clock definitions are from core-kernel commit
`992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0`, specifically
`drivers/clk/qcom/gpucc-waipio.c`, `gcc-waipio.c`, `clk-branch.c`,
`clk-rcg2.c`, and `drivers/soc/qcom/qcom_aoss.c`; the consumer order is Cape
DT commit `2e649a7f...` `cape-gpu.dtsi` and KGSL commit `51cf4da5...`
`adreno_gen7_gmu.c`.

| DT clock name | Controller / CBCR | Downstream operation | Mode-4 ownership |
|---|---:|---|---|
| `gmu_clk` | GPUCC `0x03d90000 + 0x913c` | `BRANCH_HALT`, `clk_branch2_aon_ops`; parent GMU RCG `+0x9318` | Must already be enabled; AON ops have no disable callback |
| `cxo_clk` | GPUCC `+0x9144` | `BRANCH_HALT`, reversible `clk_branch2_ops`; XO RCG `+0x9010` | Enable if off; restore bit 0 in cleanup |
| `axi_clk` | GCC `0x00100000 + 0x81154` | `BRANCH_HALT_SKIP`, `clk_branch2_aon_ops` | Must already be enabled; status polling is explicitly unsupported |
| `memnoc_clk` | GCC `+0x81010` | `BRANCH_HALT_VOTED`, reversible `clk_branch2_ops` | Enable if off; restore bit 0 in cleanup |
| `ahb_clk` | GPUCC `+0x911c` | `BRANCH_HALT_DELAY`, reversible `clk_branch2_ops` | Enable if off; use downstream 10 us settle and restore bit 0 |
| `hub_clk` | GPUCC `+0x9148` | `BRANCH_HALT`, `clk_branch2_aon_ops`; parent HUB RCG `+0x93ec` | Must already be enabled; AON ops have no disable callback |
| `apb_pclk` | AOSS QMP QDSS clock | `{class: clock, res: qdss, val: 1/0}` | Deliberately skipped: KGSL removes it unless `CONFIG_QCOM_KGSL_QDSS_STM` |

The DT contains seven entries, but the matching KGSL driver normally enables
six: `gen7_gmu_clk_probe()` nulls `apb_pclk` when QDSS-STM is not built.  Mode
4 therefore reports it as `SKIPPED (QDSS-STM not enabled)` rather than issuing
an unnecessary AOP vote.

The diagnostic validates the existing source roots instead of guessing an
RCG programming/refcount state.  It accepts only Cape's published GMU table
(19.2/200/500 MHz), HUB table (150/240/300 MHz), and XO 19.2 MHz encodings,
with no pending `CMD_UPDATE`.  AON branches must be inherited ON because their
registered operations intentionally provide no disable function.  If any is
off, mode 4 reports `AON_NOT_INHERITED` before writing it.  Reversible branches
record whether bit 0 was originally owned, use the Qualcomm 200 us branch
bound (or its explicit 10 us delay/skip rule), and restore only bit 0 in exact
reverse order.  Inherited branches are never disabled.

ACD has no per-power-cycle release in the Gen7 downstream sequence.  KGSL
sends a new ACD value only when the configured ACD setting changes and power
cycles the GPU around that change.  Consequently mode 4 retains mode 3's
source-backed `val: 1` request and does not invent a rollback message.

After clock cleanup, mode 4 reuses the physically verified CX rollback and
RPMh reverse release.  The visual screen is gated by `marblegpuvisual=1` and
delays only after all cleanup.  No GMU register, CM3 firmware, GX, GPU core,
SCM, interconnect, or SMMU context-bank access is performed.

## Cape RCG root stage (0105)

The user reports mode 4 completed RPMh/CX sequencing but clock setup was
incomplete and several CBCRs read zero. Zero CBCRs alone do not prove a bad
GPUCC mapping or a stopped delayed AHB clock. The same `0x03d90000` window
provided the physically verified CX GDSCR/HWCTRL transition. Mode 5 measures
root programming directly; a reset/unconfigured root is a hypothesis until
the physical CMD/CFG results are collected.

The mode-5 sequence is derived from the pinned
`gpucc-waipio.c`, `gcc-waipio.c`, `clk-rcg2.c`, and `clk-alpha-pll.c` at
core-kernel commit `992742f9cdcc5ba27e07464a5b2c6a8474ffd1f0`, checked
against Cape DT commit `2e649a7f...`.  The independently supplied
`UniXNU-pong` reference at commit `64ddf288ab6f7fa38eab36a31a599dbaf051534a` confirms the same offsets and
RCG encodings, but its GPU PLL setup, extra future clocks, and deliberate
resource retention are not imported.

| Root | CMD/CFG | Temporary rate | Parent |
|---|---:|---:|---|
| `gmu_clk_src` | GPUCC `+0x9318/+0x931c` | 200 MHz, CFG `0x00100602` | `gpll0_out_main_div` |
| `hub_clk_src` | GPUCC `+0x93ec/+0x93f0` | 150 MHz, CFG `0x00100603` | `gpll0_out_main_div` |
| `xo_clk_src` | GPUCC `+0x9010/+0x9014` | 19.2 MHz, CFG `0x00100001` | `bi_tcxo` |

Mode 5 first requires GCC GPLL0 to be inherited RUN, output-enabled and
locked. Cape changes GPLL0 to the Lucid-OLE layout (OPMODE +0x04, L +0x10,
ALPHA +0x14, USER_CTL +0x18). The diagnostic requires L=31, ALPHA=0x4000
and the post-divider field at USER_CTL[13:10]=1: 600 MHz / 2 from 19.2 MHz
XO. It refuses an unknown inherited rate instead of assuming 300 MHz.  It does not configure or vote the global PLL.  It temporarily
acquires only Cape's `gcc_gpu_gpll0_div_clk_src` vote at GCC `+0x62000` bit
16.  Each RCG follows downstream `clk-rcg2.c`: reject a pending update, inherited force owner or unowned source, save
CMD/CFG, set `CMD_ROOT_EN`, poll `CMD_ROOT_OFF` clear for at most 500 us,
replace only SRC/DIV/MODE/HW fields, assert `CMD_UPDATE`, and poll its
self-clear for at most 500 us.  Cleanup restores the same fields with another
bounded update, restores the original ROOT_EN bit in reverse order, then
restores the parent vote before CX/RPMh rollback.

An update timeout is an uncertain hardware completion, not a normal failure.
Mode 5 issues no second RCG transaction, parent removal, CX collapse, or RPMh
release after that condition; it reports `RESOURCE RETAINED` and requires a
cold reboot.  This avoids cutting power beneath a transaction that may finish
late.  Mode 5 does not configure GPU PLL0/PLL1, write `+0x9534`, enable any
branch clock, or access GMU/GX/GPU/SMMU registers.  In particular it does not
clear an AON branch: matching downstream AON operations still provide no
disable callback.


### Recovery audit and physical test boundary (2026-10-31)

Interrupted work was preserved in `/tmp/a725-work-preserved/`; no worktree
reset was used. The exact 0104 source/headers and compiler commands were
recovered from CI 40872190871. Full-tree reverse/replay of 0001–0105 passed;
0105 strictly applies to the exact CI probe and byte-matches the compiled
source. The MARBLE TU compiles to arm64 Mach-O. The SWEET configuration
excludes the entire TU; no SWEET implementation or CPU/touch/storage/display
source changes are introduced. Firmware, ADT, boot-v4, topology and synthetic
RPMh checks pass. `tools/test-marble-a725-roots.py REPLAYED_XNU` runs actual
root C with an MMIO allowlist and tests inherited-vote restoration, unrelated
bit preservation, PLL rate/lock failures, ignored writes, ownership refusal,
and every forward/cleanup update timeout. Host results cannot prove clocks.

Mode 5 is deliberately the next independently testable prerequisite: it does
not enable branches or start CM3. A PASS needs all three root transitions,
root cleanup, CX rollback and both vote releases, followed by normal
SpringBoard/touch/UFS operation. An inherited owner or pending update also
retains resources. On uncertain completion do not repeat the experiment in
that power session; cold reboot before returning to the tested fallback.
The fixed-delay AHB readback issue belongs to the subsequent branch stage;
mode 4 is unchanged and its strict bit0 check is not proof of clock failure.

The source audit is pinned for the next agent, avoiding repeated discovery:

- [Mondrian GPU notes](https://github.com/xNekom/ios-mondrian/blob/7fad03b8e7b3f7831a4a8d178008360a4cf5c2ea/docs/MONDIAN_GPU.md)
  and patches 0164/0166/0168/0169/0171/0172/0182: hold root force until
  branches run; delayed AHB may read zero. Submission cache maintenance must
  cover **every submitted BO/page**, including VBO/constant/draw-state data,
  not only the top-level IB. Preserve this requirement in the future ABI.
- [Pong clock implementation](https://github.com/Chengdong-Yu/UniXNU-pong/blob/64ddf288ab6f7fa38eab36a31a599dbaf051534a/drivers/PongAdreno/PongAdrenoClocks.c):
  confirms encodings, force/update and branch delay; its irreversible AON
  acquisition, PLL configuration and retention policy are not imported.
  This patch is authored locally from hardware facts, not a driver transplant.
- Jebbranch `c03d18a34c9103e3ad1be27bc7a15038d607d69d`, actual
  `0215-sweet-gpu-probe-v9.patch` and GPU notes through October 31: the
  `fcae6a91...` correction confirms SLEEP=0/WAKE=1/ACTIVE=2. CM3 execution
  experiments affected subsequent XNU startup; no CM3/WAKE experiment copied.
- Lietxia `6f88f7e95c96b9344d41c6c8b2073e7197ab5071`: reported GPU SMMU
  ID1=0x40000016 decodes CB0=+0x20000, within the factory +0x40000 window.
  Our phone's ID1 must still be read/verified before context programming.
- Mondrian `docs/COREANIMATION_GLES.md` at the pin above explicitly says its
  backboardd hooks create a context but **the UI is still CPU-rendered**;
  IOSurface request 0x7e and Mesa no-copy hooks are missing there. Do not
  treat context creation as accelerated SpringBoard. Apollo
  `467b48084c2939c36c093f017634c0e468f3a657` and Sailfish
  `6f27e41ff249f2680540ebe8ee5ab982c5e641c9` EAGL/libdrm sources were
  retrieved for the later bridge; offsets must be verified against local
  20H392 binaries before use. No rootfs library installation was attempted.
