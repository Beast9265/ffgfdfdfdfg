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
