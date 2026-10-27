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
firmware directory and performs the same structural checks.  Supplying
`--marble-gpu-firmware DIR` to `mkadt.py` embeds the blobs and hashes only in
the generated ADT.  Proprietary blobs remain outside git.

After firmware validation, mode 2 reads the already-established GPUCC state.
It deliberately stops at `POWER_CONTROLLER_MISSING` without issuing a write.
Mode 3 currently reaches the same refusal; it does not advertise a ring,
fence, SMMU context, command execution, or userspace service.

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

The next implementation patch must add and independently test the RPMh/AOP/SCM
and clock/GDSC ownership layer with rollback.  Only after logs prove CX and the
GMU register aperture are live may it load CM3, negotiate HFI, and approach the
GPU SMMU context banks.  A command self-test remains blocked on that result and
must not report PASS before a fence and guarded result-buffer mutation agree.
